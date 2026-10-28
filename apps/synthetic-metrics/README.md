# Synthetic Metrics Generator

Creates fake (synthetic) CPU and memory readings so the team can test monitoring in OpenObserve. Most of the time the numbers look healthy, and on a fixed schedule they show a **CPU spike** or a **memory leak**.

```text
synthetic-metrics pod  --->  OpenObserve collector  --->  OpenObserve (Logs page)
 (prints a line every 5 s)    (reads the pod's logs)        (default stream)
```

Everything here is simulated: `synthetic-host-1` does not exist.

All commands run from the **root of the repository**. They work the same in macOS Terminal and Windows PowerShell.

---

## Before you start

You need Minikube running with OpenObserve and its collector installed. Check:

```bash
kubectl get pods -n stars
kubectl get pods -n openobserve-collector
```

You should see an `openobserve-...` pod and the `o2c-...` collector pods, all `Running`. If not, set them up first:

1. Minikube and the `stars` namespace: `infrastructure/README.md`
2. OpenObserve: `observability/install.md`
3. The collector: `observability/collector.md`

---

## Step 1: Start the generator

```bash
kubectl create configmap synthetic-metrics-script -n stars --from-file=apps/synthetic-metrics/synthetic_metrics.py --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f apps/synthetic-metrics/deployment.yaml
```

The first command loads the script into the cluster. It is **one line**. The second command starts the pod.

You should see `configmap/synthetic-metrics-script created` and `deployment.apps/synthetic-metrics created`.

The schedule starts counting **from the moment the pod starts**, so note the time.

## Step 2: Check that it is running

```bash
kubectl get pods -n stars -l app=synthetic-metrics
```

Wait until `READY` shows `1/1` (a few seconds). Then watch the output:

```bash
kubectl logs -n stars -l app=synthetic-metrics -f
```

You should see a startup line, a settings line, a ready line, then one new metrics line every 5 seconds:

```text
... level=INFO service=synthetic-metrics run_id=metrics01 event=startup message="Process started"
... level=INFO ... run_id=metrics01 message="Settings interval_s=5 anomalies=on cpu_spike=every 5 min memory_leak=minutes 35-50 of each hour"
... level=INFO service=synthetic-metrics scenario=metrics host=synthetic-host-1 run_id=metrics01 cpu_percent=24.71 memory_percent=54.93
... level=INFO service=synthetic-metrics run_id=metrics01 event=ready message="Ready to serve"
```

Press Ctrl+C to stop following the log. The pod keeps running.

## Step 3: See the data in OpenObserve

1. In a second terminal, start the port-forward and leave it running:
   ```bash
   kubectl port-forward -n stars svc/openobserve-openobserve-standalone 5080:5080
   ```
2. Open <http://localhost:5080> and log in with the email and password from your `observability/values.local.yaml`.
3. Click **Logs**, choose the **default** stream, and set the time range to **Past 15 Minutes**.
4. Paste this into the query box and click **Run query**:
   ```sql
   k8s_container_name = 'synthetic-metrics'
   ```

You should see one line every 5 seconds.

## Step 4: See a CPU spike

Wait until **5 minutes** after the pod started. Then run this query (turn on **SQL mode** first):

```sql
SELECT _timestamp, body
FROM "default"
WHERE k8s_container_name = 'synthetic-metrics'
  AND TRY_CAST(regexp_replace(body, '.*cpu_percent=([0-9.]+).*', '\1') AS DOUBLE) > 65
ORDER BY _timestamp DESC
```

You should see about 12 lines with `cpu_percent` around 80: one minute of high CPU. This repeats every 5 minutes.

## Step 5: See a memory leak

Wait until **at least 40 minutes** after the pod started. Then run this query (in **SQL mode**):

```sql
SELECT _timestamp, body
FROM "default"
WHERE k8s_container_name = 'synthetic-metrics'
  AND TRY_CAST(regexp_replace(body, '.*memory_percent=([0-9.]+).*', '\1') AS DOUBLE) > 65
ORDER BY _timestamp DESC
```

You should see `memory_percent` climbing toward 85. The leak runs from minute 35 to 50, and repeats every hour.

### Find the exact event times

The generator logs a line each time an event starts and ends. To see only those lines:

```sql
k8s_container_name = 'synthetic-metrics' AND body LIKE '%message=%'
```

```text
... level=WARN ... message="CPU spike started"
... level=INFO ... message="CPU spike ended"
... level=WARN ... message="Memory leak started"
... level=INFO ... message="Memory leak ended"
```

