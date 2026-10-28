# Trace Generator

Creates fake (synthetic) OpenTelemetry traces so the team can test distributed tracing in OpenObserve. One request becomes one trace that passes through four pretend services:

```text
frontend -> api -> db
              `--> payment
```

```text
trace-generator Job  --->  OpenObserve collector  --->  OpenObserve (Traces page)
   (runs for a set time)    (openobserve-collector)         (stars)
```

Every span is tagged with a `run_id` and a `scenario`, so you can find the traces from one run. Everything here is simulated: the services and database do not exist.

All commands run from the **root of the repository**.

**On Windows?** `run.sh` is a shell script and does not run in PowerShell. Use the [Windows](#windows) section for Step 1; Steps 2 and 3 are the same.

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

The cluster also needs internet access, because the Job downloads the OpenTelemetry packages when it starts.

---

## Step 1: Start a run

```bash
chmod +x apps/trace-generator/run.sh
apps/trace-generator/run.sh normal trace01 60
```

The three values are: the **scenario** (`normal`), a **run ID** you choose (`trace01`), and how long to run in **seconds** (`60`, default 300).

You should see `job.batch/trace-generator-trace01 created`.

Use a **new run ID every time** (`trace02`, `trace03`, ...). A run ID may use letters, digits, `_` and `-`, up to 64 characters.

## Step 2: Watch it run

```bash
kubectl -n stars logs -f job/trace-generator-trace01
```

After a few seconds you should see:

```text
... level=INFO service=trace-generator scenario=normal run_id=trace01 message="Run started ..."
... level=INFO service=trace-generator scenario=normal run_id=trace01 message="Run completed traces=118 failed_traces=1"
```

- `Run started` and `Run completed` are the exact start and end times (in UTC) to record for the run.
- About 2 traces are made per second. A few failures are normal: the `normal` scenario has a 1% random failure rate.
- Press Ctrl+C to stop following the log. The run continues.
- If you see `Exception while exporting` or `Failed to resolve`, go to [Troubleshooting](#troubleshooting).

## Step 3: See the traces in OpenObserve

1. In a second terminal, start the port-forward and leave it running:
   ```bash
   kubectl --namespace stars port-forward svc/openobserve-openobserve-standalone 5080:5080
   ```
2. Open <http://localhost:5080> and log in with the email and password from your `observability/values.local.yaml`.
3. Click **Traces** in the left menu, set the time range to **Past 15 Minutes**, and click **Run query**.
4. To see only one run, type `run_id = 'trace01'` in the query box and run it again.
5. Click a trace. You should see **7 spans** across `frontend`, `api`, `db` and `payment`, nested like this:

```text
frontend  GET /checkout
  frontend  POST api/checkout
    api  POST /checkout
      api  db query
        db  SELECT orders
      api  POST payment/charge
        payment  POST /charge
```

The **Service Catalog** view (next to Traces) lists the four services.

---

## Windows

The `kubectl` commands in this README work the same in PowerShell. Only `run.sh` (Step 1) and the local test need Windows versions. Run everything from the **root of the repository**.

### Option A: Git Bash or WSL2 (easiest)

If you have Git for Windows, open **Git Bash** (or a WSL2 terminal) in the repository root and use Step 1 exactly as written:

```bash
apps/trace-generator/run.sh normal trace01 60
```

`kubectl` must work in that terminal. Check with `kubectl get pods -n stars`.

### Option B: PowerShell

These commands do the same thing as `run.sh`. Change the first three values for each run:

```powershell
$Scenario = "normal"      # normal | slow-db | payment-errors
$RunId    = "trace01"     # new run ID every time; letters, digits, _ and -
$Duration = 60            # seconds

