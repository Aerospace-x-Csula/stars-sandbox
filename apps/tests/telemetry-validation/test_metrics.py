"""TC-09 and TC-10: synthetic-metrics CPU spike and memory leak.

Both use one fresh pod: the schedule counts from pod start.
  TC-09 (CPU spike)   ~6 minutes   marked slow
  TC-10 (memory leak) ~52 minutes  marked very_slow; keep the laptop awake
Afterwards the deployment is put back to its defaults (RUN_ID=metrics01, ANOMALIES=on).
"""

import uuid

import pytest

from helpers import (number, parse_line, pod_logs, pod_status, restart_count,
                     restart_deployment, wait_until)

SELECTOR = "app=synthetic-metrics"
DEPLOYMENT = "synthetic-metrics"


@pytest.fixture(scope="module")
def metrics_run():
    """Restart synthetic-metrics with a new RUN_ID and anomalies on."""
    run_id = f"tc-metrics-{uuid.uuid4().hex[:6]}"
    pod = restart_deployment(DEPLOYMENT, SELECTOR, env={"RUN_ID": run_id, "ANOMALIES": "on"})
    yield {"pod": pod, "run_id": run_id}
    restart_deployment(DEPLOYMENT, SELECTOR, env={"RUN_ID": "metrics01", "ANOMALIES": "on"})


def read(pod):
    """Parsed log lines of the pod, plus the event=startup time."""
    lines = [parse_line(l) for l in pod_logs(pod)]
    startup = next(l["ts"] for l in lines if l.get("event") == "startup")
    return lines, startup


def index_of(lines, message):
    found = [i for i, l in enumerate(lines) if l.get("message") == message]
    return found


def wait_for_message(pod, message, timeout):
    def seen():
        lines, _ = read(pod)
        return index_of(lines, message)
    wait_until(seen, timeout=timeout, interval=10, what=f'"{message}"')
    return read(pod)


@pytest.mark.slow
def test_tc09_cpu_spike(metrics_run):
    pod = metrics_run["pod"]
    # First spike starts at minute 4 and ends at minute 5 after pod start.
    lines, startup = wait_for_message(pod, "CPU spike ended", timeout=7 * 60)
    six_min = [l for l in lines if l["ts"] and (l["ts"] - startup).total_seconds() <= 6 * 60]

    starts, ends = index_of(six_min, "CPU spike started"), index_of(six_min, "CPU spike ended")
    assert len(starts) == 1 and len(ends) == 1, f"Expected 1 start and 1 end line, got {len(starts)} and {len(ends)}"
    s, e = starts[0], ends[0]

    inside = [number(l, "cpu_percent") for l in six_min[s:e] if "cpu_percent" in l]
    outside = [number(l, "cpu_percent") for i, l in enumerate(six_min)
               if "cpu_percent" in l and not s <= i < e]
    memory = [number(l, "memory_percent") for l in six_min if "memory_percent" in l]

    assert 11 <= len(inside) <= 13, f"Expected 11-13 metrics lines during the spike, got {len(inside)}"
    assert all(c > 65 for c in inside), f"CPU during the spike should be above 65: {inside}"
    assert all(c < 65 for c in outside), f"CPU outside the spike should be below 65: {[c for c in outside if c >= 65]}"
    assert all(m < 65 for m in memory), "memory_percent should stay below 65 during the first 6 minutes"
    assert restart_count(pod_status(pod)) == 0, "The pod restarted"


@pytest.mark.very_slow
def test_tc10_memory_leak(metrics_run):
    pod = metrics_run["pod"]
    # Leak runs from minute 35 to minute 50 after pod start.
    lines, startup = wait_for_message(pod, "Memory leak ended", timeout=55 * 60)

    starts, ends = index_of(lines, "Memory leak started"), index_of(lines, "Memory leak ended")
    assert len(starts) == 1 and len(ends) == 1, f"Expected 1 start and 1 end line, got {len(starts)} and {len(ends)}"
    s, e = starts[0], ends[0]
    minutes = (lines[e]["ts"] - lines[s]["ts"]).total_seconds() / 60
    assert 13 <= minutes <= 17, f"Leak lasted {minutes:.1f} min; expected 13-17 (was the laptop asleep?)"

    # memory_percent should climb about 2 points per minute: fit a straight line.
    points = [((l["ts"] - lines[s]["ts"]).total_seconds() / 60, number(l, "memory_percent"))
              for l in lines[s:e] if "memory_percent" in l]
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / sum((x - mean_x) ** 2 for x, _ in points)
    assert 1.5 <= slope <= 2.5, f"Memory climbed {slope:.2f} points per minute; expected about 2"
    assert points[0][1] < 60, f"Memory at the start of the leak was {points[0][1]}; expected about 55"
    assert max(y for _, y in points) > 80, "Memory never got above 80 during the leak"

    def readings_after_end():
        fresh, _ = read(pod)
        return [number(l, "memory_percent") for l in fresh[e + 1:] if "memory_percent" in l]

    after = wait_until(readings_after_end, timeout=30, interval=5, what="a reading after the leak ended")
    assert after[0] < 65, f"Memory after the leak should drop below 65, got {after[0]}"
    assert restart_count(pod_status(pod)) == 0, "The pod restarted"
