# Fresh OpenObserve Enterprise Installation (Minikube)

**THE OTHER GUIDE IS RECOMMENDED TO TRY FIRST SINCE IT IS EASIER**

This guide installs a fresh **OpenObserve Enterprise ALONGSIDE an existing Community/Standalone instance**. It assumes Minikube, Helm, OpenTelemetry collectors (`o2c` Helm release), and the log/error generators are already installed. **No need to pause or reinstall the generators or collectors.** A brief collector restart and possible telemetry gap can occur when changing destinations.

**Only configuration file you need to retain:** `enterprise-values.yaml` (your tested Enterprise Helm configuration, with no plaintext secrets). Keep your old OpenObserve installation and PVC until Enterprise is verified. A fresh Enterprise installation does **not** automatically migrate historical logs or dashboards.

**This guide is when your collector has already been installed.**

## 1. Start Minikube and install Enterprise

Run in **Windows PowerShell** or **macOS/Linux terminal** (same commands):

```sh
minikube status
helm repo add openobserve https://charts.openobserve.ai --force-update
helm repo update
kubectl create namespace stars-2-0 --dry-run=client -o yaml | kubectl apply -f -
```

If `enterprise-values.yaml` references `openobserve-enterprise-admin` as its root-user Secret, create it **before** installing the chart. Use the corresponding block below (skip it if your tested values file uses a different auth setup). Do not commit credentials.

**Windows PowerShell:**

```powershell
$email = Read-Host "Enterprise admin email"
$secure = Read-Host "Enterprise admin password" -AsSecureString
$pass = [System.Net.NetworkCredential]::new("", $secure).Password
kubectl create secret generic openobserve-enterprise-admin -n stars-2-0 --from-literal="ZO_ROOT_USER_EMAIL=$email" --from-literal="ZO_ROOT_USER_PASSWORD=$pass"
Remove-Variable pass,secure -ErrorAction SilentlyContinue
```

**macOS/Linux (Bash):**

```bash
read -r -p "Enterprise admin email: " EMAIL
read -r -s -p "Enterprise admin password: " PASSWORD; echo
kubectl create secret generic openobserve-enterprise-admin -n stars-2-0 \
  --from-literal="ZO_ROOT_USER_EMAIL=$EMAIL" \
  --from-literal="ZO_ROOT_USER_PASSWORD=$PASSWORD"
unset PASSWORD
```

**Note:** If your values file uses another Secret name or chart authentication key, match that configuration. Check the installed chart's values before applying. If the Secret already exists, don't recreate it.

```sh
helm upgrade --install openobserve-enterprise openobserve/openobserve-standalone --namespace stars-2-0 --version 1.1.3 -f enterprise-values.yaml
kubectl get pods,svc -n stars-2-0
```

The Enterprise pod should be `Running` and `Ready`. In another terminal, access the UI:

```sh
kubectl port-forward -n stars-2-0 svc/openobserve-enterprise-openobserve-standalone 5080:5080
```

Open **http://localhost:5080** and confirm the header shows **Edition: Enterprise**. If local port 5080 is occupied, use `5082:5080` and visit port 5082.

## 2. Get your Enterprise access key (REQUIRED)

Open **OpenObserve Enterprise → Data Sources → Kubernetes** (or **Manage Tokens** if using a dedicated ingestion account). Copy the **access key** associated with the user account that will ingest telemetry. **Do not paste the key into this Markdown file or into GitHub.**

**You will enter the access key at a terminal prompt in Step 3.** When the terminal asks:

```text
Enterprise account email:      ← enter the email for the account owning the key
Enterprise access key:         ← paste your access key (input stays hidden)
```

OpenObserve's collector exporter expects an Authorization header in this format:

```text
Authorization: Basic <base64(email:access_key)>
```

The scripts below generate that header automatically. **A raw key alone is not the value of the Authorization header.** If your account's access key cannot be used with Basic auth, use its account password or a compatible service-account token instead; do not guess the required format. The login-email/password pair we previously tested is also valid for this installation.

## 3. Point the existing collectors at Enterprise

The in-cluster OTLP/HTTP endpoint is:

```text
http://openobserve-enterprise-openobserve-standalone.stars-2-0.svc.cluster.local:5080/api/default
```

