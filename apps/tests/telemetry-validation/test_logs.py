import subprocess
import time
import uuid


def test_error_spike():
    # Create a unique ID for this test
    run_id = f"test-{uuid.uuid4().hex[:8]}"

    # Trigger the failure
    trigger = subprocess.run(
        [
            "kubectl", "exec", "-n", "stars",
            "deployment/log-generator", "--",
            "/tmp/stars-trigger", "error-spike", run_id
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=15
    )

    assert f"Queued scenario=error-spike run_id={run_id}" in trigger.stdout

    # Retry until the scenario completes or 15 seconds pass
    deadline = time.monotonic() + 15
    error_logs = []
    completed = False

    while time.monotonic() < deadline:
        result = subprocess.run(
            [
                "kubectl", "logs", "-n", "stars",
                "deployment/log-generator"
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        # Only count logs belonging to this test
        matching_lines = [
            line for line in result.stdout.splitlines()
            if f"run_id={run_id} " in line
            and "scenario=error-spike" in line
        ]

        error_logs = [
            line for line in matching_lines
            if "level=ERROR" in line
            and "Injected application error" in line
        ]

        completed = any(
            'message="Scenario completed"' in line
            for line in matching_lines
        )

        if completed:
            break

        time.sleep(1)

    # Verify the expected results
    assert completed, "Scenario did not complete within 15 seconds"
    assert len(error_logs) == 20, (
        f"Expected 20 error logs, found {len(error_logs)}"
    )

def test_warning():
    run_id = f"test-{uuid.uuid4().hex[:8]}"

    subprocess.run(
        [
            "kubectl", "exec", "-n", "stars",
            "deployment/log-generator", "--",
            "/tmp/stars-trigger", "warn", run_id
        ],
        check=True
    )

    deadline = time.monotonic() + 15

    while time.monotonic() < deadline:
        result = subprocess.run(
            ["kubectl", "logs", "-n", "stars",
             "deployment/log-generator"],
            capture_output=True,
            text=True,
            check=True
        )

        matching_logs = [
            line for line in result.stdout.splitlines()
            if f"run_id={run_id} " in line
            and "level=WARN" in line
            and "scenario=warn" in line
        ]

        if len(matching_logs) == 1:
            return

        time.sleep(1)

    assert False, "Expected warning log was not found"


def test_error():
    run_id = f"test-{uuid.uuid4().hex[:8]}"

    subprocess.run(
        [
            "kubectl", "exec", "-n", "stars",
            "deployment/log-generator", "--",
            "/tmp/stars-trigger", "error", run_id
        ],
        check=True
    )

    deadline = time.monotonic() + 15

    while time.monotonic() < deadline:
        result = subprocess.run(
            ["kubectl", "logs", "-n", "stars",
             "deployment/log-generator"],
            capture_output=True,
            text=True,
            check=True
        )

        matching_logs = [
            line for line in result.stdout.splitlines()
            if f"run_id={run_id} " in line
            and "level=ERROR" in line
            and "scenario=error " in line
        ]

        if len(matching_logs) == 1:
            return

        time.sleep(1)

    assert False, "Expected error log was not found"


def test_connectivity():
    run_id = f"test-{uuid.uuid4().hex[:8]}"

    subprocess.run(
        [
            "kubectl", "exec", "-n", "stars",
            "deployment/log-generator", "--",
            "/tmp/stars-trigger", "connectivity", run_id
        ],
        check=True
    )

    deadline = time.monotonic() + 15

    while time.monotonic() < deadline:
        result = subprocess.run(
            ["kubectl", "logs", "-n", "stars",
             "deployment/log-generator"],
            capture_output=True,
            text=True,
            check=True
        )

        matching_logs = [
            line for line in result.stdout.splitlines()
            if f"run_id={run_id} " in line
            and "level=ERROR" in line
            and "scenario=connectivity" in line
            and "Controlled connection failure" in line
        ]

        if len(matching_logs) == 1:
            return

        time.sleep(1)

    assert False, "Expected connectivity failure log was not found"

def test_crash():
    run_id = f"test-{uuid.uuid4().hex[:8]}"

    # Identify the current pod and restart count
    def get_pod_status():
        result = subprocess.run(
            [
                "kubectl", "get", "pods",
                "-n", "stars",
                "-l", "app=log-generator",
                "-o", "json"
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        import json
        pods = json.loads(result.stdout)["items"]
        assert len(pods) == 1, "Expected exactly one log-generator pod"

        return pods[0]

    pod_before = get_pod_status()
    pod_name = pod_before["metadata"]["name"]
    status_before = pod_before["status"]["containerStatuses"][0]
    restarts_before = status_before["restartCount"]

    # Trigger the crash
    subprocess.run(
        [
            "kubectl", "exec", "-n", "stars",
            pod_name, "--",
            "/tmp/stars-trigger", "crash", run_id
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=15
    )

    # Wait for Kubernetes to restart the container
    deadline = time.monotonic() + 60
    recovered = False

    while time.monotonic() < deadline:
        pod = get_pod_status()

        if pod["metadata"]["uid"] != pod_before["metadata"]["uid"]:
            break

        container = pod["status"]["containerStatuses"][0]
        last_exit = container.get("lastState", {}).get("terminated", {})

        if (
            container["restartCount"] > restarts_before
            and last_exit.get("exitCode") == 42
            and container.get("ready", False)
        ):
            recovered = True
            break

        time.sleep(2)

    assert recovered, "Container did not restart successfully within 60 seconds"

    # Verify the previous container recorded the crash
    logs = subprocess.run(
        [
            "kubectl", "logs", "-n", "stars",
            pod_name, "--previous"
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=10
    )

    assert any(
        f"run_id={run_id}" in line
        and "level=ERROR" in line
        and "Injected container crash; exiting with code 42" in line
        for line in logs.stdout.splitlines()
    ), "Expected crash log not found"