Use these times when you record what happened in a test.

---

## The schedule

Times are counted from when the pod started.

| Event | When | What you will see |
|---|---|---|
| Normal | All other times | CPU around 25%, memory around 55%, with small random changes |
| CPU spike | Minute 4-5, 9-10, 14-15, ... (the last minute of every 5) | CPU jumps to about 80% |
| Memory leak | Minute 35-50 of every hour | Memory climbs steadily from 55% to about 85%, then drops back |

Restarting the pod restarts the schedule from minute 0.

---

## Settings

Two settings live in `deployment.yaml` under `env`:

| Setting | Default | Purpose |
|---|---|---|
| `RUN_ID` | `metrics01` | Added to every line as `run_id=...`, so one search finds a whole run. Use a new value for each test run. Letters, digits, `_` and `-`, up to 64 characters |
| `ANOMALIES` | `on` | `on` = CPU spikes and memory leak on the schedule above. `off` = normal values only |

To change them without editing the file (this restarts the pod, so the schedule starts again from minute 0):

```bash
kubectl set env deployment/synthetic-metrics -n stars RUN_ID=baseline01 ANOMALIES=off
```

Use `ANOMALIES=off` for **baseline runs**, when you need a stretch of purely normal data. Find a run in OpenObserve with:

```sql
k8s_container_name = 'synthetic-metrics' AND body LIKE '%run_id=baseline01 %'
```

---

## Update after changing a file

If you edit `synthetic_metrics.py` or `deployment.yaml`, run all three:

```bash
kubectl create configmap synthetic-metrics-script -n stars --from-file=apps/synthetic-metrics/synthetic_metrics.py --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f apps/synthetic-metrics/deployment.yaml
kubectl rollout restart deployment synthetic-metrics -n stars
```

Then repeat Step 2.

## Stop and remove

Pause it (keeps everything, starts again from minute 0):

```bash
kubectl scale deployment synthetic-metrics -n stars --replicas=0
kubectl scale deployment synthetic-metrics -n stars --replicas=1
```

The first line stops it, the second starts it again.

Remove everything this component created:

```bash
kubectl delete deployment synthetic-metrics -n stars
kubectl delete configmap synthetic-metrics-script -n stars
```

This only removes it from the cluster. The files in the repo stay.

---

## Troubleshooting

| What you see | What to do |
|---|---|
| `namespaces "stars" not found` | Create it: `kubectl create namespace stars` |
| Pod stuck in `ContainerCreating` or `ImagePullBackOff` | The cluster cannot download `python:3.12-slim`. Check Minikube's internet access |
| `READY` stays `0/1`, or the pod keeps restarting | Run `kubectl logs -n stars -l app=synthetic-metrics`. A Python error there means the script crashed. Then run `kubectl describe pod -n stars -l app=synthetic-metrics` and read `Events` at the bottom |
| `configmap "synthetic-metrics-script" not found` in `Events` | You skipped the first command in Step 1. Run it, then `kubectl rollout restart deployment synthetic-metrics -n stars` |
| Logs show in Step 2 but OpenObserve is empty | Widen the time range, and check the collector pods are `Running` |
| The spike or leak query returns nothing | It has not happened yet. Check how long ago the pod started: `kubectl get pods -n stars -l app=synthetic-metrics` (`AGE` column) |

---

## How it works

| File | Purpose |
|---|---|
| `synthetic_metrics.py` | The generator. Prints one line every 5 seconds |
| `deployment.yaml` | Runs the script in one pod, with health checks |

**Health checks.** Every time the script prints a line, it also updates the file `/tmp/ready`. Kubernetes checks that file:

- **Startup check:** the file must appear within 30 seconds, or the pod is restarted.
- **Readiness check:** the file must have been updated in the last 30 seconds, or `READY` shows `0/1`. This catches a script that is running but stuck.

**Startup and readiness logs.** For the Observability team's startup monitoring, the script logs these two lines (format agreed with Observability):

```text
<UTC time> level=INFO service=synthetic-metrics run_id=<RUN_ID> event=startup message="Process started"
<UTC time> level=INFO service=synthetic-metrics run_id=<RUN_ID> event=ready message="Ready to serve"
```

`event=startup` is printed as soon as the script starts. `event=ready` is printed once, right after the first metrics line, at the same moment the ready file is created. The time between them is the startup time.

When the pod is stopped, the script logs `Stopping` and exits cleanly.
