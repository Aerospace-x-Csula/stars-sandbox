import os, random, signal, sys, time
from datetime import datetime, timezone

READY_FILE = "/tmp/ready"	# Probes in deployment.yaml check this file

random.seed(42)
start = time.time()


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(level, message):
    # Same key=value style as the metric lines, so the same OpenObserve filter finds both
    print('%s level=%s service=synthetic-metrics scenario=metrics host=synthetic-host-1 message="%s"'
          % (stamp(), level, message), flush=True)


def stop(signum, frame):
    # Kubernetes sends SIGTERM when the pod is stopped or restarted
    log("INFO", "Stopping")
    try:
        os.remove(READY_FILE)
    except OSError:
        pass
    sys.exit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

log("INFO", "Started interval_s=5 cpu_spike=every 5 min memory_leak=minutes 35-50 of each hour")
in_spike = False
in_leak = False

while True:
    now = datetime.now(timezone.utc)
    minute = ((time.time() - start) / 60) % 60
    spike_minute = ((time.time() - start) / 60) % 5

    cpu = 25 + random.gauss(0, 2)
    memory = 55 + random.gauss(0, 0.4)

    spike = 4 <= spike_minute < 5	# Generates CPU spikes every 5th minute
    leak = 35 <= minute < 50		# Generates Memory leaks every 35th minute

    # Log only when an event starts or ends, not on every line
    if spike != in_spike:
        if spike:
            log("WARN", "CPU spike started")
        else:
            log("INFO", "CPU spike ended")
        in_spike = spike
    if leak != in_leak:
        if leak:
            log("WARN", "Memory leak started")
        else:
            log("INFO", "Memory leak ended")
        in_leak = leak

    if spike:
        cpu += 55
    if leak:
        memory += 30 * (minute - 35) / 15
					#Printing the logs out for metrics to be pushed into OpenObserve
    print("%s level=INFO service=synthetic-metrics scenario=metrics host=synthetic-host-1 cpu_percent=%.2f memory_percent=%.2f"
          % (now.strftime("%Y-%m-%dT%H:%M:%SZ"), max(0, min(100, cpu)), max(0, min(100, memory))), flush=True)

    # Touch the ready file after every line: the readiness probe fails if it goes stale
    with open(READY_FILE, "w") as f:
        f.write(stamp())
    time.sleep(5)
