# Local Healer (`local-healer`)

The `local-healer` component is an automated self-healing script designed to monitor pod health within a target Kubernetes cluster (e.g., Minikube) and automatically mitigate failing pods based on configurable rules.

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
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main healer script:

```Bash
python local_healer.py
```