$JobName = "trace-generator-" + $RunId.ToLower().Replace("_", "-")
kubectl -n stars create configmap trace-generator --from-file=apps/trace-generator/generator.py --from-file=apps/trace-generator/requirements.txt --dry-run=client -o yaml | kubectl apply -f -
(Get-Content apps/trace-generator/job.yaml -Raw) -replace "__JOB_NAME__", $JobName -replace "__SCENARIO__", $Scenario -replace "__RUN_ID__", $RunId -replace "__DURATION__", $Duration | kubectl create -f -
```

You should see `configmap/trace-generator configured` (or `created`) and `job.batch/trace-generator-trace01 created`. Then continue with [Step 2](#step-2-watch-it-run).

- Keep run IDs short (under 40 characters) so the Job name stays valid.
- `run.sh` checks the scenario and run ID for you; here a typo is not caught. A wrong scenario name makes the Job fail right away, so check the log in Step 2.
- To run again, change `$RunId` and paste the last three lines again.

### PowerShell versions of other commands

Collector log in [Troubleshooting](#troubleshooting) (`grep` does not exist in PowerShell):

```powershell
kubectl logs -n openobserve-collector o2c-openobserve-collector-gateway-collector-0 | Select-String -NotMatch "Failed to scrape" | Select-Object -Last 30
```

Local test without a cluster (from [Settings](#settings-optional)):

```powershell
python -m venv apps/trace-generator/.venv
apps/trace-generator/.venv/Scripts/Activate.ps1
pip install -r apps/trace-generator/requirements.txt
$env:DRY_RUN = "1"; $env:SCENARIO = "payment-errors"; $env:RUN_ID = "local01"; $env:DURATION_SECONDS = "5"
python apps/trace-generator/generator.py
```

- If `python` is not found, use `py` instead.
- If `Activate.ps1` is blocked ("running scripts is disabled"), run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

---

## Scenarios

The scenario is the first value after `run.sh` in Step 1. The pattern is:

```text
apps/trace-generator/run.sh   SCENARIO   RUN_ID   SECONDS
```

`SECONDS` is optional (default 300). Copy one of these, and use a new run ID each time:

```bash
apps/trace-generator/run.sh normal trace07 60
apps/trace-generator/run.sh slow-db trace08 60
apps/trace-generator/run.sh payment-errors trace09 60
```

| Scenario | What happens | What you will see |
|---|---|---|
| `normal` | Healthy traffic, about 1% random failures | Fast traces, almost all green |
| `slow-db` | The database is about 800 ms slower | Long `db` spans, with `api` and `frontend` slower too; no errors |
| `payment-errors` | About 70% of payment calls fail | Mostly red traces; the error starts at `payment` and shows up in `api` and `frontend` |

Slower scenarios make fewer traces per second, because requests run one at a time. That is expected.

---

## Remove

Stop a run early:

```bash
kubectl -n stars delete job trace-generator-trace01
```

Remove everything this component created:

```bash
kubectl -n stars delete job -l app=trace-generator
kubectl -n stars delete configmap trace-generator
```

Finished runs delete themselves after one hour.

---

## Troubleshooting

| What you see | What to do |
|---|---|
| `namespaces "stars" not found` | Create it: `kubectl create namespace stars` |
| `Job trace-generator-... already exists` (or `field is immutable`) | That run ID was already used. Use a new run ID, or delete the old Job: `kubectl -n stars delete job trace-generator-trace01` |
| Log shows `Failed to resolve ...` or `Exception while exporting` | The collector is not reachable. Run `kubectl get svc -n openobserve-collector` and check that `o2c-openobserve-collector-gateway-collector` exists with port 4318. If the name differs, change `OTEL_EXPORTER_OTLP_ENDPOINT` in `apps/trace-generator/job.yaml` |
| Log looks fine, but Traces is empty | Widen the time range, and check the collector log: `kubectl logs -n openobserve-collector o2c-openobserve-collector-gateway-collector-0 \| grep -v "Failed to scrape" \| tail -30` |
| Job stays `Pending` or the log is empty for a long time | `kubectl -n stars describe job/trace-generator-trace01`. Usually the cluster cannot download the image or packages |
| `Failed to scrape Prometheus endpoint` in the collector log | Harmless on Minikube; ignore it |

---

## Settings (optional)

Set these in `apps/trace-generator/job.yaml`:

| Variable | Default | Purpose |
|---|---|---|
| `RATE` | `2` | Target traces per second |
| `ERROR_RATE` | by scenario | Override the payment failure probability (0.0 to 1.0) |
| `EXTRA_DB_MS` | by scenario | Override extra database delay in milliseconds |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | the collector gateway, port 4318 | Where traces are sent |

To try it on your own computer without a cluster, print spans to the terminal:

```bash
python3 -m venv apps/trace-generator/.venv
source apps/trace-generator/.venv/bin/activate
pip install -r apps/trace-generator/requirements.txt
DRY_RUN=1 SCENARIO=payment-errors RUN_ID=local01 DURATION_SECONDS=5 python apps/trace-generator/generator.py
```

## Notes

- This is a separate generator from the log-generator and Locust on purpose, so each can run alone. Use the same run ID across them to match logs, traffic and traces.
- Each run is a Kubernetes Job that stops by itself and never repeats.
