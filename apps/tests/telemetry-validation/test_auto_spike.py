"""TC-11: log-generator automatic error spikes (AUTO_SPIKE).

Turns AUTO_SPIKE on, checks the first spikes, then turns it off again and checks
that no spikes appear. Takes about 2-3 minutes and restarts log-generator twice.
The deployment is always left with AUTO_SPIKE=false (its default).
"""

import re
import time
from collections import OrderedDict

import pytest

from helpers import (OUTDATED, O2_STREAM, needs_openobserve, o2_wait, parse_line, pod_logs, pod_status,
                     restart_count, restart_deployment, wait_until)

SELECTOR = "app=log-generator"
DEPLOYMENT = "log-generator"
AUTO_RUN_ID = re.compile(r"^auto-\d{8}T\d{6}Z-(\d+)$")

# error_index % 5 -> scenario, and the start of its message (catalog, Part 4)
CYCLE = {
    1: ("authentication", "authentication failure"),
    2: ("database", "database timeout"),
    3: ("connectivity", "connection failure"),
    4: ("dependency", "dependency failure"),
    0: ("service", "service unavailable"),
}


def spikes(pod):
    """Spike lines of the pod, grouped by run_id in the order they appeared."""
    groups = OrderedDict()
    startup = None
    for line in pod_logs(pod, container="log-generator"):
        fields = parse_line(line)
        if fields.get("event") == "startup":
            startup = fields["ts"]
        if fields.get("spike") == "true":
            groups.setdefault(fields["run_id"], []).append(fields)
    return startup, groups


@pytest.fixture(scope="module")
def spike_run():
    pod = restart_deployment(DEPLOYMENT, SELECTOR, env={"AUTO_SPIKE": "true"})

    def three_spikes_started():
        startup, groups = spikes(pod)
        if startup is None and len(pod_logs(pod, container="log-generator")) > 3:
            pytest.fail(OUTDATED.format(app=DEPLOYMENT), pytrace=False)
        return (startup, groups) if len(groups) >= 3 else None

    # Spikes come every 20 s, the first at startup: 3 have started after about 45 s.
    startup, groups = wait_until(three_spikes_started, timeout=90, interval=5, what="3 automatic spikes")
    try:
        yield {"pod": pod, "startup": startup, "groups": groups}
    finally:
        restart_deployment(DEPLOYMENT, SELECTOR, env={"AUTO_SPIKE": "false"})


def test_tc11_spikes_are_complete_and_ordered(spike_run):
    groups = list(spike_run["groups"].items())
    complete = groups[:-1]  # the newest spike may still be printing
    assert len(complete) >= 2, f"Expected at least 2 complete spikes, got {len(complete)}"

    numbers = []
    for run_id, lines in complete:
        match = AUTO_RUN_ID.match(run_id)
        assert match, f"run_id {run_id} is not auto-<UTC>-<n>"
        numbers.append(int(match[1]))

        assert len(lines) == 20, f"{run_id}: expected 20 lines, got {len(lines)}"
        assert all(l.get("level") == "ERROR" for l in lines), f"{run_id}: not every line is ERROR"
        indexes = [int(l["error_index"]) for l in lines]
        assert indexes == list(range(1, 21)), f"{run_id}: error_index should be 1..20 in order, got {indexes}"
        for l in lines:
            scenario, message = CYCLE[int(l["error_index"]) % 5]
            assert l["scenario"] == scenario, f"{run_id} index {l['error_index']}: scenario {l['scenario']}, expected {scenario}"
            assert l["message"].startswith(message), f"{run_id} index {l['error_index']}: unexpected message {l['message']}"

    assert "invalid_token" in complete[0][1][0]["message"], "Index 1 should be the invalid_token authentication failure"
    assert numbers == list(range(numbers[0], numbers[0] + len(numbers))), f"Spike numbers should rise by 1: {numbers}"


def test_tc11_spike_timing(spike_run):
    starts = [lines[0]["ts"] for _, lines in spike_run["groups"].items()]
    first_gap = (starts[0] - spike_run["startup"]).total_seconds()
    assert first_gap <= 2, f"The first spike should start at startup; it started {first_gap:.0f} s later"
    gaps = [(b - a).total_seconds() for a, b in zip(starts, starts[1:])]
    assert all(18 <= g <= 22 for g in gaps), f"Spikes should start 18-22 s apart, got {gaps}"
    assert restart_count(pod_status(spike_run["pod"])) == 0, "log-generator restarted while spikes were on"


@needs_openobserve
def test_tc11_spikes_reach_openobserve(spike_run):
    run_id = next(iter(spike_run["groups"]))
    sql = (f'SELECT body FROM "{O2_STREAM}" WHERE k8s_container_name = \'log-generator\' '
           f"AND body LIKE '%spike=true run_id={run_id} %'")
    rows = o2_wait(sql, expected=20, timeout=90)
    assert len(rows) == 20, f"Expected the 20 lines of {run_id} in OpenObserve, found {len(rows)}"


def test_tc11_no_spikes_when_off(spike_run):
    # Runs last in this file: turn spikes off and watch for two intervals.
    pod = restart_deployment(DEPLOYMENT, SELECTOR, env={"AUTO_SPIKE": "false"})

    time.sleep(45)
    _, groups = spikes(pod)
    assert not groups, f"Found {sum(len(g) for g in groups.values())} spike=true lines with AUTO_SPIKE=false"
    assert restart_count(pod_status(pod)) == 0, "log-generator restarted"
