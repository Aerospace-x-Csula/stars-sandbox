"""TC-12 to TC-15: Locust headless Jobs (normal, high-traffic, failing, mixed).

Each Job runs for 5 minutes, one after another (about 22 minutes in total), so
these are marked slow. Needs stars-app deployed (apps/locust/README.md, step 1).
"""

import json
import time

import pytest

from helpers import APPS_DIR, kubectl, kubectl_json

pytestmark = pytest.mark.slow

LOCUST_DIR = APPS_DIR / "locust"
results = {}  # scenario -> parsed run, so TC-13 can compare against TC-12


@pytest.fixture(scope="module", autouse=True)
def setup_locust():
    deploy = kubectl_json("get", "deployment", "stars-app")
    if not deploy["status"].get("readyReplicas"):
        pytest.skip("stars-app is not running: follow apps/locust/README.md step 1 first")
    # Load the current locustfile into the cluster so the Jobs run the repo's version.
    configmap = kubectl("create", "configmap", "locustfile",
                        f"--from-file={LOCUST_DIR / 'locustfile.py'}",
                        "--dry-run=client", "-o", "yaml").stdout
    kubectl("apply", "-f", "-", stdin=configmap)


def run_job(scenario):
    """Run one Locust Job and return its test_start / test_stop events and full log."""
    job = f"locust-{scenario}"
    kubectl("delete", "job", job, "--ignore-not-found", "--wait=true", timeout=120)
    kubectl("apply", "-f", str(LOCUST_DIR / "jobs" / f"{scenario}.yaml"))

    # Catalog: within 420 s the Job is Complete (and never Failed).
    deadline = time.monotonic() + 420
    while True:
        status = kubectl_json("get", "job", job)["status"]
        if status.get("succeeded"):
            break
        assert not status.get("failed"), f"Job {job} failed:\n{kubectl('logs', f'job/{job}', check=False).stdout[-3000:]}"
        assert time.monotonic() < deadline, f"Job {job} did not complete within 420 s"
        time.sleep(10)

    log = kubectl("logs", f"job/{job}", timeout=60).stdout
    events = [json.loads(line.split("loadtest ", 1)[1]) for line in log.splitlines() if "loadtest {" in line]
    starts = [e for e in events if e["event"] == "test_start"]
    stops = [e for e in events if e["event"] == "test_stop"]
    assert len(starts) == 1 and len(stops) == 1, f"Expected 1 test_start and 1 test_stop, got {len(starts)} and {len(stops)}"
    start, stop = starts[0], stops[0]
    assert start["run_id"] == stop["run_id"], "test_start and test_stop have different run_ids"
    assert start["scenario"] == stop["scenario"] == scenario, f"scenario should be {scenario}"
    assert 290 <= stop["duration_s"] <= 330, f"Run lasted {stop['duration_s']} s; expected about 300"
    kubectl("delete", "job", job, "--ignore-not-found", "--wait=false", check=False)

    run = {"start": start, "stop": stop, "log": log}
    results[scenario] = run
    return run


def test_tc12_normal():
    run = run_job("normal")
    assert run["start"]["users"] == 20
    assert run["stop"]["failures"] == 0, f"Expected no failures, got {run['stop']['failures']}"
    assert 2000 <= run["stop"]["requests"] <= 3200, f"Expected 2000-3200 requests, got {run['stop']['requests']}"


def test_tc13_high_traffic():
    run = run_job("high-traffic")
    stop = run["stop"]
    assert run["start"]["users"] == 200
    normal = results.get("normal", {}).get("stop", {}).get("requests", 2000)
    assert stop["requests"] >= 10 * normal, f"{stop['requests']} requests is less than 10x normal ({normal})"
    assert stop["failures"] / stop["requests"] < 0.01, f"Failure rate {stop['failures']}/{stop['requests']} is 1% or more"


def test_tc14_failing():
    run = run_job("failing")
    stop = run["stop"]
    assert run["start"]["users"] == 20
    assert stop["failures"] >= 0.95 * stop["requests"], f"Only {stop['failures']} of {stop['requests']} requests failed"
    for error in ("404", "500", "ReadTimeout"):
        assert error in run["log"], f"The Job's error report does not mention {error}"


def test_tc15_mixed():
    run = run_job("mixed")
    stop = run["stop"]
    assert run["start"]["users"] == 50
    assert 0 < stop["failures"] < stop["requests"], f"Expected some failures and some successes, got {stop['failures']} of {stop['requests']}"
    for text in ("404", "500", "ReadTimeout", "homepage", "list_items"):
        assert text in run["log"], f"The Job's output does not mention {text}"
