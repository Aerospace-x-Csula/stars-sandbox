"""TC-06 to TC-08: trace-generator scenarios (normal, slow-db, payment-errors).

The three 60-second Jobs start together, so the whole file takes about 2-3 minutes.
Job-log checks always run; span checks need the OpenObserve login (see README).
"""

import re
import time
import uuid
from collections import defaultdict

import pytest

from helpers import APPS_DIR, O2_STREAM, kubectl, needs_openobserve, o2_wait

TRACE_DIR = APPS_DIR / "trace-generator"
DURATION_S = 60
SCENARIOS = ["normal", "slow-db", "payment-errors"]
COMPLETED = re.compile(r"Run completed traces=(\d+) failed_traces=(\d+)")


def job_name(run_id):
    # Same rule as run.sh: lowercase, '_' -> '-', at most 40 characters of run ID.
    return "trace-generator-" + run_id.lower().replace("_", "-")[:40]


def start_job(scenario, run_id):
    job = (TRACE_DIR / "job.yaml").read_text()
    for placeholder, value in {"__JOB_NAME__": job_name(run_id), "__SCENARIO__": scenario,
                               "__RUN_ID__": run_id, "__DURATION__": str(DURATION_S)}.items():
        job = job.replace(placeholder, value)
    kubectl("create", "-f", "-", stdin=job)


@pytest.fixture(scope="module")
def runs():
    """Start one Job per scenario, wait for all of them, and return their results."""
    configmap = kubectl("create", "configmap", "trace-generator",
                        f"--from-file={TRACE_DIR / 'generator.py'}",
                        f"--from-file={TRACE_DIR / 'requirements.txt'}",
                        "--dry-run=client", "-o", "yaml").stdout
    kubectl("apply", "-f", "-", stdin=configmap)

    results = {}
    for scenario in SCENARIOS:
        run_id = f"tc-{scenario}-{uuid.uuid4().hex[:6]}"
        start_job(scenario, run_id)
        results[scenario] = {"run_id": run_id, "started": time.monotonic()}

    try:
        for scenario, run in results.items():
            name = job_name(run["run_id"])
            # Catalog: the Job completes within 180 s.
            done = kubectl("wait", "--for=condition=complete", f"job/{name}", "--timeout=180s",
                           timeout=200, check=False)
            run["complete"] = done.returncode == 0
            run["log"] = kubectl("logs", f"job/{name}", check=False).stdout
            match = COMPLETED.search(run["log"])
            run["traces"], run["failed"] = (int(match[1]), int(match[2])) if match else (None, None)
        yield results
    finally:
        for run in results.values():
            kubectl("delete", "job", job_name(run["run_id"]), "--wait=false", check=False)


def check_job(run):
    assert run["complete"], f"Job did not complete within 180 s. Log:\n{run['log'][-2000:]}"
    assert f"run_id={run['run_id']}" in run["log"] and "Run started" in run["log"], "No 'Run started' line"
    assert run["traces"] is not None, "No 'Run completed traces=N failed_traces=M' line"
    return run["traces"], run["failed"]


# ---------------------------------------------------------------- job-log checks

def test_tc06_normal_job(runs):
    traces, failed = check_job(runs["normal"])
    assert 100 <= traces <= 130, f"Expected 100-130 traces, got {traces}"
    assert failed / traces <= 0.05, f"Failure rate {failed}/{traces} is above 5%"


def test_tc07_slow_db_job(runs):
    traces, failed = check_job(runs["slow-db"])
    assert traces < 90, f"Expected fewer than 90 traces (slower requests), got {traces}"
    assert failed / traces <= 0.05, f"Failure rate {failed}/{traces} is above 5%"


def test_tc08_payment_errors_job(runs):
    traces, failed = check_job(runs["payment-errors"])
    assert 0.55 <= failed / traces <= 0.85, f"Failure rate {failed}/{traces} is outside 55-85%"


# ---------------------------------------------------------------- span checks in OpenObserve

def spans_per_trace(run):
    """Rows of (trace_id, span count, service count) for a run, once all traces have arrived."""
    sql = (f'SELECT trace_id, count(*) AS spans, count(DISTINCT service_name) AS services '
           f'FROM "{O2_STREAM}" WHERE run_id = \'{run["run_id"]}\' GROUP BY trace_id')
    return o2_wait(sql, expected=run["traces"], stream_type="traces", timeout=120)


@needs_openobserve
@pytest.mark.parametrize("scenario", ["normal", "slow-db"])
def test_tc06_tc07_every_trace_has_7_spans_across_4_services(runs, scenario):
    run = runs[scenario]
    check_job(run)
    rows = spans_per_trace(run)
    assert len(rows) == run["traces"], f"Job made {run['traces']} traces, OpenObserve has {len(rows)}"
    bad = [r for r in rows if r["spans"] != 7 or r["services"] != 4]
    assert not bad, f"{len(bad)} traces do not have 7 spans across 4 services, e.g. {bad[:3]}"


@needs_openobserve
def test_tc07_db_spans_at_least_800ms(runs):
    run = runs["slow-db"]
    check_job(run)
    sql = (f'SELECT trace_id, duration FROM "{O2_STREAM}" '
           f"WHERE run_id = '{run['run_id']}' AND operation_name = 'SELECT orders'")
    rows = o2_wait(sql, expected=run["traces"], stream_type="traces", timeout=120)
    assert len(rows) == run["traces"], f"Expected one db span per trace, found {len(rows)}"
    # OpenObserve stores span duration in microseconds.
    short = [r["duration"] / 1000 for r in rows if r["duration"] / 1000 < 800]
    assert not short, (f"{len(short)} db spans are under 800 ms, e.g. {short[:3]} ms "
                       "(if every value looks 1000x off, the duration unit differs)")


@needs_openobserve
def test_tc08_failed_traces_have_4_error_spans(runs):
    run = runs["payment-errors"]
    check_job(run)
    sql = (f'SELECT trace_id, service_name, operation_name FROM "{O2_STREAM}" '
           f"WHERE run_id = '{run['run_id']}' AND span_status = 'ERROR'")
    rows = o2_wait(sql, expected=run["failed"] * 4, stream_type="traces", timeout=120)

    error_spans = defaultdict(set)
    for row in rows:
        error_spans[row["trace_id"]].add(f"{row['service_name']} {row['operation_name']}")

    expected = {"payment POST /charge", "api POST payment/charge", "api POST /checkout", "frontend GET /checkout"}
    assert len(error_spans) == run["failed"], f"Job failed {run['failed']} traces, OpenObserve shows {len(error_spans)}"
    wrong = {t: s for t, s in error_spans.items() if s != expected}
    assert not wrong, f"{len(wrong)} failed traces have different error spans, e.g. {list(wrong.values())[:2]}"
