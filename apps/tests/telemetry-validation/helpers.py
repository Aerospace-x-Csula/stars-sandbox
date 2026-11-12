"""Shared helpers for the telemetry-validation tests.

Everything here runs from the laptop: kubectl talks to the cluster, and the
OpenObserve search API is reached through a port-forward (see README.md).
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

NAMESPACE = "stars"
TESTS_DIR = Path(__file__).resolve().parent
APPS_DIR = TESTS_DIR.parents[1]

O2_URL = os.getenv("O2_URL", "http://localhost:5080").rstrip("/")
O2_ORG = os.getenv("O2_ORG", "default")
O2_STREAM = os.getenv("O2_STREAM", "default")
O2_AUTH = (os.getenv("O2_USER", ""), os.getenv("O2_PASSWORD", ""))
HAVE_O2 = all(O2_AUTH)

needs_openobserve = pytest.mark.skipif(
    not HAVE_O2, reason="Set O2_USER and O2_PASSWORD to run the OpenObserve checks"
)

KV = re.compile(r'(\w+)=("[^"]*"|\S+)')


# ---------------------------------------------------------------- kubectl

def kubectl(*args, stdin=None, timeout=60, check=True):
    """Run kubectl in the stars namespace and return the completed process."""
    return subprocess.run(
        ["kubectl", "-n", NAMESPACE, *args],
        input=stdin, capture_output=True, text=True, check=check, timeout=timeout,
    )


def kubectl_json(*args, timeout=30):
    return json.loads(kubectl(*args, "-o", "json", timeout=timeout).stdout)


def newest_pod(selector):
    """Name of the newest pod for a label selector.

    While a pod is being replaced the old one can still be listed, so sort by
    creation time and take the last one (see the catalog notes).
    """
    pods = kubectl_json("get", "pods", "-l", selector, "--sort-by=.metadata.creationTimestamp")["items"]
    running = [p for p in pods if not p["metadata"].get("deletionTimestamp")]
    assert running, f"No running pod found for {selector}"
    return running[-1]["metadata"]["name"]


def pod_status(pod):
    return kubectl_json("get", "pod", pod)


def is_ready(pod_json):
    for cond in pod_json["status"].get("conditions", []):
        if cond["type"] == "Ready":
            return cond["status"] == "True"
    return False


def ready_since(pod_json):
    for cond in pod_json["status"].get("conditions", []):
        if cond["type"] == "Ready" and cond["status"] == "True":
            return parse_ts(cond["lastTransitionTime"])
    return None


def restart_count(pod_json):
    statuses = pod_json["status"].get("containerStatuses", [])
    return statuses[0]["restartCount"] if statuses else 0


def pod_logs(pod, container=None):
    args = ["logs", pod, "--tail=-1"]
    if container:
        args += ["-c", container]
    return kubectl(*args, timeout=60).stdout.splitlines()


OUTDATED = ("{app} in the cluster looks outdated (no event=startup line). Apply the current version from the "
            "repo root:\n  kubectl apply -f apps/{app}/deployment.yaml\n  kubectl -n stars rollout status deployment/{app}")


def restart_deployment(deployment, selector, env=None, timeout=180):
    """Optionally set env vars, restart the deployment, wait for the rollout,
    and return the new pod's name once it is Ready."""
    if env:
        kubectl("set", "env", f"deployment/{deployment}", *[f"{k}={v}" for k, v in env.items()])
    kubectl("rollout", "restart", f"deployment/{deployment}")
    kubectl("rollout", "status", f"deployment/{deployment}", f"--timeout={timeout}s", timeout=timeout + 30)
    return wait_until(lambda: _ready_pod(selector), timeout=60, what=f"{deployment} pod to be Ready")


def _ready_pod(selector):
    pod = newest_pod(selector)
    return pod if is_ready(pod_status(pod)) else None


# ---------------------------------------------------------------- parsing

def parse_ts(text):
    """Parse 2026-10-29T18:48:15Z (log lines and Kubernetes times) as UTC."""
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def parse_line(line):
    """Turn '<UTC> level=INFO service=x run_id=y message="..."' into a dict.

    The leading timestamp is returned as 'ts' (a datetime); quotes are removed.
    """
    parts = line.split(" ", 1)
    fields = {k: v.strip('"') for k, v in KV.findall(line)}
    try:
        fields["ts"] = parse_ts(parts[0])
    except ValueError:
        fields["ts"] = None
    return fields


def number(fields, key):
    return float(fields[key]) if key in fields else None


# ---------------------------------------------------------------- waiting

def wait_until(check, timeout, interval=2, what="condition"):
    """Call check() until it returns something truthy, or fail after timeout seconds."""
    deadline = time.monotonic() + timeout
    while True:
        result = check()
        if result:
            return result
        if time.monotonic() > deadline:
            pytest.fail(f"Timed out after {timeout}s waiting for {what}", pytrace=False)
        time.sleep(interval)


# ---------------------------------------------------------------- OpenObserve

def o2_search(sql, stream_type="logs", minutes=30, size=1000):
    """Run one SQL search against OpenObserve and return the rows."""
    now = int(time.time() * 1_000_000)  # microseconds
    body = {"query": {"sql": sql, "start_time": now - minutes * 60 * 1_000_000,
                      "end_time": now, "from": 0, "size": size}}
    try:
        response = requests.post(f"{O2_URL}/api/{O2_ORG}/_search", params={"type": stream_type},
                                 json=body, auth=O2_AUTH, timeout=30)
    except requests.ConnectionError:
        pytest.fail(f"Cannot reach OpenObserve at {O2_URL}. Start the port-forward:\n"
                    "  kubectl port-forward -n stars svc/openobserve-openobserve-standalone 5080:5080",
                    pytrace=False)
    assert response.status_code != 401, "OpenObserve rejected the login: check O2_USER and O2_PASSWORD"
    response.raise_for_status()
    return response.json().get("hits", [])


def o2_wait(sql, expected, stream_type="logs", timeout=120, minutes=30, size=1000):
    """Search every 5 s until at least `expected` rows come back (data arrives in batches)."""
    deadline = time.monotonic() + timeout
    rows = []
    while time.monotonic() < deadline:
        rows = o2_search(sql, stream_type, minutes, size)
        if len(rows) >= expected:
            break
        time.sleep(5)
    return rows
