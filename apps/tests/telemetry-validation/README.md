# STARS — Automated Telemetry Validation

## Overview

This project uses Python and pytest to automatically test the STARS telemetry generators (log-generator, synthetic-metrics and trace-generator) running in a local Kubernetes environment, and to confirm their data reaches OpenObserve.

There are two test files:

| File | What it proves |
|---|---|
| `test_logs.py` | The log-generator prints the right lines and recovers from a crash (checked with `kubectl logs`) |
| `test_openobserve.py` | Logs, metrics and traces actually **reach OpenObserve** and can be searched (app -> collector -> OpenObserve) |

## Prerequisites

- Python 3.10 or newer
- Minikube
- kubectl
- A running STARS log-generator deployment in the `stars` namespace
- For `test_openobserve.py` only: OpenObserve and its collector installed, the `synthetic-metrics` deployment running, and internet access for the cluster (the trace test starts a trace-generator Job that downloads packages)

All commands below work in macOS Terminal and Windows PowerShell unless a section shows both.

## Setup

Navigate to the testing directory:

```bash
cd apps/tests/telemetry-validation
```

Create a Python virtual environment:

```bash
python3 -m venv .venv      # macOS
python -m venv .venv       # Windows (use py if python is not found)
```

Activate the environment:

```bash
source .venv/bin/activate          # macOS
```

```powershell
.venv\Scripts\Activate.ps1          # Windows PowerShell
```

If Windows says "running scripts is disabled", run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Verify your Kubernetes environment:

```bash
kubectl config current-context
kubectl get pods -n stars
```

Ensure the `log-generator` pod is running before executing tests.

## Running the Tests

Run the entire test suite and save the results as test evidence:

```bash
python -m pytest -v --junitxml=test-results.xml
```

`test-results.xml` is the team's test evidence: it lists every test and whether it passed. Each run replaces it. Set the OpenObserve login first (see "OpenObserve tests") so all 8 tests run, then commit the file.

Run a single test:

```bash
python -m pytest test_logs.py::test_error_spike -v
```

The OpenObserve tests are **skipped** unless you set your login first (next section).

When you are done, leave the virtual environment (same on macOS and Windows):

```bash
deactivate
```

The `(.venv)` at the start of your prompt disappears. Next time, activate it again (Setup) before running tests; you do not need to reinstall.

## OpenObserve tests

These need a port-forward and your OpenObserve login. The login is read from environment variables, so it is never saved in the repo.

1. In a second terminal, start the port-forward and leave it running:

   ```bash
   kubectl port-forward -n stars svc/openobserve-openobserve-standalone 5080:5080
   ```

2. Set your login (the email and password from `observability/values.local.yaml`) in the terminal you run the tests from:

   ```bash
   export O2_USER="you@example.com"        # macOS
   export O2_PASSWORD="your-password"
   ```

   ```powershell
   $env:O2_USER = "you@example.com"        # Windows PowerShell
   $env:O2_PASSWORD = "your-password"
   ```

3. Run only the OpenObserve tests (for a quick check; use the full-suite command above for evidence):

   ```bash
   python -m pytest test_openobserve.py -v
   ```

They take about 3–5 minutes, mostly waiting for the trace-generator Job to install its packages and for the collector to deliver data.

Optional settings: `O2_URL` (default `http://localhost:5080`), `O2_ORG` (default `default`), `O2_STREAM` (default `default`).

| What you see | What to do |
|---|---|
| `Cannot reach OpenObserve` | The port-forward is not running. Start it (step 1) |
| `OpenObserve rejected the login` | Check `O2_USER` and `O2_PASSWORD` |
| `3 skipped` | `O2_USER` / `O2_PASSWORD` are not set in this terminal |
| Metrics test fails with few lines | Start the metrics generator: `apps/synthetic-metrics/README.md` |
| Traces test fails | Read the Job log the error message points to; see `apps/trace-generator/README.md` Troubleshooting |

## Test Scenarios

| Test | Expected Result |
|---|---|
| `test_warning` | Generates one warning log |
| `test_error` | Generates one application error log |
| `test_error_spike` | Generates 20 application error logs |
| `test_connectivity` | Generates one controlled connection failure log |
| `test_crash` | Terminates the container with exit code 42 and verifies Kubernetes recovery |
| `test_logs_reach_openobserve` | Triggers one ERROR with a unique `run_id` and finds exactly that line in OpenObserve |
| `test_metrics_reach_openobserve` | Finds at least 10 synthetic-metrics lines from the last 2 minutes in OpenObserve (one every 5 s) |
| `test_traces_reach_openobserve` | Runs a 20-second trace-generator Job and finds its spans from all 4 services in OpenObserve's traces |

## Expected Results

With the OpenObserve login set, all eight tests run:

```text
8 passed
```

Without it, the five `test_logs.py` tests run and the three OpenObserve tests are skipped (`5 passed, 3 skipped`).

Each execution uses a unique test identifier to distinguish its logs from previous runs.

## Limitations

- The log-generator's automatic error spikes (`AUTO_SPIKE=true`) and the Locust traffic generator are not tested yet.
- Tests require access to a running local Minikube environment.
- The crash test intentionally restarts the log-generator container. Avoid running it while another teammate is using the same deployment.
- Tests assume the existing single-replica log-generator deployment.

## Future Improvements

- Expand regression testing as new failure scenarios are introduced.
- Save structured test reports for project evaluation.

## Project Alignment

**STARS Project Outline — Data/Test Engineering**

Supports regression testing, failure-injection validation, reproducibility, and evidence collection.
