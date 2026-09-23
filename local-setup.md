# Local Setup

Install these tools, then run the checks. Figure out any errors yourself first. If you're still stuck, comment on the Setup checklist issue.

## Tools

| Tool | Mac | Windows (admin PowerShell) |
|---|---|---|
| Package manager | [Homebrew](https://brew.sh) | winget (built in) |
| Git | `brew install git` | `winget install --id Git.Git` |
| Docker Desktop | `brew install --cask docker` | `winget install --id Docker.DockerDesktop` |
| kubectl | `brew install kubectl` | `winget install --id Kubernetes.kubectl` |
| Minikube | `brew install minikube` | `winget install --id Kubernetes.minikube` |
| Helm | `brew install helm` | `winget install --id Helm.Helm` |

Open Docker Desktop before continuing. Restart your terminal after installing.

## Check

```
git --version
docker --version
kubectl version --client
minikube version
helm version

minikube start
kubectl get nodes      # should show: minikube   Ready
```

## Get the repo

```
git clone <repo URL>
```

## Docs

- [Minikube](https://minikube.sigs.k8s.io/docs/)
- [kubectl](https://kubernetes.io/docs/reference/kubectl/)
- [Helm](https://helm.sh/docs/)
