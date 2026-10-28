# Log Generator

Simple Kubernetes application that continuously writes log lines to stdout in the `stars` namespace. It supports manual WARN, ERROR, error-spike, connectivity, and crash scenarios, plus optional automatic 20-error spikes for OpenObserve testing.

## Prerequisites

Make sure Minikube is running:

```bash
minikube status
```

Make sure the stars namespace exists:

```bash
kubectl get namespace stars
```

If the namespace does not exist, create it:

```bash
kubectl create namespace stars
```

## Deploy the Application

From the root of the repository, run:

```bash
kubectl apply -f apps/log-generator/deployment.yaml
kubectl -n stars rollout status deployment/log-generator --timeout=120s
```

Wait for the rollout to succeed before continuing.

## Verify the Pod

List the pods:

```bash
kubectl get pods -n stars
```

Find the pod whose name starts with `log-generator`. It should show `Running` under STATUS and `1/1` under READY. Copy its name from the NAME column.

In the commands below, replace `<pod-name>` with that name, including removing the angle brackets.

## View the Logs

View the last 20 log lines:

```bash
kubectl logs <pod-name> -n stars --tail=20
```

You should see INFO heartbeat logs with an increasing count approximately every five seconds.

In a second terminal, follow the logs while you run tests in the original terminal:

```bash
kubectl logs -f <pod-name> -n stars
```

Ctrl+C stops following logs without stopping the application. If the pod is replaced, list the pods again and use its new name.

## Test WARN, ERROR, and Failures

Run one test at a time. `Queued` means the request was accepted; wait for `Scenario completed` in the logs before the next test. Each test below produces INFO start/completion markers, and heartbeats continue without a restart.

The last argument is a run ID. Use a new ID when repeating a test (for example, `warn02`). IDs allow 1–64 letters, digits, underscores, or hyphens.

### WARN

```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger warn warn01
```

Expected: one WARN line with `run_id=warn01`.

### ERROR

```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger error error01
```

Expected: one ERROR line with `run_id=error01`.

### Error Spike

```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger error-spike spike01
```

Expected: 20 ERROR lines numbered 1–20 with `run_id=spike01`. WARN, ERROR, and error-spike tests generate synthetic log events.

### Connectivity Failure

```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger connectivity network01
```

Expected: one ERROR with `run_id=network01`, `target=127.0.0.1:1`, and a nonzero `wget_exit` (normally `1`). This is an intentional failed connection to a local port inside the pod. `Unexpected HTTP success` means the test is invalid.

## Test Container Crash and Recovery

Run this test last. Check the log-generator pod's RESTARTS column and write down the number:

```bash
kubectl get pods -n stars
```

Trigger the crash:

```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger crash crash01
```

Expected: an ERROR with `run_id=crash01` and `exiting with code 42`. There is no completion marker; Kubernetes automatically restarts the container.

After a short wait, check the pods again:

```bash
kubectl get pods -n stars
```

The log-generator pod should return to `Running` with READY `1/1`. Its RESTARTS count should increase by **one** (for example, from `0` to `1`). If it has not restarted yet, wait and check again.

Check the crash exit code:

```bash
kubectl describe pod <pod-name> -n stars
```

Under **Containers → log-generator → Last State**, look for `Terminated` and **Exit Code: 42**. The current State should be `Running`.

View the crashed container's logs:

```bash
kubectl logs <pod-name> -n stars --previous
```

Confirm the current container is producing heartbeats again:

```bash
kubectl logs <pod-name> -n stars --tail=20
```

The heartbeat counter resets after restart. Restart log following if it stopped. Repeated crashes close together may delay recovery.

## Automatic Error Spikes

The combined `log-generator` also generates automatic spikes: **20 ERROR logs every ~20 seconds** when `AUTO_SPIKE=true`. This runs separately from the manual `error-spike` scenario. Each batch has four errors in each category: `authentication`, `database`, `connectivity`, `dependency`, and `service`. All are simulated.

The default in `apps/log-generator/deployment.yaml` is `AUTO_SPIKE: "false"`. To test it without editing the file:

```powershell
kubectl set env deployment/log-generator -n stars AUTO_SPIKE=true   # Turn on automatic spikes
kubectl rollout status deployment/log-generator -n stars            # Wait for the rollout
kubectl logs -n stars deployment/log-generator --tail=30            # Check the generated logs
```

Automatic logs contain `service=log-generator`, `spike=true`, `scenario=<type>`, `run_id=auto-...`, and `error_index=1` through `20`. All 20 errors in one batch share the same `run_id`; each new batch gets a different one. This replaces the old `spike_id` field.

To count one batch, replace `YOUR_RUN_ID` with an ID from the logs:

```powershell
kubectl logs -n stars deployment/log-generator | Select-String 'level=ERROR.*spike=true run_id=YOUR_RUN_ID ' | Measure-Object  # Expect Count: 20
```

Turn it off when finished:

```powershell
kubectl set env deployment/log-generator -n stars AUTO_SPIKE=false  # Stop automatic spikes
kubectl rollout status deployment/log-generator -n stars           # Wait for the rollout
```

`kubectl set env` changes the Kubernetes Deployment, not your local YAML. The five manual scenarios and heartbeat logs still work when automatic spikes are enabled.

## OpenObserve Dashboard

The Log Generator writes logs to Kubernetes stdout. The OpenObserve Collector collects them and sends them to the `default` stream for the **STARS Error Monitoring** dashboard.

For the dashboard setup, all seven SQL queries, and panel explanations, see:

```text
observability/dashboards/README.md
```

That dashboard uses logs from the combined `log-generator` for both manual scenarios and automatic error spikes.

## Delete the Application (Optional)

```bash
kubectl delete -f apps/log-generator/deployment.yaml
```
