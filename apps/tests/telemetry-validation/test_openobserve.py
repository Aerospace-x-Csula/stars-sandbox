"""End-to-end checks: telemetry from our generators actually reaches OpenObserve.

test_logs.py proves the apps print the right lines (kubectl logs).
These tests prove the whole path works: app -> collector -> OpenObserve -> searchable.

Before running (see README.md, "OpenObserve tests"):
  - kubectl port-forward -n stars svc/openobserve-openobserve-standalone 5080:5080
  - O2_USER and O2_PASSWORD set to your OpenObserve login (from values.local.yaml)
  - log-generator and synthetic-metrics running in the stars namespace

Never put the password in this file.
"""

import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest
import requests

O2_URL = os.getenv("O2_URL", "http://localhost:5080").rstrip("/")
O2_ORG = os.getenv("O2_ORG", "default")
O2_STREAM = os.getenv("O2_STREAM", "default")          # logs and traces both land in "default"
AUTH = (os.getenv("O2_USER", ""), os.getenv("O2_PASSWORD", ""))

TRACE_DIR = Path(__file__).resolve().parents[2] / "trace-generator"

pytestmark = pytest.mark.skipif(
    not all(AUTH), reason="Set O2_USER and O2_PASSWORD to run the OpenObserve tests"
)


# ---------------------------------------------------------------- helpers

def search(sql, stream_type="logs", minutes=15):
    """Run one SQL search against OpenObserve and return the matching rows."""
    now = int(time.time() * 1_000_000)  # OpenObserve uses microseconds
    body = {
        "query": {
            "sql": sql,
            "start_time": now - minutes * 60 * 1_000_000,
            "end_time": now,
            "from": 0,
            "size": 500,
        }
    }
    response = requests.post(
        f"{O2_URL}/api/{O2_ORG}/_search",
        params={"type": stream_type},
        json=body,
        auth=AUTH,
        timeout=20,
    )
    assert response.status_code != 401, "OpenObserve rejected the login: check O2_USER and O2_PASSWORD"
    response.raise_for_status()
    return response.json().get("hits", [])


def wait_for(sql, stream_type="logs", expected=1, timeout=90, minutes=15):
    """Search every 5 seconds until at least `expected` rows appear or `timeout` passes.

    The collector sends data in batches, so new data can take a little while to show up.
    """
    deadline = time.monotonic() + timeout
    hits = []
    while time.monotonic() < deadline:
        hits = search(sql, stream_type, minutes)
        if len(hits) >= expected:
            return hits
        time.sleep(5)
    return hits


def kubectl(*args, stdin=None, timeout=30):
    return subprocess.run(
        ["kubectl", *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=True,
        timeout=timeout,
    )


def start_trace_run(run_id, scenario="normal", duration=20):
    """Start one trace-generator Job. Does what run.sh does, in Python, so it works on Windows too."""
    # 1. Load the generator code into the cluster (create or update the ConfigMap)
    configmap = kubectl(
        "-n", "stars", "create", "configmap", "trace-generator",
        f"--from-file={TRACE_DIR / 'generator.py'}",
        f"--from-file={TRACE_DIR / 'requirements.txt'}",
        "--dry-run=client", "-o", "yaml",
    )
    kubectl("apply", "-f", "-", stdin=configmap.stdout)

    # 2. Fill in the Job template
    job_name = f"trace-generator-{run_id}"
    job = (TRACE_DIR / "job.yaml").read_text()
    for placeholder, value in {
        "__JOB_NAME__": job_name,
        "__SCENARIO__": scenario,
        "__RUN_ID__": run_id,
        "__DURATION__": str(duration),
    }.items():
        job = job.replace(placeholder, value)

    # 3. Start the Job
    kubectl("create", "-f", "-", stdin=job)
    return job_name


# ---------------------------------------------------------------- setup check

@pytest.fixture(scope="module", autouse=True)
def openobserve_reachable():
    try:
        search('SELECT _timestamp FROM "%s"' % O2_STREAM, minutes=1)
    except requests.ConnectionError:
        pytest.fail(
            f"Cannot reach OpenObserve at {O2_URL}. Start the port-forward:\n"
            "  kubectl port-forward -n stars svc/openobserve-openobserve-standalone 5080:5080",
            pytrace=False,
        )


# ---------------------------------------------------------------- tests

def test_logs_reach_openobserve():
    """Trigger one known ERROR in log-generator and find exactly that line in OpenObserve.

    The search is limited to the log-generator container: OpenObserve logs its own search
    queries into the same stream, and those contain the run_id text too.
    """
    run_id = f"o2-{uuid.uuid4().hex[:8]}"
    kubectl("exec", "-n", "stars", "deployment/log-generator", "--",
            "/tmp/stars-trigger", "error", run_id, timeout=15)

    hits = wait_for(
        f"""SELECT body FROM "{O2_STREAM}"
            WHERE k8s_container_name = 'log-generator'
              AND body LIKE '%run_id={run_id} %' AND body LIKE '%level=ERROR%'"""
    )

    assert len(hits) == 1, f"Expected 1 ERROR line for run_id={run_id} in OpenObserve, found {len(hits)}"


def test_metrics_reach_openobserve():
    """synthetic-metrics prints a line every 5 s, so the last 2 minutes should hold ~24 lines."""
    hits = wait_for(
        f"""SELECT body FROM "{O2_STREAM}"
            WHERE k8s_container_name = 'synthetic-metrics' AND body LIKE '%cpu_percent=%'""",
        expected=10,
        timeout=60,
        minutes=2,
    )

    assert len(hits) >= 10, (
        f"Only {len(hits)} metric lines in the last 2 minutes (expected about 24). "
        "Is synthetic-metrics running? kubectl get pods -n stars -l app=synthetic-metrics"
    )
    assert all("memory_percent=" in hit.get("body", "") for hit in hits), "Metric lines are missing memory_percent"


def test_traces_reach_openobserve():
    """Run a 20-second trace-generator Job and find its spans in the traces stream."""
    run_id = f"o2-{uuid.uuid4().hex[:8]}"
    job_name = start_trace_run(run_id, duration=20)
    try:
        # The Job installs its Python packages first, so allow up to 4 minutes.
        # ~2 traces per second x 7 spans per trace -> one full trace is 7 spans.
        hits = wait_for(
            f"""SELECT trace_id, service_name FROM "{O2_STREAM}" WHERE run_id = '{run_id}'""",
            stream_type="traces",
            expected=7,
            timeout=240,
        )

        assert len(hits) >= 7, (
            f"Expected at least 7 spans for run_id={run_id}, found {len(hits)}. "
            f"Check the Job: kubectl -n stars logs job/{job_name}"
        )
        services = {hit.get("service_name") for hit in hits}
        assert {"frontend", "api", "db", "payment"} <= services, f"Missing services, found: {services}"
    finally:
        subprocess.run(
            ["kubectl", "-n", "stars", "delete", "job", job_name, "--wait=false"],
            capture_output=True,
        )
