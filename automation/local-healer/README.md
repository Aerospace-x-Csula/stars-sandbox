# Local Healer (`local-healer`)

The `local-healer` component is an automated self-healing script that monitors pod health within a target Kubernetes cluster (e.g., Minikube) and automatically replaces failing pods based on built-in safety limits.

## Directory Structure

```text
automation/local-healer/
├── local_healer.py    # Main self-healing monitoring and remediation script
├── requirements.txt   # Python package dependencies
└── README.md          # Setup and usage documentation
```

## Prerequisites

* **Python 3.9+**
* **kubectl** installed and configured
* A running Kubernetes cluster (e.g., **Minikube**) with active workloads

Verify your cluster connectivity before running the healer:
```bash
kubectl cluster-info
```

## Setup & Installation

1. Navigate to the local-healer directory:
```bash
cd automation/local-healer
```

2. Create and activate a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
```
```powershell
python -m venv venv
venv\Scripts\Activate.ps1       # Windows PowerShell
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python local_healer.py
```

Stop it with Ctrl+C.

## How it works

The healer checks the cluster every 10 seconds and looks only at pods labeled
`auto-heal=true`. A pod also needs an `app` (or `app.kubernetes.io/name`)
label and must be owned by a controller such as a Deployment. If the pod is
unhealthy (for example CrashLoopBackOff or a failing readiness probe), the
healer deletes it so its controller recreates it.

## Safety limits

- At most 3 heals per app and namespace within a 30-minute window. After that
  the healer stops acting on that app and prints a "blocked" audit entry.
- The block clears after the app has been healthy for 10 minutes.
- Pods that are starting up or terminating are skipped.
- Every action, and every blocked action, prints an audit entry (trigger,
  evidence, decision, action, result) in the terminal.

The limits are constants at the top of `local_healer.py`
(`WINDOW_SECONDS`, `MAX_HEALS_IN_WINDOW`, `STABLE_RESET_SECONDS`,
`CHECK_INTERVAL_SECONDS`).

## Known limits

See the [Known limits](../README.md#known-limits) section in the Automation README.