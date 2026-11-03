# STARS Sandbox System Overview

> **Status:** Draft — pending review by the Architecture Lead and relevant sub-leads.
> **Scope:** The documented local development sandbox, not a production STARS deployment. Running workloads and end-to-end telemetry have not been independently verified.

## Purpose

The STARS sandbox is a local, reproducible development environment for the **STARS AI-Powered Observability Platform**, a university capstone project in collaboration with The Aerospace Corporation. The project aims to monitor a representative environment, investigate problems using telemetry, and eventually support AI-assisted detection, root-cause analysis, and controlled remediation.

The current focus is establishing a working local Kubernetes sandbox with OpenObserve. Later features should be documented as implemented and tested, rather than assumed to be available.

## Current High-Level Architecture

The repository provides setup scripts for Windows and macOS that prepare a local Minikube cluster and install OpenObserve using Helm.

```text
Student workstation (Windows or macOS)
  |-- Git / stars-sandbox repository
  |-- Docker Desktop
  |     `-- Minikube (local Kubernetes cluster)
  |           `-- Kubernetes namespace: stars
  |                 `-- OpenObserve (Helm release: openobserve)
  `-- kubectl / Helm
        `-- Port-forward OpenObserve to http://localhost:5080

Planned integration (not yet verified end-to-end):
Sample applications --> Telemetry collectors --> OpenObserve
                                               |
                                               v
                              AI detection / investigation
                                               |
                                               v
                                  Controlled remediation
```

This diagram shows the **documented setup path**, not a verified inventory of running Pods or complete telemetry pipelines. There is no confirmed production or shared cluster in this overview.

## Main Components

| Component | Current documented role |
| --- | --- |
| **Developer workstation** | Runs setup scripts, Docker Desktop, Minikube, `kubectl`, and Helm. |
| **Docker Desktop** | Provides the local container environment. Windows explicitly uses the Docker driver with WSL 2; macOS starts Docker before Minikube but does not explicitly select a driver. |
| **Minikube / Kubernetes** | Hosts local sandbox resources. Windows setup requests 2 CPUs and 4 GB RAM; macOS uses Minikube's configured defaults. |
| **`stars` namespace** | Groups project Kubernetes resources. |
| **OpenObserve** | Installed using the `openobserve/openobserve-standalone` Helm chart, with release name `openobserve`. Provides the intended central observability interface and telemetry destination. |
| **Sample applications** | The `apps/` directory is designated for sample workloads and telemetry generation; actual deployed applications still need confirmation. |
| **Telemetry collection** | The `observability/` directory is designated for OpenObserve and collector configuration; active collectors and data flows still need confirmation. |
| **AI and automation** | Planned capabilities for anomaly detection, investigation, root-cause analysis, and safe remediation; not established as working components by the supplied infrastructure setup. |

## Current Setup and Access

The repository includes two setup scripts:

- **Windows:** [`infrastructure/setup-windows.ps1`](../../infrastructure/setup-windows.ps1) sets up WSL 2 / Docker Desktop, starts Minikube with the Docker driver, and uses Helm to install or upgrade OpenObserve in `stars`.
- **macOS:** [`infrastructure/macsetup.sh`](../../infrastructure/macsetup.sh) installs missing tools, starts Docker and Minikube, creates `stars`, and installs OpenObserve with Helm.

Both scripts use a local file, `observability/values.local.yaml`, for OpenObserve login configuration. **Do not commit credentials or this local values file.**

The documented access method is a local port-forward:

```bash
kubectl --context=minikube --namespace=stars port-forward svc/openobserve-openobserve-standalone 5080:5080
```

With port-forwarding running, open <http://localhost:5080>. This local URL does not indicate that OpenObserve is publicly exposed.

For installation steps and known setup issues, see the [local setup guide](../onboarding/local-setup.md) and [infrastructure setup instructions](../../infrastructure/SETUP.md).

## Repository Areas

| Directory | Responsibility |
| --- | --- |
| [`infrastructure/`](../../infrastructure/README.md) | Local cluster setup, namespaces, and infrastructure configuration. |
| [`apps/`](../../apps/README.md) | Sample applications and telemetry-generating workloads. |
| [`observability/`](../../observability/README.md) | OpenObserve setup and telemetry collection. |
| [`automation/`](../../automation/) | Future investigation and controlled remediation implementation. |
| [`docs/`](../README.md) | Cross-system architecture, onboarding, operational documentation, and release guidance. |

Component-specific instructions should remain near their code or configuration. Cross-system explanations belong under `docs/`.

## Project Direction

The repository describes the intended development flow as:

```text
Sandbox (Minikube) --> Sample Apps --> OpenObserve --> AI Detection --> Auto-Fix
```

The **near-term integration goal** is to make the sandbox, sample applications, and OpenObserve work together reliably. The larger capstone plan adds logs, metrics, and traces; dashboards and alerts; AI-assisted anomaly detection and root-cause analysis; and controlled remediation with approval and rollback safeguards.

These later stages are **project goals, not confirmed current functionality**. The sandbox is for development and testing, not autonomous changes to STARS production systems.

## Items to Verify Before Approval

The Architecture Lead and relevant sub-leads should confirm:

- Which sample applications and telemetry collectors are actually deployed, and whether data reaches OpenObserve.
- The active OpenObserve storage and persistence configuration.
- Any additional service endpoints, networking, dashboards, or alerting that are already working.
- Whether both setup scripts reliably reproduce the expected environment on supported computers.
- Which AI, investigation, or remediation components, if any, have moved beyond planning.

Update this overview when those items are verified; keep detailed deployment and topology information in the [infrastructure architecture document](infrastructure-architecture.md).

## Related Documents

- [Infrastructure architecture](infrastructure-architecture.md) — local cluster design and implementation details.
- [Local setup guide](../onboarding/local-setup.md) — onboarding and prerequisites.
- [Infrastructure setup instructions](../../infrastructure/SETUP.md) — platform-specific scripts and commands.
- [Repository README](../../README.md) — project goals and repository layout.
- [Documentation index](../README.md) — other project documentation.
- [Observability installation guide](../../observability/install.md) — OpenObserve installation details.
