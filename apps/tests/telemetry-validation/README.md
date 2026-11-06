# STARS — Automated Telemetry Validation

## Overview

This project uses Python and pytest to automatically test the STARS telemetry generators (log-generator, synthetic-metrics and trace-generator) running in a local Kubernetes environment, and to confirm their data reaches OpenObserve.

The tests cover all 17 test cases in the [failure catalog](../../failure-scenarios/README.md) (TC-01 to TC-17), plus three checks that data reaches OpenObserve.

| File | What it proves | Catalog | Time |
|---|---|---|---|
| `test_logs.py` | The log-generator prints the right lines and recovers from a crash | TC-01 to TC-05 | ~1 min |
| `test_openobserve.py` | Logs, metrics and traces actually **reach OpenObserve** and can be searched | (pipeline checks) | ~1 min |
| `test_traces.py` | The three trace scenarios produce the right traces and spans | TC-06 to TC-08 | ~3 min |
| `test_auto_spike.py` | Automatic error spikes turn on, look right, and turn off | TC-11 | ~3 min |
| `test_readiness.py` | Apps log startup/ready and become Ready in time; a Not Ready pod recovers without restarting | TC-16, TC-17 | ~3 min |
| `test_metrics.py` | The CPU spike and the memory leak happen on schedule | TC-09 (**slow**), TC-10 (**very slow**) | ~6 min / ~52 min |
| `test_locust.py` | The four Locust scenarios run for 5 minutes with the expected results | TC-12 to TC-15 (**slow**) | ~22 min |

`helpers.py` holds code the test files share (kubectl, log parsing, OpenObserve search). `pytest.ini` defines the `slow` and `very_slow` labels.

## Prerequisites

- Python 3.10 or newer
- Minikube
- kubectl
- A running STARS log-generator deployment in the `stars` namespace
- The `synthetic-metrics` deployment running
- OpenObserve and its collector installed, and internet access for the cluster (the trace tests start trace-generator Jobs that download packages)
- For `test_locust.py`: `stars-app` deployed ([`apps/locust/README.md`](../../locust/README.md), step 1). The test loads the current `locustfile.py` into the cluster itself
- **Use your cluster alone while testing.** Several tests restart `log-generator` and `synthetic-metrics`, and turn automatic spikes on and off

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

Set the OpenObserve login first (see "OpenObserve tests"), or the OpenObserve checks are skipped. Then pick how much to run:

| Run | Command | Time |
|---|---|---|
| **Everyday** (everything except the long tests) | `python -m pytest -v -m "not slow and not very_slow"` | ~10 min |
| **Before a pull request** (adds the CPU spike and Locust) | `python -m pytest -v -m "not very_slow" --junitxml=test-results.xml` | ~40 min |
| **Full** (adds the 1-hour memory leak; keep the laptop awake) | `python -m pytest -v --junitxml=test-results.xml` | ~1.5 hours |

`test-results.xml` is the team's test evidence: it lists every test and whether it passed. Each run replaces it, so save it from a "before a pull request" or "full" run, then commit the file.

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
| `test_tc06_normal_job`, `test_tc07_slow_db_job`, `test_tc08_payment_errors_job` | Each 60-second trace Job completes with the right number of traces and failure rate |
| `test_tc06_tc07_every_trace_has_7_spans_across_4_services` | Every `normal` and `slow-db` trace in OpenObserve has 7 spans across 4 services |
| `test_tc07_db_spans_at_least_800ms` | In `slow-db`, every `db SELECT orders` span takes at least 800 ms |
| `test_tc08_failed_traces_have_4_error_spans` | In `payment-errors`, each failed trace has exactly the 4 expected error spans |
| `test_tc09_cpu_spike` | The first CPU spike starts at minute 4, lasts 11-13 readings above 65%, and memory stays normal |
| `test_tc10_memory_leak` | The leak lasts 13-17 minutes, memory climbs about 2 points per minute, then drops back |
| `test_tc11_spikes_are_complete_and_ordered` | Each automatic spike has 20 ERROR lines, `error_index` 1-20, the right type cycle and a rising number |
| `test_tc11_spike_timing` | The first spike comes at startup and the rest every 18-22 s, with no restarts |
| `test_tc11_spikes_reach_openobserve` | A spike's 20 lines are searchable in OpenObserve |
| `test_tc11_no_spikes_when_off` | With `AUTO_SPIKE=false`, no spike lines appear for two intervals |
| `test_tc12_normal` to `test_tc15_mixed` | Each Locust Job completes with matching start/stop lines, the right user count and the expected failures |
| `test_tc16_starts_and_becomes_ready` | `log-generator` and `synthetic-metrics` log startup and ready, then become Ready within 60 s without restarting |
| `test_tc17_not_ready_on_purpose_then_recovers` | `synthetic-metrics` goes Not Ready when its ready file is stale, keeps running, and recovers by itself |

## Expected Results

With the OpenObserve login set:

| Run | Expected |
|---|---|
| Everyday | `22 passed, 6 deselected` |
| Before a pull request | `27 passed, 1 deselected` |
| Full | `28 passed` |

Without the login, the 8 tests that search OpenObserve are skipped (for example, everyday: `14 passed, 8 skipped, 6 deselected`).

If a test changes a deployment's settings (`AUTO_SPIKE`, or `RUN_ID`/`ANOMALIES` on synthetic-metrics), it puts the defaults back when it finishes.

Each execution uses a unique test identifier to distinguish its logs from previous runs.

## Limitations

- The tests run against a shared cluster state, so don't run two test sessions at once, and don't use the cluster for anything else while they run.
- `test_tc10_memory_leak` needs the laptop awake for about an hour; sleep stretches the schedule and fails the test.
- `test_tc07_db_spans_at_least_800ms` assumes OpenObserve stores span durations in microseconds. If every value in a failure message looks 1000 times off, that assumption needs changing.
- Tests require access to a running local Minikube environment.
- The crash test intentionally restarts the log-generator container. Avoid running it while another teammate is using the same deployment.
- Tests assume the existing single-replica log-generator deployment.

## Future Improvements

- Expand regression testing as new failure scenarios are introduced.
- Save structured test reports for project evaluation.

## Project Alignment

**STARS Project Outline — Data/Test Engineering**

Supports regression testing, failure-injection validation, reproducibility, and evidence collection.
