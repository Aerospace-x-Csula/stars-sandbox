#!/usr/bin/env bash
set -euo pipefail

if (( EUID == 0 )); then
    echo 'Run this as your regular Ubuntu user. The script uses sudo for system setup.' >&2
    exit 1
fi

source /etc/os-release
if [[ ${ID:-} != ubuntu ]]; then
    echo 'Run this on Ubuntu.' >&2
    exit 1
fi

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
values_file="$repo_root/observability/values.local.yaml"
if [[ ! -d "$repo_root/observability" ]]; then
    echo 'Keep this script in the infrastructure folder of the STARS repo.' >&2
    exit 1
fi

installer_dir=$(mktemp -d)
trap 'rm -rf -- "$installer_dir"' EXIT

echo 'Installing Ubuntu packages...'
packages=(ca-certificates curl git)
if ! command -v dockerd >/dev/null; then
    packages+=(docker.io)
fi
sudo apt-get update
sudo apt-get install -y "${packages[@]}"
sudo systemctl enable --now docker

if ! command -v helm >/dev/null; then
    echo 'Installing Helm...'
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4 \
        -o "$installer_dir/install-helm.sh"
    sudo bash "$installer_dir/install-helm.sh"
fi

if command -v k3s >/dev/null; then
    sudo systemctl start k3s
else
    echo 'Installing K3s and kubectl...'
    curl -fsSL https://get.k3s.io -o "$installer_dir/install-k3s.sh"
    sudo sh "$installer_dir/install-k3s.sh" server --docker --disable traefik
fi

# keep the local cluster config separate
mkdir -p -m 700 "$HOME/.kube"
export KUBECONFIG="$HOME/.kube/stars-local.yaml"
sudo install -m 600 -o "$(id -u)" -g "$(id -g)" \
    /etc/rancher/k3s/k3s.yaml "$KUBECONFIG"

k3s kubectl wait --for=create nodes --all --timeout=180s
k3s kubectl wait --for=condition=Ready nodes --all --timeout=180s
runtime=$(k3s kubectl get nodes -o jsonpath='{.items[0].status.nodeInfo.containerRuntimeVersion}')
if [[ $runtime != docker://* ]]; then
    echo "This K3s cluster uses $runtime. Run this setup in a fresh Ubuntu environment to use Docker." >&2
    exit 1
fi

if [[ ! -e "$values_file" ]]; then
    echo 'Use at least one uppercase letter, one number, and one punctuation character in the OpenObserve password.'
    echo 'Avoid double quotes and backslashes in the email and password; the chart does not escape them.'
    read -r -p 'OpenObserve root email: ' email
    read -r -s -p 'OpenObserve root password: ' password
    printf '\n'
    (
        umask 077
        printf "auth:\n  ZO_ROOT_USER_EMAIL: '%s'\n  ZO_ROOT_USER_PASSWORD: '%s'\n" \
            "${email//\'/\'\'}" "${password//\'/\'\'}" > "$values_file"
    )
    unset password
else
    echo 'Using existing observability/values.local.yaml.'
fi

helm repo add openobserve https://charts.openobserve.ai --force-update
helm repo update openobserve
helm upgrade --install openobserve openobserve/openobserve-standalone \
    --namespace stars --create-namespace --values "$values_file" --wait --timeout 10m
k3s kubectl get pods,services --namespace stars

cat <<'EOF'
OpenObserve is ready. Run this command and leave its terminal open:
kubectl --kubeconfig "$HOME/.kube/stars-local.yaml" -n stars port-forward svc/openobserve-openobserve-standalone 5080:5080
Then open http://localhost:5080 in Ubuntu and sign in with your OpenObserve credentials.
EOF
