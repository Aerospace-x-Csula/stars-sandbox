"""TC-16 and TC-17: startup and readiness.

TC-16 restarts log-generator and synthetic-metrics and checks the event=startup /
event=ready lines against the pod's Ready time (about 1 minute).
TC-17 makes synthetic-metrics Not Ready on purpose for 70 s and checks that it
recovers by itself without restarting (about 2 minutes).
"""

import subprocess
import time
from datetime import datetime, timezone

import pytest

from helpers import (OUTDATED, NAMESPACE, is_ready, kubectl_json, newest_pod, parse_line, pod_logs,
                     pod_status, ready_since, restart_count, restart_deployment, wait_until)

APPS = {
    "log-generator": ("app=log-generator", "log-generator"),
    "synthetic-metrics": ("app=synthetic-metrics", None),
}


@pytest.mark.parametrize("app", list(APPS))
def test_tc16_starts_and_becomes_ready(app):
    selector, container = APPS[app]
    restarted_at = datetime.now(timezone.utc)
    pod = restart_deployment(app, selector)

    status = pod_status(pod)
    ready_at = ready_since(status)
    assert ready_at, f"{pod} is not Ready"
    assert (ready_at - restarted_at).total_seconds() <= 60, f"{pod} took more than 60 s to become Ready"
    assert restart_count(status) == 0, f"{pod} restarted"

    events = [parse_line(l) for l in pod_logs(pod, container) if "event=" in l]
    startup = [e for e in events if e.get("event") == "startup"]
    ready = [e for e in events if e.get("event") == "ready"]
    if not startup and not ready:
        pytest.fail(OUTDATED.format(app=app), pytrace=False)
    assert len(startup) == 1 and len(ready) == 1, f"Expected 1 startup and 1 ready line, got {len(startup)} and {len(ready)}"
    assert startup[0]["run_id"] == ready[0]["run_id"], "startup and ready lines have different run_ids"
    assert startup[0]["ts"] <= ready[0]["ts"], "event=ready was logged before event=startup"
    # The pod may only be Ready after it logged event=ready (1 s tolerance).
    gap = (ready_at - ready[0]["ts"]).total_seconds()
    assert gap >= -1, f"Pod became Ready {-gap:.0f} s before logging event=ready"


def test_tc17_not_ready_on_purpose_then_recovers():
    selector = "app=synthetic-metrics"
    pod = newest_pod(selector)
    status = pod_status(pod)
    assert is_ready(status), f"{pod} must be Ready before the test starts"
    restarts_before = restart_count(status)

    def metric_lines():
        return sum(1 for l in pod_logs(pod) if "cpu_percent=" in l)

    lines_before = metric_lines()

    # Keep /tmp/ready stale for 70 s: reset its time to 1970 every 0.2 s (catalog, scenario 17).
    loop = ("end=$(( $(date +%s) + 70 )); "
            "while [ $(date +%s) -lt $end ]; do touch -d @0 /tmp/ready; sleep 0.2; done")
    trigger = subprocess.Popen(["kubectl", "-n", NAMESPACE, "exec", pod, "--", "sh", "-c", loop],
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        wait_until(lambda: not is_ready(pod_status(pod)), timeout=60, what=f"{pod} to become Not Ready")

        status = pod_status(pod)
        assert restart_count(status) == restarts_before, "The container restarted; readiness must not restart it"
        assert status["status"]["phase"] == "Running"

        time.sleep(10)
        assert metric_lines() >= lines_before + 2, "The script stopped writing metrics lines while Not Ready"

        events = kubectl_json("get", "events", "--field-selector", f"involvedObject.name={pod},reason=Unhealthy")
        messages = [e.get("message", "") for e in events["items"]]
        assert any("Readiness probe failed" in m for m in messages), f"No 'Readiness probe failed' event: {messages}"
    finally:
        try:
            trigger.wait(timeout=90)
        except subprocess.TimeoutExpired:
            trigger.kill()

    # After the loop ends the script rewrites /tmp/ready on its own.
    wait_until(lambda: is_ready(pod_status(pod)), timeout=30, what=f"{pod} to become Ready again")
    assert restart_count(pod_status(pod)) == restarts_before, "The container restarted"
