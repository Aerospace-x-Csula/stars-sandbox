"""STARS trace generator.

Emits synthetic OpenTelemetry traces that look like a small distributed system:

    frontend -> api -> db
                  `--> payment

Each fake service has its own TracerProvider (its own `service.name`), but all of
them run in this one process. Parent/child links work because they share the
current trace context, so OpenObserve shows one trace spanning four services.

Configuration is by environment variable (see README.md):

    SCENARIO          normal | slow-db | payment-errors     (default: normal)
    RUN_ID            letters, digits, _ and - (max 64)      (required)
    DURATION_SECONDS  how long to generate traffic           (default: 300, 0 = until stopped)
    RATE              target traces per second               (default: 2)
    ERROR_RATE        override payment failure probability   (0.0 - 1.0)
    EXTRA_DB_MS       override extra database latency in ms
    DRY_RUN           1 = print spans to stdout instead of exporting

Export uses the standard OTEL_EXPORTER_OTLP_* variables, e.g.
    OTEL_EXPORTER_OTLP_ENDPOINT=http://<collector>:4318
    OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic%20...   (only if sending straight to OpenObserve)
"""

import os
import random
import re
import signal
import sys
import time
from datetime import datetime, timezone

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

# name -> settings. Every value can still be overridden by env vars.
SCENARIOS = {
    # Healthy baseline with a tiny background failure rate.
    "normal": {"error_rate": 0.01, "extra_db_ms": 0},
    # Database is slow: latency grows in db, api and frontend spans, but no errors.
    "slow-db": {"error_rate": 0.01, "extra_db_ms": 800},
    # Payment service fails most calls; the error propagates up to api and frontend.
    "payment-errors": {"error_rate": 0.70, "extra_db_ms": 0},
}

SERVICES = ["frontend", "api", "db", "payment"]
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(level, scenario, run_id, message):
    # Same key=value style as the log-generator so runs can be correlated.
    print(
        f'{utc_now()} level={level} service=trace-generator '
        f'scenario={scenario} run_id={run_id} message="{message}"',
        flush=True,
    )


def make_exporter():
    if os.getenv("DRY_RUN") == "1":
        return ConsoleSpanExporter()
    # Imported here so DRY_RUN works without the OTLP package installed.
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    return OTLPSpanExporter()  # reads OTEL_EXPORTER_OTLP_* from the environment


def build_tracers(exporter_factory, run_id, scenario):
    """One TracerProvider per fake service. Returns ({name: tracer}, [providers])."""
    tracers, providers = {}, []
    for name in SERVICES:
        resource = Resource.create(
            {
                "service.name": name,
                "service.namespace": "stars",
                "stars.run_id": run_id,
                "stars.scenario": scenario,
                "stars.generator": "trace-generator",
            }
        )
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(exporter_factory()))
        providers.append(provider)
        tracers[name] = provider.get_tracer("stars.trace-generator")
    return tracers, providers


def work(ms_low, ms_high, extra_ms=0):
    time.sleep((random.uniform(ms_low, ms_high) + extra_ms) / 1000.0)


def fail(span, message):
    exc = RuntimeError(message)
    span.record_exception(exc)
    span.set_status(Status(StatusCode.ERROR, message))


def one_request(t, attrs, error_rate, extra_db_ms):
    """Simulate a single checkout request across all four services."""
    failed = False

    with t["frontend"].start_as_current_span(
        "GET /checkout", kind=SpanKind.SERVER, attributes={**attrs, "http.method": "GET", "http.route": "/checkout"}
    ) as fe_server:
        work(2, 8)
        with t["frontend"].start_as_current_span(
            "POST api/checkout", kind=SpanKind.CLIENT, attributes={**attrs, "http.method": "POST"}
        ):
            with t["api"].start_as_current_span(
                "POST /checkout", kind=SpanKind.SERVER, attributes={**attrs, "http.method": "POST", "http.route": "/checkout"}
            ) as api_server:
                work(3, 10)

                # api -> db
                # No db.system on the CLIENT span: OpenObserve would infer an extra
                # "postgresql" service from it. It stays on the db SERVER span below.
                with t["api"].start_as_current_span("db query", kind=SpanKind.CLIENT, attributes=attrs):
                    with t["db"].start_as_current_span(
                        "SELECT orders",
                        kind=SpanKind.SERVER,
                        attributes={**attrs, "db.system": "postgresql", "db.operation": "SELECT", "db.name": "stars-db"},
                    ):
                        work(15, 60, extra_db_ms)

                # api -> payment
                with t["api"].start_as_current_span(
                    "POST payment/charge", kind=SpanKind.CLIENT, attributes={**attrs, "http.method": "POST"}
                ) as pay_client:
                    with t["payment"].start_as_current_span(
                        "POST /charge",
                        kind=SpanKind.SERVER,
                        attributes={**attrs, "http.method": "POST", "http.route": "/charge"},
                    ) as pay_server:
                        work(20, 90)
                        if random.random() < error_rate:
                            failed = True
                            pay_server.set_attribute("http.status_code", 503)
                            fail(pay_server, "payment service unavailable")
                        else:
                            pay_server.set_attribute("http.status_code", 200)
                    if failed:
                        pay_client.set_attribute("http.status_code", 503)
                        fail(pay_client, "payment call failed")

                if failed:
                    api_server.set_attribute("http.status_code", 502)
                    fail(api_server, "upstream payment failure")
                else:
                    api_server.set_attribute("http.status_code", 200)

        if failed:
            fe_server.set_attribute("http.status_code", 502)
            fail(fe_server, "checkout failed")
        else:
            fe_server.set_attribute("http.status_code", 200)

    return failed


def main(exporter_factory=make_exporter):
    scenario = os.getenv("SCENARIO", "normal")
    run_id = os.getenv("RUN_ID", "")

    if scenario not in SCENARIOS:
        print(f"Unknown SCENARIO '{scenario}'. Choose from: {', '.join(SCENARIOS)}", file=sys.stderr)
        return 2
    if not RUN_ID_PATTERN.match(run_id):
        print("RUN_ID is required: 1-64 letters, digits, underscores or hyphens", file=sys.stderr)
        return 2

    cfg = SCENARIOS[scenario]
    error_rate = float(os.getenv("ERROR_RATE", cfg["error_rate"]))
    extra_db_ms = float(os.getenv("EXTRA_DB_MS", cfg["extra_db_ms"]))
    rate = float(os.getenv("RATE", "2"))
    duration = float(os.getenv("DURATION_SECONDS", "300"))

    tracers, providers = build_tracers(exporter_factory, run_id, scenario)
    attrs = {"run_id": run_id, "scenario": scenario}

    stop = {"now": False}

    def handle_signal(signum, _frame):
        stop["now"] = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    log("INFO", scenario, run_id,
        f"Run started rate={rate} duration_s={duration:g} error_rate={error_rate} extra_db_ms={extra_db_ms:g}")

    started = time.monotonic()
    total = errors = 0
    interval = 1.0 / rate if rate > 0 else 1.0
    while not stop["now"] and (duration == 0 or time.monotonic() - started < duration):
        tick = time.monotonic()
        if one_request(tracers, attrs, error_rate, extra_db_ms):
            errors += 1
        total += 1
        time.sleep(max(0.0, interval - (time.monotonic() - tick)))

    for provider in providers:
        provider.force_flush()
        provider.shutdown()

    log("INFO", scenario, run_id, f"Run completed traces={total} failed_traces={errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