Do **not** use `localhost` in the collector's Helm values. The following scripts explicitly ask for your **access key**, build the Basic authentication header, then generate a **temporary Helm override** for both agent and gateway exporters. Use the block for your operating system.

### Windows (PowerShell)

```powershell
$email = Read-Host "Enterprise account email (associated with access key)"
$secureKey = Read-Host "Enterprise access key" -AsSecureString
$key = [System.Net.NetworkCredential]::new("", $secureKey).Password
$auth = "Basic " + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${email}:${key}"))
$endpoint = "http://openobserve-enterprise-openobserve-standalone.stars-2-0.svc.cluster.local:5080/api/default"

@{
  exporters = @{
    'otlphttp/openobserve' = @{ endpoint = $endpoint; headers = @{ Authorization = $auth } }
    'otlphttp/openobserve_k8s_events' = @{ endpoint = $endpoint; headers = @{ Authorization = $auth } }
  }
} | ConvertTo-Json -Depth 10 | Set-Content -Encoding ascii collector-enterprise-temp.json

Remove-Variable key, secureKey, auth -ErrorAction SilentlyContinue
```

### macOS / Linux (Bash)

```bash
read -r -p "Enterprise account email (associated with access key): " EMAIL
read -r -s -p "Enterprise access key: " ACCESS_KEY; echo
AUTH="Basic $(printf '%s:%s' "$EMAIL" "$ACCESS_KEY" | base64 | tr -d '\n')"
export AUTH
python3 - <<'PYCODE'
import json, os
endpoint = 'http://openobserve-enterprise-openobserve-standalone.stars-2-0.svc.cluster.local:5080/api/default'
exporters = {
    name: {'endpoint': endpoint, 'headers': {'Authorization': os.environ['AUTH']}}
    for name in ('otlphttp/openobserve', 'otlphttp/openobserve_k8s_events')
}
with open('collector-enterprise-temp.json', 'w') as f:
    json.dump({'exporters': exporters}, f)
PYCODE
unset ACCESS_KEY AUTH
```

### Apply the collector update (both platforms)

The file generated above contains the **Enterprise endpoint and access-key-derived header**. Helm accepts JSON as a values file. Before upgrading, identify your **currently installed** collector chart version using `helm list -n openobserve-collector`; pin that chart version using `--version` if necessary to avoid unintentionally updating the chart at the same time.

```sh
helm upgrade o2c openobserve/openobserve-collector --namespace openobserve-collector --reuse-values -f collector-enterprise-temp.json
kubectl get pods -n openobserve-collector
```

The two collectors can restart briefly. **Only delete the temporary file after Helm completes successfully.**

```powershell
# Windows PowerShell
Remove-Item collector-enterprise-temp.json
```

```bash
# macOS/Linux
rm collector-enterprise-temp.json
```

**Security:** The temporary file contains a reversible credential. Keep it out of Git, and remember Helm/Kubernetes may still retain the header in release/configuration data. For a more secure long-term team deployment, configure exporters to read credentials from a Kubernetes Secret using a supported collector configuration mechanism.

## 4. Verify ingestion

1. In Enterprise, open **Logs**, choose the `default` organization, and set a recent time range.
2. Confirm `service=log-generator` heartbeat logs and `service=error-generator` error logs appear. If they do, the Enterprise endpoint and credentials are working for log ingestion.
3. Check the agent and gateway for new `401 Unauthorized` errors:

```sh
kubectl logs -n openobserve-collector daemonset/o2c-openobserve-collector-agent-collector --since=5m --tail=50
kubectl logs -n openobserve-collector statefulset/o2c-openobserve-collector-gateway-collector --since=5m --tail=50
```

**Notes:** Keep generators in `stars`, collectors in `openobserve-collector`, and Enterprise in `stars-2-0`; namespaces do not need to match. Retain the old Community data/PVC until you're sure you no longer need historical data. For a same-instance edition conversion or migration of old data, use a separate backup/upgrade procedure.

**References:** [OpenObserve Helm charts](https://github.com/openobserve/openobserve-helm-chart) · [Collector Helm chart](https://github.com/openobserve/openobserve-helm-chart/tree/main/charts/openobserve-collector) · [OTLP ingestion](https://openobserve.ai/docs/ingestion/logs/otlp/)
