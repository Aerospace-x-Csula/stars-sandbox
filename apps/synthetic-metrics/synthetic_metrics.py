import os, random, re, signal, sys, time
from datetime import datetime, timezone

READY_FILE = "/tmp/ready"	# Probes in deployment.yaml check this file

# Settings come from deployment.yaml (see README "Settings")
RUN_ID = os.getenv("RUN_ID", "manual")			# Tags every line so one search finds the whole run
ANOMALIES = os.getenv("ANOMALIES", "on").lower() == "on"	# "off" = normal values only (baseline runs)

if not re.match(r"^[A-Za-z0-9_-]{1,64}$", RUN_ID):
    print("RUN_ID must be 1-64 letters, digits, underscores or hyphens", file=sys.stderr)
    sys.exit(2)

random.seed(42)
start = time.time()


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(level, message):
    # Same key=value style as the metric lines, so the same OpenObserve filter finds both
    print('%s level=%s service=synthetic-metrics scenario=metrics host=synthetic-host-1 run_id=%s message="%s"'
          % (stamp(), level, RUN_ID, message), flush=True)


def event(name, message):
    # Startup/readiness lines in the format confirmed with the Observability team
    # run_id goes at the end, after the confirmed fields (same as log-generator)
    print('%s level=INFO service=synthetic-metrics event=%s message="%s" run_id=%s'
          % (stamp(), name, message, RUN_ID), flush=True)


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

event("startup", "Process started")
if ANOMALIES:
    log("INFO", "Settings interval_s=5 anomalies=on cpu_spike=every 5 min memory_leak=minutes 35-50 of each hour")
else:
    log("INFO", "Settings interval_s=5 anomalies=off")
in_spike = False
in_leak = False
announced_ready = False

while True:
    now = datetime.now(timezone.utc)
    minute = ((time.time() - start) / 60) % 60
    spike_minute = ((time.time() - start) / 60) % 5

    cpu = 25 + random.gauss(0, 2)
    memory = 55 + random.gauss(0, 0.4)

    spike = ANOMALIES and 4 <= spike_minute < 5	# Generates CPU spikes every 5th minute
    leak = ANOMALIES and 35 <= minute < 50		# Generates Memory leaks every 35th minute

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
    print("%s level=INFO service=synthetic-metrics scenario=metrics host=synthetic-host-1 run_id=%s cpu_percent=%.2f memory_percent=%.2f"
          % (now.strftime("%Y-%m-%dT%H:%M:%SZ"), RUN_ID, max(0, min(100, cpu)), max(0, min(100, memory))), flush=True)

    # Touch the ready file after every line: the readiness probe fails if it goes stale
    with open(READY_FILE, "w") as f:
        f.write(stamp())
    if not announced_ready:
        event("ready", "Ready to serve")
        announced_ready = True
    time.sleep(5)
