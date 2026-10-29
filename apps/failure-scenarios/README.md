# STARS Failure Scenario Test Catalog

Expected logs, traces, metrics and behavior for every STARS generator, with a test case for each scenario. The pass/fail criteria are written so they can be turned into automated checks later.

## Contents
* [1. Log Generator](#Part-1-log-generator)
* [2. Trace Generator](#Part-2-trace-generator)
* [3. Syntehtic Metrics](#Part-3-synthetic-metrics)
* [4. Automatic Error Spike](#Part-4-Automatic-error-spike)
* [5. Locust](#Part-5-Locust-traffic)
* [6. Readiness](#Part-6-Readiness)
* [7. Test Case Catalog](#Test-case-catalog)
* [8. Notes](#Notes)

## Generators and Their Scenarios
| Part | Generator | Scenarios |
|------|-----------|-----------|
| 1 | log-generator | `warn`, `error`, `error-spike`, `connectivity`, `crash` |
| 2 | trace-generator | `normal`, `slow-db`, `payment-errors` |
| 3 | synthetic-metrics | CPU spike, memory leak |
| 4 | log-generator (automatic) | Automatic error spike |
| 5 | Locust | `normal`, `high-traffic`, `failing`, `mixed` |
| 6 | All long-running apps | Startup and readiness |

## Conventions

- **Mac (Terminal) and Windows (PowerShell)** commands are both shown where they differ. Plain `kubectl` commands are the same on both.
- Everything runs in the `stars` namespace on minikube, from the repo root (Locust: from its own folder).
- Use a **unique `run_id` per run** (letters, digits, `_`, `-`; max 64 characters) so one search finds a whole run. Locust and the automatic spikes generate their own.
- **Observed** = captured from real runs on Oct 28 and 29 (minikube on a Mac). Counts and timings are approximate, so use tolerances in automated checks.
- **Not tested:** the Windows (PowerShell) commands (no Windows machine was available), whether a Not Ready `synthetic-metrics` pod leaves its Service endpoints (TC-17), and sending Locust results to OpenObserve.

---

# Part 1: log-generator

A shell script runs as PID 1. It logs a heartbeat about every 5 seconds and checks once per second for a queued scenario (at most one per tick). Scenarios are queued with `/tmp/stars-trigger`. Requests are cleared on every container start, so a scenario **never repeats after a restart**.

**Log format.** Scenario lines are bracketed by `Scenario started` and `Scenario completed` (INFO), except `crash`.

```
2026-10-28T02:40:32Z level=INFO service=log-generator event=startup message="Process started" run_id=startup-20261028T024032Z-1
2026-10-28T02:40:32Z level=INFO service=log-generator event=ready message="Ready to serve" run_id=startup-20261028T024032Z-1
2026-10-28T02:40:37Z level=INFO service=log-generator message="STARS heartbeat" run_id=startup-20261028T024032Z-1 count=2
<UTC> level=<LEVEL> service=log-generator scenario=<scenario> run_id=<RUN_ID> message="<message>"
```

The startup `run_id` is generated when the process starts, so a **new startup `run_id` identifies a restart**.

**Trigger** (same on Mac and Windows). The command only queues the request; logs appear within about 1 second.

```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger <SCENARIO> <RUN_ID>
```

**Check one run:**

```bash
# Mac (Terminal)
kubectl -n stars logs deployment/log-generator -c log-generator | grep 'run_id=<RUN_ID>'
```
```powershell
# Windows (PowerShell)
kubectl -n stars logs deployment/log-generator -c log-generator | Select-String 'run_id=<RUN_ID>'
```

> The outputs below are from the merged log-generator deployed on Oct 29 (`kubectl apply -f apps/log-generator/deployment.yaml`). Runs on Oct 28 with the pre-merge generator produced the same scenario lines.

### 1. `warn` (example: `warn warn03`)

Observed (between `Scenario started` and `Scenario completed` INFO lines in the same second):
```
2026-10-29T18:48:15Z level=WARN service=log-generator scenario=warn run_id=warn03 message="On-demand warning; synthetic degraded condition"
```
Expected: exactly 1 `WARN` with that message, no `ERROR`. Container keeps running, no restart.

### 2. `error` (example: `error error03`)

Observed:
```
2026-10-29T18:48:16Z level=ERROR service=log-generator scenario=error run_id=error03 message="On-demand error; synthetic application failure"
```
Expected: exactly 1 `ERROR` with that message. Container keeps running, no restart.

### 3. `error-spike` (example: `error-spike spike03`)

The **manual** spike: a burst of errors in one second. (The automatic spike is [Part 4](#part-4-automatic-error-spike).)

Observed (first and last of 20; all 20 lines were logged at 18:48:14Z):
```
2026-10-29T18:48:14Z level=ERROR service=log-generator scenario=error-spike run_id=spike03 message="Injected application error 1 of 20"
2026-10-29T18:48:14Z level=ERROR service=log-generator scenario=error-spike run_id=spike03 message="Injected application error 20 of 20"
```
Expected: exactly 20 `ERROR` lines, `N of 20` for N = 1 to 20 in order, all within the same second. Container keeps running, no restart.

### 4. `connectivity` (example: `connectivity network03`)

Tries an HTTP request to a closed loopback port (`127.0.0.1:1`), which always fails. No external network is used.

Observed:
```
2026-10-29T18:48:13Z level=ERROR service=log-generator scenario=connectivity run_id=network03 message="Controlled connection failure target=127.0.0.1:1 wget_exit=1"
```
Expected: exactly 1 `ERROR` with that message. If the request ever succeeded, a `WARN` `Unexpected HTTP success; connectivity test invalid` would appear instead, which means the test environment is invalid. Container keeps running, no restart.

### 5. `crash` (example: `crash crash03`)

Logs an error, then the process exits with code 42 and Kubernetes restarts the container.

Observed (last lines of the crashed container, from `--previous`):
```
2026-10-29T18:48:21Z level=INFO service=log-generator message="STARS heartbeat" run_id=startup-20261029T184531Z-1 count=35
2026-10-29T18:48:21Z level=INFO service=log-generator scenario=crash run_id=crash03 message="Scenario started"
2026-10-29T18:48:21Z level=ERROR service=log-generator scenario=crash run_id=crash03 message="Injected container crash; exiting with code 42"
```
No `Scenario completed` line follows. One second later the new container logged a **new** startup `run_id` and the heartbeat `count` was back at 1:
```
2026-10-29T18:48:22Z level=INFO service=log-generator event=startup message="Process started" run_id=startup-20261029T184822Z-1
2026-10-29T18:48:22Z level=INFO service=log-generator message="STARS heartbeat" run_id=startup-20261029T184822Z-1 count=1
```
Pod 15 seconds after the crash (a new pod with no earlier restarts, so the count went from 0 to 1):
```
NAME                             READY   STATUS    RESTARTS      AGE
log-generator-6fd89d5fdf-nffgk   1/1     Running   1 (15s ago)   3m5s
```
Exit code, from `kubectl describe pod` (captured Oct 28 on the pre-merge generator):
```
Last State:     Terminated
  Reason:       Error
  Exit Code:    42
```
Expected:
- 1 `ERROR` with that message and **no** `Scenario completed`
- Exit code **42**; `RESTARTS` goes up by 1; pod back to `1/1 Running` within seconds
- After restart: new `event=startup` and `event=ready` lines with a **new** startup `run_id`, and the heartbeat `count` restarts from a low value
- The crash does not repeat

Verify:
```bash
kubectl get pods -n stars
kubectl logs <pod-name> -n stars --previous
```
```bash
# Mac (Terminal)
kubectl describe pod <pod-name> -n stars | grep -A4 "Last State"
```
```powershell
# Windows (PowerShell)
kubectl describe pod <pod-name> -n stars | Select-String "Last State" -Context 0,4
```

---

# Part 2: trace-generator

A Kubernetes **Job** creates fake OpenTelemetry traces for a set number of seconds, then stops by itself (it never repeats). Traces go through the OpenObserve collector to OpenObserve. Each trace has **7 spans** across `frontend`, `api`, `db` and `payment`. Every span has `run_id` and `scenario`.

Prerequisite: minikube with OpenObserve and its collector running (`kubectl get pods -n stars` and `-n openobserve-collector`), and internet access for the Job to download packages.

**Job log** has a start and end line:
```
... level=INFO service=trace-generator scenario=<scenario> run_id=<RUN_ID> message="Run started rate=2.0 duration_s=<S> error_rate=<P> extra_db_ms=<MS>"
... level=INFO service=trace-generator scenario=<scenario> run_id=<RUN_ID> message="Run completed traces=<N> failed_traces=<M>"
```

**Trigger** (`<SCENARIO>` is `normal`, `slow-db` or `payment-errors`; use a new run ID every time):

```bash
# Mac (Terminal), or Git Bash / WSL2 on Windows
chmod +x apps/trace-generator/run.sh
apps/trace-generator/run.sh <SCENARIO> <RUN_ID> 60
```
```powershell
# Windows (PowerShell): set the first three values, then run the rest
$Scenario = "<SCENARIO>"
$RunId    = "<RUN_ID>"
$Duration = 60

$JobName = "trace-generator-" + $RunId.ToLower().Replace("_", "-")
kubectl -n stars create configmap trace-generator --from-file=apps/trace-generator/generator.py --from-file=apps/trace-generator/requirements.txt --dry-run=client -o yaml | kubectl apply -f -
(Get-Content apps/trace-generator/job.yaml -Raw) -replace "__JOB_NAME__", $JobName -replace "__SCENARIO__", $Scenario -replace "__RUN_ID__", $RunId -replace "__DURATION__", $Duration | kubectl create -f -
```
Keep run IDs under 40 characters. The PowerShell version does not validate the scenario name; a wrong one makes the Job fail at once, so check the log.

**Watch, wait, view** (same on Mac and Windows):
```bash
kubectl -n stars logs -f job/trace-generator-<RUN_ID>
kubectl -n stars wait --for=condition=complete job/trace-generator-<RUN_ID> --timeout=180s
kubectl -n stars port-forward svc/openobserve-openobserve-standalone 5080:5080
```
Then open <http://localhost:5080>, click **Traces**, set **Past 15 Minutes**, and filter with `service_stars_run_id = '<RUN_ID>'` (this is how OpenObserve names the run ID field). Traces appear after a short delay, and runs older than the time range show nothing.

| # | Scenario | Example trigger args | Expected | Observed (Job log: traces / failed) |
|---|----------|----------------------|----------|-------------------------------------|
| 6 | `normal` | `normal trace01 60` | About 2 traces per second (about 120 in 60 s), about 1% failures, fast traces, Job ends by itself | `trace01` (Oct 28): 120 / 1 |
| 7 | `slow-db` | `slow-db trace02 60` | `db` spans about 800 ms longer, `api` and `frontend` slower too, fewer than 2 traces per second (requests run one at a time). No extra errors are injected, but the 1% base failure rate still applies | `trace02` (Oct 28): 66 / 1. `trace05` (Oct 29): 67 / 1 |
| 8 | `payment-errors` | `payment-errors trace03 60` | About 70% of traces fail; the error starts at `payment` and shows on `api` and `frontend` above it; successful traces look like `normal` | `trace03` (Oct 28): 120 / 81 (67.5%). `trace06` (Oct 29): 120 / 88 (73.3%) |

Run settings seen in the Job log: `normal` `error_rate=0.01 extra_db_ms=0`; `slow-db` `error_rate=0.01 extra_db_ms=800`; `payment-errors` `error_rate=0.7 extra_db_ms=0`.

**Observed in OpenObserve (Oct 29, Traces, `default` stream, Past 15 Minutes):**
- **`normal`:** 120 traces found (matching the Job log), every trace with 7 spans and status SUCCESS, lasting about 60 to 160 ms. No error traces.
- **`slow-db` (`trace05`):** 67 traces found, 1 error trace. Traces lasted about 860 to 960 ms. The `db SELECT orders` span took 838.32 ms in a 934.13 ms trace and 837.28 ms in a 912.02 ms trace, against 27.79 ms in a normal-speed trace.
- **`payment-errors` (`trace06`):** failed traces show `4 ERRORS` on 7 spans and last 77 to 138 ms. The 4 red spans are `payment POST /charge` (503), `api POST payment/charge` (503), `api POST /checkout` (502) and `frontend GET /checkout` (502). `frontend POST api/checkout`, `api db query` and `db SELECT orders` are not in error.

**Span structure** of a successful trace (from the `payment-errors` run, whose successful traces look like `normal`): 7 spans across 4 services, 0 errors.
```
frontend GET /checkout              96.44 ms  200
  frontend POST api/checkout        88.82 ms
    api POST /checkout              88.73 ms  200
      api db query                  27.91 ms
        db SELECT orders            27.79 ms
      api POST payment/charge       54.26 ms
        payment POST /charge        54.17 ms  200
```

---

# Part 3: synthetic-metrics

A one-pod **Deployment** prints a fake CPU and memory reading every 5 seconds; the collector ships the lines to OpenObserve (Logs, `default` stream). On a schedule counted **from pod start** (a restart resets it to minute 0):

| Event | When | Numbers |
|-------|------|---------|
| Normal | Other times | CPU about 25%, memory about 55% |
| CPU spike | Minute 4-5, 9-10, 14-15, ... | CPU about 80% |
| Memory leak | Minute 35-50 of every hour | Memory climbs from about 55% to about 85%, then drops back |

**Log lines:**
```
<UTC> level=INFO service=synthetic-metrics scenario=metrics host=synthetic-host-1 run_id=<RUN_ID> cpu_percent=<N> memory_percent=<N>
... level=WARN ... message="CPU spike started"    /  level=INFO ... message="CPU spike ended"
... level=WARN ... message="Memory leak started"  /  level=INFO ... message="Memory leak ended"
<UTC> level=INFO service=synthetic-metrics event=startup message="Process started" run_id=<RUN_ID>
<UTC> level=INFO service=synthetic-metrics event=ready message="Ready to serve" run_id=<RUN_ID>
```

**Start a test run** (same on Mac and Windows). First time only:
```bash
kubectl create configmap synthetic-metrics-script -n stars --from-file=apps/synthetic-metrics/synthetic_metrics.py --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f apps/synthetic-metrics/deployment.yaml
```
Each test run (restarts the pod; **note the time**):
```bash
kubectl set env deployment/synthetic-metrics -n stars RUN_ID=<RUN_ID> ANOMALIES=on
```
**One run covers both scenarios below**: the first CPU spike comes at minute 4-5 and the leak at minute 35-50. Watch with `kubectl logs -n stars -l app=synthetic-metrics -f`. Event lines only:
```bash
# Mac (Terminal)
kubectl logs -n stars -l app=synthetic-metrics | grep "message="
```
```powershell
# Windows (PowerShell)
kubectl logs -n stars -l app=synthetic-metrics | Select-String "message="
```
In OpenObserve (port-forward as in Part 2, **Logs**, `default` stream, SQL mode):

```sql
-- CPU spike lines (scenario 9)
SELECT _timestamp, body FROM "default"
WHERE k8s_container_name = 'synthetic-metrics' AND body LIKE '%run_id=<RUN_ID>%'
  AND TRY_CAST(regexp_replace(body, '.*cpu_percent=([0-9.]+).*', '\1') AS DOUBLE) > 65
ORDER BY _timestamp DESC
```
For the memory leak (scenario 10), use the same query with `memory_percent` instead of `cpu_percent`.

### 9. CPU spike

Expected: `CPU spike started` (WARN) at about minute 4, then about 12 metrics lines (5 s apart for 60 s) with `cpu_percent` around 80, then `CPU spike ended` (INFO). `cpu_percent` is about 25 outside the spike and `memory_percent` stays about 55. Repeats every 5 minutes.

**Observed** (Oct 28, run `metrics-test01`, pod started 22:16:25Z):
```
2026-10-28T22:20:25Z level=WARN service=synthetic-metrics scenario=metrics host=synthetic-host-1 run_id=metrics-test01 message="CPU spike started"
2026-10-28T22:20:25Z level=INFO service=synthetic-metrics scenario=metrics host=synthetic-host-1 run_id=metrics-test01 cpu_percent=82.45 memory_percent=54.99
2026-10-28T22:21:25Z level=INFO service=synthetic-metrics scenario=metrics host=synthetic-host-1 run_id=metrics-test01 message="CPU spike ended"
```
Spikes started at 22:20:25, 22:25:25, 22:30:26, 22:35:26, 22:40:26 and 22:45:26 (every 5 minutes, the first at 4:00 after pod start) and each ended exactly 60 seconds later. At 22:46:01Z, 68 lines had `cpu_percent` above 65: five complete spikes of 12 lines plus 8 lines of the sixth. `memory_percent` stayed about 55 during the spikes.

### 10. Memory leak

Expected: `Memory leak started` (WARN) at about minute 35 and `Memory leak ended` (INFO) at about minute 50. `memory_percent` rises steadily from about 55 to about 85, then returns to about 55. Repeats hourly. CPU spikes still happen on their own 5-minute schedule inside the leak window. Wait about 55 minutes to see the whole cycle.

**Observed** (same run, pod up about 20 hours). The leak runs from minute 35 to 50 after pod start, which is `:51:25` to `:06:25` of every hour for this pod. Four uninterrupted cycles:

| Leak started | Leak ended | Length | `memory_percent` at start | After it ended |
|--------------|------------|--------|---------------------------|----------------|
| 2026-10-28 22:51:26Z | 2026-10-28 23:07:48Z | 16 min 22 s | 55.54 | 54.53 |
| 2026-10-28 23:51:29Z | 2026-10-29 00:06:26Z | 14 min 57 s | 54.41 | 54.83 |
| 2026-10-29 00:51:30Z | 2026-10-29 01:06:25Z | 14 min 55 s | 55.38 | 54.52 |
| 2026-10-29 05:51:26Z | 2026-10-29 06:06:31Z | 15 min 05 s | 55.48 | 54.56 |

Samples inside the leak show a steady climb of about 2 points per minute:
```
2026-10-29T04:51:33Z memory_percent=54.85   (leak started)
2026-10-29T04:56:44Z memory_percent=66.12   (about 5 minutes in)
2026-10-29T01:51:54Z memory_percent=56.64   (leak started)
2026-10-29T02:00:24Z memory_percent=72.92   (about 8.5 minutes in)
2026-10-29T03:51:41Z memory_percent=54.50   (leak started)
2026-10-29T04:03:40Z memory_percent=79.71   (about 12 minutes in)
```
CPU spikes kept happening during the leak, and `CPU spike ended` and `Memory leak started` are logged in the same second because minute 34 to 35 is a spike minute. Later cycles are shifted or stretched (the computer most likely slept overnight), so they are not used as evidence.

---

# Part 4: Automatic error spike

The merged log-generator can make error spikes **on its own**, controlled by the environment variable `AUTO_SPIKE` (default `false`). When it is off, startup logs `scenario=startup ... message="Automatic error spikes disabled"`; when it is on, `... "Automatic error spikes enabled"`. Unlike the manual `error-spike`, each automatic spike gets a generated `run_id` and carries `spike=true` and `error_index`. A spike mixes error types: the 20 errors cycle through 5 types in a fixed order (authentication, database, connectivity, dependency, service), 4 times each.

**Turn on or off** (same on Mac and Windows; restarts the pod):
```bash
kubectl -n stars set env deployment/log-generator AUTO_SPIKE=true
kubectl -n stars set env deployment/log-generator AUTO_SPIKE=false
```
**See the spikes:**
```bash
# Mac (Terminal)
kubectl -n stars logs deployment/log-generator -c log-generator | grep "spike=true"
```
```powershell
# Windows (PowerShell)
kubectl -n stars logs deployment/log-generator -c log-generator | Select-String "spike=true"
```
```sql
-- OpenObserve (Logs, default stream, SQL mode)
SELECT _timestamp, body FROM "default"
WHERE k8s_container_name = 'log-generator' AND body LIKE '%spike=true%'
ORDER BY _timestamp DESC
```
To count lines per spike (Mac; `$6` is the `run_id` field):
```bash
POD=$(kubectl -n stars get pods -l app=log-generator --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}')
kubectl -n stars logs $POD --tail=-1 | grep "spike=true" | awk '{print $6}' | uniq -c
```

### 11. Automatic error spike

Expected per spike: 20 `ERROR` lines with `spike=true`, all sharing one `run_id` of the form `auto-<UTC timestamp>-<n>`, with `error_index` counting up from 1 to 20. The `scenario` and message follow the 5-type cycle in the table below. The next spike has a new `run_id` with `n` one higher. With the setting on, a spike starts **every 20 seconds** (the first in the same second as startup); with it off, no `spike=true` lines appear. Container keeps running, and the lines are searchable in OpenObserve.

| `error_index` | `scenario` | Message |
|---------------|------------|---------|
| 1, 6, 11, 16 | `authentication` | `authentication failure user_id=test-user reason=invalid_token` |
| 2, 7, 12, 17 | `database` | `database timeout database=stars-db timeout_ms=5000` |
| 3, 8, 13, 18 | `connectivity` | `connection failure target=stars-api:8080 reason=connection_refused` |
| 4, 9, 14, 19 | `dependency` | `dependency failure service=payment-api reason=unavailable` |
| 5, 10, 15, 20 | `service` | `service unavailable service=stars-api status=503` |

**Observed (Oct 29, spikes on from 19:04:29Z):** first line of the first spike:
```
2026-10-29T19:04:29Z level=ERROR service=log-generator scenario=authentication spike=true run_id=auto-20261029T190429Z-1 error_index=1 message="authentication failure user_id=test-user reason=invalid_token"
```
- **Size:** 45 spikes in 14 min 41 s, each with exactly 20 lines (900 lines). `run_id` numbers ran 1 to 45 in order with none missing.
- **Order:** in the first spike all 20 lines were logged in the same second and `error_index` ran 1 to 20 with no gaps, following the cycle above.
- **Interval:** a spike every **20 seconds** (44 intervals in 14 min 41 s, an average of 20.0 s; one interval was 21 s).
- **OpenObserve** (Logs, `default`, the query above, Past 15 Minutes): **900 events**, one group of 20 every 20 seconds. All 20 lines of the newest spike fell within 17 ms.
- **Off check:** after `AUTO_SPIKE=false` and a rollout, `grep -c "spike=true"` printed `0` (once after 3 minutes and again after 60 seconds).
- **Restarts:** `log-generator` showed 0 restarts after 33 minutes with spikes on.

---

# Part 5: Locust traffic

Locust runs **inside** the cluster and sends HTTP traffic to `stars-app` (httpbin, `http://stars-app.stars.svc.cluster.local`). This catalog uses the headless **Jobs**, which run **5 minutes**, print a stats table and exit.

| # | Scenario | Users | Ramp up | What it does |
|---|----------|-------|---------|--------------|
| 12 | `normal` | 20 | 2/s | Human-paced requests (1-3 s apart), no errors |
| 13 | `high-traffic` | 200 | 20/s | Near-continuous requests (0.05-0.3 s apart) |
| 14 | `failing` | 20 | 5/s | 500 errors, 404 errors and timeouts (`/delay/5` with a 1 s client timeout gives status 0) |
| 15 | `mixed` | 50 | 5/s | All three user types at once |

**Before you start:** follow the Locust README sections 1 and 3 (start minikube, deploy `stars-app`, create the `locustfile` ConfigMap, deploy Locust). The README says its PowerShell commands are not yet tested.

**Run a scenario** (same on Mac and Windows; `<scenario>` is `normal`, `high-traffic`, `failing` or `mixed`):
```bash
kubectl -n stars delete job locust-<scenario> --ignore-not-found
kubectl apply -f apps/Locust/jobs/<scenario>.yaml
kubectl -n stars logs -f job/locust-<scenario>
kubectl -n stars wait --for=condition=complete job/locust-<scenario> --timeout=420s
```
Start and stop lines only:
```bash
# Mac (Terminal)
kubectl -n stars logs job/locust-<scenario> | grep loadtest
```
```powershell
# Windows (PowerShell)
kubectl -n stars logs job/locust-<scenario> | Select-String loadtest
```
Delete the Job when done: `kubectl -n stars delete job locust-<scenario> --ignore-not-found`.

**Log format.** Locust **generates the `run_id`** (random, 8 characters); read it from the `test_start` line. Each line has a Locust log prefix (timestamp and pod name) before `loadtest {...}`. Real lines from the `normal` run on Oct 28:
```
[2026-10-28 22:23:46,311] locust-normal-m24wd/INFO/stars.loadtest: loadtest {"event": "test_start", "run_id": "bb7333e1", "scenario": "normal", "host": "http://stars-app.stars.svc.cluster.local", "users": 20}
[2026-10-28 22:28:46,202] locust-normal-m24wd/INFO/stars.loadtest: loadtest {"event": "test_stop", "run_id": "bb7333e1", "scenario": "normal", "duration_s": 299.9, "requests": 2949, "failures": 0, "avg_ms": 5.7, "p95_ms": 9}
```

Expected, all scenarios: one `test_start` and one `test_stop` with the same `run_id` and the right `scenario` and `users`, about 5 minutes long, Job ends as `Complete`.
- **normal:** `failures` is 0.
- **high-traffic:** far more requests than `normal`; few or no failures (if minikube is overloaded, failures and slow responses can appear, which is worth noting).
- **failing:** `failures` is greater than 0 and close to `requests`; status codes 500, 404 and 0 appear; the Job still ends `Complete` (it uses `--exit-code-on-error 0`).
- **mixed:** both successes and failures; 2xx, 500, 404 and 0 all appear; Job ends `Complete`.

**Observed (Oct 28):**

| Scenario | `run_id` | Users | Requests | Failures | avg / p95 (ms) | Notes |
|----------|----------|-------|----------|----------|----------------|-------|
| `normal` | `bb7333e1` | 20 | 2,949 | 0 | 5.7 / 9 | About 9.8 requests per second; only `homepage` and `list_items` |
| `high-traffic` | `8bf8f5a4` | 200 | 333,732 | 0 | 1.5 / 3 | About 1,113 requests per second, about 113 times `normal`; no failures |
| `failing` | `5242d0a1` | 20 | 4,186 | 4,186 (100%) | 171.4 / 1000 | 404 `missing_page`: 1,374; 500 `server_error`: 2,113; `slow_request` read timeout (1 s): 699 |
| `mixed` | `32eab399` | 50 | 33,928 | 3,531 (10.4%) | 19.7 / 5 | 404, 500 and timeout errors alongside normal traffic; 1 `ConnectionResetError` on `server_error` |

All four Jobs ran 299.9 seconds and ended `Complete`, including `failing` and `mixed` despite their failures. A 404 **does** count as a failure. The Job's error report lists the 404, 500 and `ReadTimeout` errors for `failing` and `mixed`.

---

# Part 6: Readiness

Long-running apps have a **startup probe** and a **readiness probe** and log these two lines so Observability can measure startup time. The pod must show `READY 1/1` only **after** the `event=ready` line is logged.
```
<UTC> level=INFO service=<app> event=startup message="Process started" run_id=<RUN_ID>
<UTC> level=INFO service=<app> event=ready message="Ready to serve" run_id=<RUN_ID>
```

| App | Selector | Has log lines | Readiness |
|-----|----------|---------------|-----------|
| `log-generator` | `app=log-generator` | Yes | Check with `kubectl -n stars describe deployment log-generator` |
| `synthetic-metrics` | `app=synthetic-metrics` | Yes | `/tmp/ready` must appear within 30 s (startup) and be updated within the last 30 s (readiness), which catches a script that is running but stuck |
| Locust, `stars-app` | `app=locust`, `app=stars-app` | Not documented | HTTP probes (Locust UI; `stars-app` on `/get`) |

Probes of `synthetic-metrics` (from `kubectl describe`). There is **no liveness probe**:
```
Readiness:  exec [python -c import os, sys, time; sys.exit(time.time() - os.path.getmtime('/tmp/ready') > 30)] delay=0s timeout=5s period=10s successThreshold=1 failureThreshold=3
Startup:    exec [test -f /tmp/ready] delay=0s timeout=1s period=2s successThreshold=1 failureThreshold=15
```
Tests cover `log-generator` and `synthetic-metrics`. While a pod is being replaced, the old pod can still be listed first, so pick the **newest** pod:
```bash
# Mac (Terminal)
POD=$(kubectl -n stars get pods -l <SELECTOR> --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}')
```
```powershell
# Windows (PowerShell)
$POD = kubectl -n stars get pods -l <SELECTOR> --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}'
```
Time the pod became Ready, and the event lines:
```bash
# Mac (Terminal)
kubectl -n stars get pod <POD_NAME> -o jsonpath='{.status.conditions[?(@.type=="Ready")].lastTransitionTime}'
kubectl -n stars logs <POD_NAME> | grep "event="
```
```powershell
# Windows (PowerShell)
$p = kubectl -n stars get pod <POD_NAME> -o json | ConvertFrom-Json
($p.status.conditions | Where-Object type -eq Ready).lastTransitionTime
kubectl -n stars logs <POD_NAME> | Select-String "event="
```

### 16. Pod starts and becomes Ready in time

Trigger (same on Mac and Windows):
```bash
kubectl -n stars rollout restart deployment/<APP>
kubectl -n stars rollout status deployment/<APP> --timeout=120s
```
Expected: exactly one `event=startup` and one `event=ready` line for the new pod with the same `run_id`; startup timestamp at or before ready; the pod's Ready time at or after the `event=ready` timestamp (1 s tolerance); `1/1 Running` within 60 s; new pod restart count 0.

**Observed (Oct 29, after `rollout restart`; newest pod selected):**

| App | New pod | `READY` / `RESTARTS` / `AGE` | `event=startup` and `event=ready` | Pod Ready time |
|-----|---------|------------------------------|-----------------------------------|----------------|
| `log-generator` | `log-generator-7b8f896466-c9hq2` | `1/1` / 0 / 3s | both at 19:02:25Z, same `run_id` `startup-20261029T190225Z-1` | 19:02:28Z (3 s after the ready line) |
| `synthetic-metrics` | `synthetic-metrics-7fd8fb767b-68rjv` | `1/1` / 0 / 2s | both at 19:02:46Z, same `run_id` `metrics-test01` | 19:02:48Z (2 s after the ready line) |

In both cases the `event=ready` line was logged before the pod's Ready time, and the new pod had no restarts.

### 17. Pod becomes Not Ready on purpose and recovers

Applies to `synthetic-metrics`. Its readiness probe runs `python` inside the container every 10 s and fails if `/tmp/ready` was not updated in the last 30 s (3 failures in a row make the pod Not Ready). There is no liveness probe, so a failing readiness check must **not** restart the container.

**A probe that cannot run is not a failure.** Hiding `python` (moving `/usr/local/bin/python` away) made the probe **error** (`executable file not found`) instead of **fail**. Kubernetes treats an errored probe as "unknown state", so the pod stayed `1/1 Running` with 0 restarts for the whole 77 seconds. The probe has to run and return a non-zero exit code.

**Method: keep `/tmp/ready` stale.** The generator rewrites `/tmp/ready` every 5 s. A loop inside the pod resets the file's modification time to 1970 every 0.2 s for 70 seconds, so almost every probe sees an old file and exits with 1, while the script itself keeps running. Get `$POD` with the newest-pod command above, then:
```bash
# Mac (Terminal)
kubectl -n stars get pod $POD
kubectl -n stars exec $POD -- sh -c 'end=$(( $(date +%s) + 70 )); while [ $(date +%s) -lt $end ]; do touch -d @0 /tmp/ready; sleep 0.2; done' &
sleep 50
kubectl -n stars get pod $POD
kubectl -n stars logs $POD --tail=2
kubectl -n stars describe pod $POD | grep -i unhealthy
wait
sleep 20
kubectl -n stars get pod $POD
```
The `wait` line lets the 70-second loop finish; after it ends the script rewrites `/tmp/ready` and the pod recovers by itself. On Windows, run the `exec` line (without the final `&`) in a **second PowerShell window**, and the other lines in the first window with `Start-Sleep 50`, `Start-Sleep 20` and `Select-String -Pattern unhealthy` in place of `sleep` and `grep -i unhealthy`.

Expected: about 30 to 50 seconds after the trigger the pod shows `READY 0/1` with status `Running` and the Ready condition `False`; `RESTARTS` does **not** increase; the log still shows a new metrics line every 5 seconds; `describe` lists `Readiness probe failed` events. After the loop ends, the pod returns to `1/1` by itself within about 10 to 20 seconds.

**Observed (Oct 29, pod `synthetic-metrics-7fd8fb767b-68rjv`):** `touch -d @0` was accepted with no error.

| Check | Expected | Observed |
|-------|----------|----------|
| Goes Not Ready | `0/1` within about 30 to 50 s | `1/1` before the trigger, `0/1 Running` at 50 s (the first check, so it may have happened earlier) |
| No restart | `RESTARTS` unchanged | 0 before, during and after |
| Script still running | A metrics line every 5 s | Lines at 19:12:07Z and 19:12:12Z while Not Ready |
| Probe events | `Readiness probe failed` | 6 events (`x6 over 47s`); the message is empty because the probe exits 1 without printing anything |
| Recovers by itself | `1/1` within about 10 to 20 s of the loop ending | `1/1 Running`, 0 restarts, at most 20 s after the loop ended; no manual action |

The two metrics lines show a high `cpu_percent` (82.48 and 76.09) because a scheduled CPU spike was running at that point (minute 9 to 10 of the pod's life), not because of the test.

---

# Test case catalog

Use a **unique run ID per execution** (Locust and the automatic spikes generate their own; read them from the logs). Times run from when the trigger returns (log-generator, trace-generator, Locust) or from pod start (synthetic-metrics). Thresholds match what was observed in real runs.

| ID | Generator | Scenario | Trigger | Expected output | Expected behavior | Pass criteria |
|----|-----------|----------|---------|-----------------|-------------------|---------------|
| TC-01 | log-generator | `warn` | `/tmp/stars-trigger warn <RUN_ID>` | `Scenario started`, 1 WARN `On-demand warning; synthetic degraded condition`, `Scenario completed` | Container stays up; no restart | Within 5s: exactly 1 line with `level=WARN scenario=warn run_id=<RUN_ID>`; 0 ERROR lines for that run_id; started and completed lines present, in order; restart count unchanged |
| TC-02 | log-generator | `error` | `/tmp/stars-trigger error <RUN_ID>` | `Scenario started`, 1 ERROR `On-demand error; synthetic application failure`, `Scenario completed` | Container stays up; no restart | Within 5s: exactly 1 line with `level=ERROR scenario=error run_id=<RUN_ID>`; started and completed lines present, in order; restart count unchanged |
| TC-03 | log-generator | `error-spike` | `/tmp/stars-trigger error-spike <RUN_ID>` | `Scenario started`, 20 ERROR lines `Injected application error N of 20`, `Scenario completed` | Burst in one second; container stays up; no restart | Within 5s: exactly 20 lines with `level=ERROR scenario=error-spike run_id=<RUN_ID>`; N = 1..20 each once, in order; all within a 2s span; completed line present; restart count unchanged |
| TC-04 | log-generator | `connectivity` | `/tmp/stars-trigger connectivity <RUN_ID>` | `Scenario started`, 1 ERROR `Controlled connection failure target=127.0.0.1:1 wget_exit=1`, `Scenario completed` | Container stays up; no restart; no external traffic | Within 10s: exactly 1 ERROR line for the run_id containing `target=127.0.0.1:1` and `wget_exit=1`; 0 lines containing `Unexpected HTTP success`; completed line present; restart count unchanged |
| TC-05 | log-generator | `crash` | `/tmp/stars-trigger crash <RUN_ID>` | `Scenario started`, 1 ERROR `Injected container crash; exiting with code 42`, no `Scenario completed` | Exits with code 42, then restarts automatically | Within 60s: ERROR line present; no `Scenario completed` for the run_id; `lastState.terminated.exitCode` = 42; restart count up by exactly 1; pod back to `1/1 Running`; new `event=startup` and `event=ready` lines with a new startup run_id (pre-merge generator: `STARS generator started`); heartbeat `count` restarts low; scenario does not re-run |
| TC-06 | trace-generator | `normal` | `run.sh normal <RUN_ID> 60` (Mac) or PowerShell block | Job log `Run started` and `Run completed traces=N failed_traces=M`; traces with 7 spans across 4 services | Job completes by itself; mostly healthy | Within 180s: job `complete`; both lines present for the run_id; N between 100 and 130; M / N at most 0.05; every trace for the run_id has 7 spans across `frontend`, `api`, `db`, `payment` |
| TC-07 | trace-generator | `slow-db` | `run.sh slow-db <RUN_ID> 60` (Mac) or PowerShell block | As above; `db` spans about 800 ms longer; no injected errors | Job completes by itself; slower, fewer traces | Within 180s: job `complete`; M / N at most 0.05 (the 1% base failure rate still applies); N below 90; `db` spans at least 800 ms; each trace has 7 spans (observed: 67 traces, 1 failed, `db SELECT orders` 837 to 838 ms) |
| TC-08 | trace-generator | `payment-errors` | `run.sh payment-errors <RUN_ID> 60` (Mac) or PowerShell block | As above; mostly failed traces, error at `payment`, visible on `api` and `frontend` | Job completes by itself; most traces red | Within 180s: job `complete`; M / N between 0.55 and 0.85; in a failed trace 4 spans are in error: `payment POST /charge`, `api POST payment/charge`, `api POST /checkout` and `frontend GET /checkout` (observed: 88 of 120 failed, 73.3%) |
| TC-09 | synthetic-metrics | CPU spike | `kubectl set env deployment/synthetic-metrics -n stars RUN_ID=<RUN_ID> ANOMALIES=on` | `CPU spike started` (WARN), about 12 lines with `cpu_percent` around 80, `CPU spike ended` (INFO) | Pod stays Ready; repeats every 5 min | Within 6 min of pod start: exactly 1 start and 1 end line; 11 to 13 metrics lines between them with `cpu_percent` above 65; lines outside the spike below 65; `memory_percent` below 65 throughout; restart count unchanged |
| TC-10 | synthetic-metrics | Memory leak | same as TC-09 (one run covers both) | `Memory leak started` (WARN) at about minute 35, rising `memory_percent`, `Memory leak ended` (INFO) at about minute 50 | Pod stays Ready; repeats hourly | Within 55 min of pod start: exactly 1 start and 1 end line, 13 to 17 minutes apart; `memory_percent` climbs about 2 points per minute (about 55 at the start, 66 at 5 min, 73 at 9 min, 80 at 12 min); value after the end line below 65; restart count unchanged |
| TC-11 | log-generator (automatic) | Automatic error spike | `kubectl -n stars set env deployment/log-generator AUTO_SPIKE=true` | A spike every 20 s: 20 ERROR lines with `spike=true run_id=auto-<UTC>-<n>` and `error_index` 1..20; `scenario` cycles authentication, database, connectivity, dependency, service | Spikes repeat by themselves, the first at startup; container stays up | Within 60s of startup: at least 2 complete spikes; each `run_id` has exactly 20 lines, all `level=ERROR spike=true`, with `error_index` 1 to 20 and no gaps or repeats and the scenario for its position in the 5-type cycle (index 1 is `authentication` with the `invalid_token` message); `n` rises by 1 per spike; consecutive spikes start 18 to 22 s apart; the same lines come back from the OpenObserve query (observed: 900 events in 15 minutes); with `AUTO_SPIKE=false`, 0 `spike=true` lines over two intervals (observed: 0); restart count unchanged (observed: 0) |
| TC-12 | Locust | `normal` | `kubectl apply -f apps/Locust/jobs/normal.yaml` | `test_start` (users 20) and `test_stop`; stats table | About 5 minutes, completes, no errors | Within 420s: job `complete`; 1 `test_start` and 1 `test_stop` with the same `run_id`, `scenario` = `normal`; `users` = 20; `failures` = 0; `duration_s` 290 to 330; `requests` 2000 to 3200; 0 failures in the Job's stats table |
| TC-13 | Locust | `high-traffic` | `kubectl apply -f apps/Locust/jobs/high-traffic.yaml` | `test_start` (users 200) and `test_stop`; stats table | About 5 minutes, completes; heavy load | Within 420s: job `complete`; matching start and stop for one `run_id`, `scenario` = `high-traffic`; `users` = 200; `requests` at least 10 times a `normal` run; failure rate below 1% |
| TC-14 | Locust | `failing` | `kubectl apply -f apps/Locust/jobs/failing.yaml` | `test_start` (users 20) and `test_stop`; stats with 500, 404 and timeout rows | Job completes (not failed) despite errors | Within 420s: job `complete`, not `Failed`; matching start and stop, `scenario` = `failing`; `failures` at least 95% of `requests`; the Job's error report lists the 404, 500 and `ReadTimeout` errors |
| TC-15 | Locust | `mixed` | `kubectl apply -f apps/Locust/jobs/mixed.yaml` | `test_start` (users 50) and `test_stop`; successes and failures | Job completes (not failed) | Within 420s: job `complete`; matching start and stop, `scenario` = `mixed`; `users` = 50; 0 < `failures` < `requests`; the Job's error report lists the 404, 500 and `ReadTimeout` errors alongside successful `homepage` and `list_items` requests |
| TC-16 | Readiness | Starts and becomes Ready in time | `kubectl -n stars rollout restart deployment/<APP>` | One `event=startup` and one `event=ready` line, same `run_id` | New pod Ready; no restarts | Within 60s: `1/1 Running`; startup timestamp at or before ready; Ready time at or after the ready timestamp (1s tolerance); restart count 0 |
| TC-17 | Readiness | Not Ready on purpose, then recovers | Keep `/tmp/ready` stale with a 70-second loop (see scenario 17) | Pod goes `0/1`, then `1/1`; metrics lines keep coming every 5 s; `Readiness probe failed` events | Leaves service without restarting, recovers by itself | Within 60s: Ready condition `False`, `0/1` (observed at 50s); restart count unchanged (observed: 0); log still shows a new line every 5s; `describe` lists `Readiness probe failed`; within 30s of the loop ending: Ready `True`, `1/1`, no manual restart (observed within 20s) |


---

# Notes

- **Crash:** pod status stays `Running`; check the restart count and exit code, not status alone. A new startup `run_id` or a heartbeat `count` drop also marks a restart.
- **Triggers are asynchronous:** `kubectl exec` returns once the request is queued; wait about 1 second. Several queued scenarios run one per second and **not in the order queued** (the order differed between runs on Oct 28 and 29).
- **Heartbeat interval is about 5 seconds**, not exact. Log timestamps are UTC; `kubectl describe` shows local time.
- **trace-generator:** a run ID cannot be reused (use a new one or `kubectl -n stars delete job trace-generator-<RUN_ID>`); `_` becomes `-` in the Job name; the Job downloads packages at start, so allow extra time.
- **synthetic-metrics:** any pod restart (including `kubectl set env`) resets the schedule to minute 0, so record the start time. `ANOMALIES=off` removes the spikes and the leak (baseline) and has no test case here. A scheduled CPU spike can overlap other tests, so do not read a high `cpu_percent` as a test effect.
- **Automatic spikes:** leave `AUTO_SPIKE=false` when you are not testing it, or it keeps logging 20 error lines every 20 seconds. `awk '{print $6}'` finds the `run_id` only while the field order stays timestamp, level, service, scenario, spike, `run_id`.
- **Locust:** each test takes about 5 minutes (over 20 minutes for all four). `high-traffic` can overload minikube (the Locust README suggests `minikube start --cpus=4 --memory=8g`). On Oct 28 it ran fine.
- **Not Ready must not mean restarted:** a rising restart count points to a startup or liveness failure, not the readiness probe under test.
- **Laptop sleep distorts long runs:** keep the computer awake for long tests, and use only uninterrupted cycles as evidence.
- **Picking the right pod:** while a pod is being replaced, `items[0]` can be the old terminating pod. Sort by `.metadata.creationTimestamp` and take the last item.
- **A probe that errors is not a failure:** if the readiness command cannot start (for example `python` is missing), Kubernetes records "unknown state" and the pod stays Ready. To test Not Ready, make the probe run and return a non-zero exit code, as `touch -d @0` does here.