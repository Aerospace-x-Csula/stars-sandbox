"""Locust load tests for the app in the stars namespace.

User classes (pick them in the web UI, or name them on the command line):
  NormalUser       steady, human-paced traffic, no errors
  HighTrafficUser  the same requests, nearly back to back (use many users)
  FailingUser      bad routes, server errors and a request that times out

Every run gets a run_id and a scenario label. Test start and stop are logged
as JSON lines and, if O2_URL is set, sent to OpenObserve together with every
request.

Keep this file ASCII-only: on Windows PowerShell 5.1 it is piped through a
text pipeline when the ConfigMap is created, which can corrupt other characters.
"""
import base64
import json
import logging
import os
import time
import uuid

import gevent
import requests
from locust import HttpUser, between, events, task

log = logging.getLogger("stars.loadtest")

# Optional OpenObserve output. Leave O2_URL unset to turn it off.
# Example O2_URL: http://openobserve.observability.svc.cluster.local:5080/api/default
O2_URL = os.getenv("O2_URL", "").rstrip("/")
O2_HEADERS = {}
if os.getenv("O2_USER"):
    _creds = "{}:{}".format(os.getenv("O2_USER"), os.getenv("O2_PASSWORD", ""))
    O2_HEADERS = {"Authorization": "Basic " + base64.b64encode(_creds.encode()).decode()}

_run = {"run_id": "-", "scenario": "-", "started": time.time()}
_buffer = []


# --------------------------------------------------------------------------
# Run tagging, start/stop logging and OpenObserve output
# --------------------------------------------------------------------------
@events.init_command_line_parser.add_listener
def add_arguments(parser):
    # Shows up as a field in the web UI and as --scenario on the command line.
    parser.add_argument(
        "--scenario", type=str, env_var="LOCUST_SCENARIO", default="adhoc",
        include_in_web_ui=True,
        help="Label for this run, e.g. normal, high-traffic, failing, mixed",
    )
    parser.add_argument(
        "--run-id", type=str, env_var="LOCUST_RUN_ID", default="",
        include_in_web_ui=False,
        help="Optional fixed run id. A short random id is generated if empty.",
    )


def _post(stream, rows):
    if not O2_URL or not rows:
        return
    try:
        requests.post("{}/{}/_json".format(O2_URL, stream), json=rows,
                      headers=O2_HEADERS, timeout=5)
    except Exception as exc:  # never let telemetry break the load test
        log.warning("OpenObserve post failed: %s", exc)


def _flush():
    if _buffer:
        rows = _buffer[:]
        del _buffer[:]
        _post("locust", rows)


def _flush_loop():
    while True:
        gevent.sleep(2)
        _flush()


def _event(name, **fields):
    row = {"event": name, "run_id": _run["run_id"], "scenario": _run["scenario"]}
    row.update(fields)
    log.info("loadtest %s", json.dumps(row))
    stamped = dict(row)
    stamped["_timestamp"] = int(time.time() * 1000000)
    _post("locust_runs", [stamped])


@events.init.add_listener
def on_init(environment, **kwargs):
    gevent.spawn(_flush_loop)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    opts = environment.parsed_options
    _run["run_id"] = getattr(opts, "run_id", "") or uuid.uuid4().hex[:8]
    _run["scenario"] = getattr(opts, "scenario", "") or "adhoc"
    _run["started"] = time.time()
    runner = environment.runner
    _event(
        "test_start",
        host=environment.host,
        users=getattr(runner, "target_user_count", None),
    )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    total = environment.stats.total
    _flush()
    _event(
        "test_stop",
        duration_s=round(time.time() - _run["started"], 1),
        requests=total.num_requests,
        failures=total.num_failures,
        avg_ms=round(total.avg_response_time, 1),
        p95_ms=total.get_response_time_percentile(0.95),
    )


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    _flush()


@events.request.add_listener
def on_request(request_type, name, response_time, exception, response=None, **kwargs):
    _buffer.append({
        "_timestamp": int(time.time() * 1000000),
        "run_id": _run["run_id"],
        "scenario": _run["scenario"],
        "method": request_type,
        "name": name,
        "status_code": getattr(response, "status_code", 0) or 0,
        "response_time_ms": round(response_time, 1),
        "failed": exception is not None,
        "error": str(exception) if exception else "",
    })


# --------------------------------------------------------------------------
# User classes. Paths below are for the httpbin stand-in; change them to your
# app's real endpoints.
# --------------------------------------------------------------------------
class NormalUser(HttpUser):
    """Steady, human-paced traffic. No errors."""
    wait_time = between(1, 3)

    @task(3)
    def homepage(self):
        self.client.get("/", name="homepage")

    @task(2)
    def list_items(self):
        self.client.get("/get", name="list_items")


class HighTrafficUser(HttpUser):
    """Same requests as NormalUser, but nearly back to back.
    Run this with a high user count."""
    wait_time = between(0.05, 0.3)

    @task(3)
    def homepage(self):
        self.client.get("/", name="homepage")

    @task(2)
    def list_items(self):
        self.client.get("/get", name="list_items")


class FailingUser(HttpUser):
    """Generates errors: server errors, missing pages and timeouts."""
    wait_time = between(0.5, 2)

    @task(3)
    def server_error(self):
        # httpbin returns a 500 on demand. Your own app will not have this
        # route; remove it or call an endpoint that fails.
        self.client.get("/status/500", name="server_error")

    @task(2)
    def missing_page(self):
        self.client.get("/does-not-exist", name="missing_page")

    @task(1)
    def slow_request(self):
        # The server waits 5s but the client gives up after 1s, so Locust
        # records this as a failed request (timeout, status 0).
        self.client.get("/delay/5", name="slow_request", timeout=1)
