# OpenObserve Standalone (Community) to Enterprise — In-Place Upgrade

This guide follows the **existing Helm-release upgrade** used by our team. It upgrades OpenObserve in Minikube without creating a second namespace or reinstalling the OpenTelemetry collectors.

## Prerequisites

- Minikube, `kubectl`, and Helm are installed and working.
- OpenObserve Standalone is already installed as Helm release **`openobserve`** in namespace **`stars`**.
- OpenTelemetry collectors and the log/error generators are already installed.
- The example below matches our tested starting point: **OpenObserve `v1.0.1`** and **standalone Helm chart `1.0.1`**. If your versions differ, confirm chart values and a compatible Enterprise image tag before running the upgrade.

> This is an **in-place** upgrade. It reuses the existing Kubernetes Service and persistent storage. We chose not to back up historical logs for this local test environment. For data you cannot afford to lose, take a PVC/data backup before upgrading.

## 1. Check the existing installation

These commands work in **Windows PowerShell, macOS, and Linux**:

```sh
minikube status
helm list -n stars
kubectl get pods -n stars
kubectl get pvc -n stars
kubectl get statefulset openobserve-openobserve-standalone -n stars -o jsonpath='{.spec.template.spec.containers[0].image}'
```

Check that `openobserve` exists and the current image is the expected Community version.

## 2. Add/update the Helm repository

```sh
helm repo add openobserve https://charts.openobserve.ai --force-update
helm repo update
helm show values openobserve/openobserve-standalone --version 1.0.1
```

The last command lets you inspect that chart version before the upgrade.

## 3. Upgrade the existing release to Enterprise

**Windows — PowerShell:**

```powershell
helm upgrade openobserve openobserve/openobserve-standalone `
  -n stars `
  --version 1.0.1 `
  --reuse-values `
  --set image.repository=o2cr.ai/openobserve/openobserve-enterprise `
  --set image.tag=v1.0.1 `
  --set enterprise.enabled=true
```

**macOS / Linux — Bash or Zsh:**

```bash
helm upgrade openobserve openobserve/openobserve-standalone \
  -n stars \
  --version 1.0.1 \
  --reuse-values \
  --set image.repository=o2cr.ai/openobserve/openobserve-enterprise \
  --set image.tag=v1.0.1 \
  --set enterprise.enabled=true
```

This is the in-place image-switch approach from our teammate's guide, with the chart version pinned. **Do not change the namespace or release name** if you want to keep the existing Service, dashboards, and storage.

> Helm chart values can differ across releases. The commands above describe the team's `1.0.1` path; do not blindly use them for newer versions.

## 4. Verify the upgrade

```sh
kubectl rollout status statefulset/openobserve-openobserve-standalone -n stars
kubectl get pods -n stars
kubectl get statefulset openobserve-openobserve-standalone -n stars -o jsonpath='{.spec.template.spec.containers[0].image}'
```

The OpenObserve pod should become Ready and the image should show the Enterprise repository. Open the dashboard by running:

```sh
kubectl port-forward -n stars svc/openobserve-openobserve-standalone 5080:5080
```

Visit **http://localhost:5080** and verify that OpenObserve identifies itself as **Enterprise**. Existing dashboards should remain if the original metadata storage was retained (as happened in our laptop upgrade).

## 5. Verify collectors (do not reinstall them)

The existing collector destination should still be:

```text
http://openobserve-openobserve-standalone.stars.svc.cluster.local:5080/api/default
```

Because this upgrade keeps the same Kubernetes Service, you normally **do not need to change collector endpoints**. If the Enterprise instance accepts the same ingestion credentials, you also do not need a new access key or Authorization header.

Check the collector pods:

```sh
kubectl get pods -n openobserve-collector
```

Then open **Enterprise → Logs** and confirm that *new* logs from the log generator and error generator are arriving. Existing dashboards alone do **not** prove ingestion works.

If logs stop arriving, inspect the collector errors:

```sh
kubectl logs -n openobserve-collector daemonset/o2c-openobserve-collector-agent-collector --since=5m --tail=50
kubectl logs -n openobserve-collector statefulset/o2c-openobserve-collector-gateway-collector --since=5m --tail=50
```

- **401 Unauthorized:** the collector's ingestion credentials are not accepted; check the configured `Authorization` header. For HTTP Basic, the value is `Basic <base64(email:password-or-valid-ingestion-token)>` — not the raw access key.
- **Connection errors:** check that the original OpenObserve Service is healthy and the collector endpoint still matches it.

Do not paste credentials into GitHub or screenshots. For this in-place path, there is **no separate access-key entry step unless authentication actually changes**.

## Result

**Community → Enterprise, same `stars` namespace, same Helm release, same Service, same collectors, and existing dashboards retained.** No new Enterprise namespace, collector reinstall, or generator pause is required for the basic image-switch route; a brief ingestion interruption may occur during the restart.

## References

- Team member's `enterprise.md` (in-place upgrade approach)
- OpenObserve Helm charts: https://github.com/openobserve/openobserve-helm-chart
- Helm chart upgrade notes: https://github.com/openobserve/openobserve-helm-chart/blob/main/UPGRADING.md
