# STARS — Automated Telemetry Validation

## Overview

This project uses Python and pytest to automatically test the STARS log generator running in a local Kubernetes environment.

The tests trigger predefined failure scenarios and verify the expected logs and container behavior using Kubernetes.

## Prerequisites

- Python 3.10 or newer
- Minikube
- kubectl
- A running STARS log-generator deployment in the `stars` namespace

## Setup

Navigate to the testing directory:

```bash
cd apps/tests/telemetry-validation
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
```

Activate the environment (macOS/Linux):

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Verify your Kubernetes environment:

```bash
kubectl config current-context
kubectl get pods -n stars
```

Ensure the `log-generator` pod is running before executing tests.

## Running the Tests

Run the entire test suite:

```bash
python -m pytest -v
```

Run a single test:

```bash
python -m pytest test_logs.py::test_error_spike -v
```

## Test Scenarios

| Test | Expected Result |
|---|---|
| `test_warning` | Generates one warning log |
| `test_error` | Generates one application error log |
| `test_error_spike` | Generates 20 application error logs |
| `test_connectivity` | Generates one controlled connection failure log |
| `test_crash` | Terminates the container with exit code 42 and verifies Kubernetes recovery |

## Expected Results

When all five scenarios execute successfully, pytest reports:

```text
5 passed
```

Each execution uses a unique test identifier to distinguish its logs from previous runs.

## Limitations

- Tests currently validate Kubernetes logs and container behavior.
- OpenObserve ingestion validation is not yet implemented.
- Tests require access to a running local Minikube environment.
- The crash test intentionally restarts the log-generator container. Avoid running it while another teammate is using the same deployment.
- Tests assume the existing single-replica log-generator deployment.

## Future Improvements

- Integrate OpenObserve API validation.
- Expand regression testing as new failure scenarios are introduced.
- Save structured test reports for project evaluation.

## Project Alignment

**STARS Project Outline — Data/Test Engineering**

Supports regression testing, failure-injection validation, reproducibility, and evidence collection.
