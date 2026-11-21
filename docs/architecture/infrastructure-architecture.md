# STARS Sandbox Infrastructure Architecture

> **Status:** Updated Draft - reflects the Fall 2026 infrastructure demonstrated by the project team. Technical review by the Infrastructure Sub-Lead is recommended before final approval.
>
> **Scope:** Development and testing infrastructure for the STARS student sandbox. This document does **not** describe a production STARS environment.

## Purpose

This document explains how the current STARS sandbox infrastructure is organized and how the project's major development environments support the application, observability, AI, testing, and automation workstreams.

The project currently uses two main Kubernetes environments:

1. **Local Minikube environments** for individual development and testing.
2. **A private multi-node K3s VM environment** for shared/multi-node infrastructure testing.

Cloud deployment is a later project goal.

For setup instructions, use the [local setup guide](../onboarding/local-setup.md), [`infrastructure/README.md`](../../infrastructure/README.md), and [`infrastructure/SETUP.md`](../../infrastructure/SETUP.md).

---

## Environment Overview

```text
                     STARS Development Environments
                                |
                 +--------------+--------------+
                 |                             |
                 v                             v
       Local Developer Sandbox         Multi-Node Test Environment
                 |                             |
        Docker + Minikube             Private School VM Network
                 |                             |
        Kubernetes cluster                  K3s
                 |                             |
        namespace: stars             stars1 - control plane
                 |                   stars2 - worker
                 |                   stars3 - worker
                 |                   stars4 - worker
                 |
       Project workloads
```

The two environments serve different purposes.

- **Minikube** provides a lightweight environment that each student can run locally.
- **K3s on school/private VMs** provides a more representative multi-node Kubernetes environment for integration and scaling work.

---

## 1. Local Developer Environment

The local sandbox is the primary individual development environment.

The repository supports development across the operating systems used by the team and contains platform-specific infrastructure setup scripts.

Relevant files include:

```text
infrastructure/
├── README.md
├── SETUP.md
├── macsetup.sh
├── setup-ubuntu.sh
└── setup-windows.ps1
```

The local environment uses:

- Git,
- Docker / Docker Desktop,
- Minikube,
- Kubernetes,
- `kubectl`,
- Helm, and
- OpenObserve.

The project's Kubernetes resources primarily use the namespace:

```text
stars
```

---

## 2. Local Minikube Architecture

A developer laptop runs the sandbox through Docker and Minikube.

```text
Developer Laptop
|
+-- Git / stars-sandbox repository
|
+-- Docker
|    |
|    `-- Minikube
|         |
|         `-- Kubernetes cluster
|              |
|              +-- namespace: stars
|              |    |
|              |    +-- Data/Test workloads
|              |    +-- OpenObserve
|              |    `-- other project resources
|              |
|              `-- OpenTelemetry Collector resources
|
+-- kubectl
|
`-- Helm
```

This environment allows a student to develop, deploy, observe, and test project components without accessing a production STARS environment.

---

## 3. Current Local Workloads

The current development architecture includes several workloads used to generate and validate telemetry.

### Data/Test Workloads

Current repository components include:

| Component | Kubernetes form / purpose |
| --- | --- |
| **Log Generator** | Deployment that produces heartbeat, warning, error, and failure-scenario logs. |
| **Synthetic Metrics** | Deployment that produces CPU and memory telemetry, including controlled anomalies. |
| **Trace Generator** | Job that produces OpenTelemetry traces for simulated distributed requests. |
| **Locust** | Deployment/jobs used to generate repeatable application traffic and load scenarios. |
| **STARS Test App** | Application target used by Locust traffic generation. |
| **Telemetry Tests** | pytest-based validation executed from the development environment. |

The exact running resource set depends on which components a developer has deployed.

---

## 4. Telemetry Collection Architecture

The local sandbox uses an OpenTelemetry collector to move supported telemetry toward OpenObserve.

A simplified architecture is:

```text
Trace Generator
      |
      | OTLP traces
      v
+---------------------------+
| OpenTelemetry Collector   |
|                           |
| Gateway                   |
| Agent                     |
+-------------+-------------+
              |
              v
         OpenObserve
```

Container-generated logs from project applications can be read by the collector and forwarded toward the collector gateway/OpenObserve path.

The trace generator sends OTLP trace data through the collector gateway.

Locust also generates traffic against the test application and can provide result data for observability/testing workflows.

---

## 5. OpenObserve

OpenObserve is the central observability backend for the sandbox.

It is deployed into Kubernetes using Helm.

The local development environment exposes the OpenObserve web interface through port forwarding.

The standard local access endpoint is:

```text
http://localhost:5080
```

A typical port-forward command is:

```bash
kubectl --namespace stars port-forward svc/openobserve-openobserve-standalone 5080:5080
```

While the command is running, the browser can access OpenObserve on the local workstation.

OpenObserve is not publicly exposed simply because it is reachable through `localhost`.

---

## 6. Current Telemetry and Observability Flow

The current local architecture can be represented as:

```text
+-------------------------+
| Data/Test Workloads     |
|                         |
| log-generator           |
| synthetic-metrics       |
| trace-generator         |
| Locust                  |
| stars-app               |
+------------+------------+
             |
             | logs / traces / workload activity
             v
+-------------------------+
| OpenTelemetry Collector |
|                         |
| Agent + Gateway         |
+------------+------------+
             |
             v
+-------------------------+
| OpenObserve             |
|                         |
| Logs                    |
| Traces                  |
| Kubernetes events       |
| Locust result streams   |
| Dashboards              |
+------------+------------+
             |
             v
+-------------------------+
| Browser / Team          |
|                         |
| Search                  |
| Dashboards              |
| Validation              |
+-------------------------+
```

Automated telemetry tests are used to verify that expected data reaches the observability platform.

The project has demonstrated generated logs being collected, ingested into OpenObserve, searched, and monitored through dashboards.

---

## 7. Multi-Node K3s Testing Environment

In addition to the local Minikube environment, the Infrastructure team has established a private VM-based multi-node K3s testing environment.

The documented topology is:

```text
                     STARS Team
                         |
                  SSH / kubectl / Helm
                         |
                         v
             Private School VM Network
                         |
                         v
                 K3s Cluster
                         |
              +----------+----------+
              |          |          |
              |          |          |
           stars2     stars3     stars4
           worker     worker     worker
              \          |          /
               \         |         /
                    stars1
                control plane
```

More simply:

| Node | Role |
| --- | --- |
| `stars1` | K3s control plane |
| `stars2` | K3s worker |
| `stars3` | K3s worker |
| `stars4` | K3s worker |

The environment exists to provide a multi-node test platform beyond a single developer laptop.

The presentation describes the team accessing the environment through SSH and then using Kubernetes tooling such as `kubectl` or Helm.

### Important Scope Note

The existence of the K3s cluster does **not** mean that every workload currently running in Minikube has been fully validated on the multi-node K3s environment.

Deployment parity between local Minikube and the K3s environment should be documented as each component is tested there.

---

## 8. Linux / VM Setup Automation

The Infrastructure workstream has developed a streamlined Linux setup process for the VM environment.

The Fall 2026 project presentation reports that this setup handles tasks including:

- user credential setup for Git and OpenObserve,
- Git installation,
- Helm installation,
- K3s-related setup,
- OpenObserve setup, and
- Docker installation.

The repository contains:

```text
infrastructure/setup-ubuntu.sh
```

Detailed behavior should remain documented in the Infrastructure team's setup documentation rather than duplicated here.

---

## 9. Networking and Service Access

### Local Minikube

Local development primarily relies on Kubernetes networking plus local port forwarding.

OpenObserve:

```text
localhost:5080
```

Locust may expose its local user interface separately when deployed.

Internal Kubernetes Services allow workloads to communicate inside the cluster.

### K3s VM Environment

The multi-node environment operates on a private VM network.

The team accesses the environment through the approved VM access path and then manages Kubernetes using normal K3s/Kubernetes tools.

This document does not assume that K3s services are publicly exposed.

---

## 10. Namespace Organization

The main STARS sandbox namespace is:

```text
stars
```

It contains many of the project's application and observability workloads.

The Data/Test architecture also uses collector resources associated with an OpenTelemetry collector deployment.

Namespace placement should continue to be documented in the component-specific deployment files and guides because it may evolve as the environment is hardened.

---

## 11. Storage and Configuration

Project-local configuration includes Git-ignored credentials and values files where appropriate.

For example:

```text
observability/values.local.yaml
```

must remain local and must not be committed to Git.

This document does **not** currently define a guaranteed persistence, backup, or disaster-recovery architecture for OpenObserve.

Before documenting storage as production-like, the team should confirm:

- active Kubernetes volumes,
- StorageClasses,
- OpenObserve persistence configuration,
- retention behavior,
- backup procedures, and
- recovery behavior.

---

## 12. Infrastructure Dependencies

The current local environment has the following major dependency chain:

```text
Developer workstation
        |
        v
Docker
        |
        v
Minikube
        |
        v
Kubernetes
        |
        +--> Data/Test workloads
        |
        +--> OpenTelemetry Collector
        |
        `--> OpenObserve
```

The observability pipeline additionally depends on:

```text
Telemetry-producing workload
        |
        v
Collector / ingestion path
        |
        v
OpenObserve
        |
        v
Search / dashboard / validation
```

AI/ML experiments depend on telemetry or datasets produced by the sandbox.

The low-risk automation prototype depends on Kubernetes workload state but should be considered a separate controlled remediation component rather than a general cluster administrator.

---

## 13. Current Infrastructure State

### Implemented / Demonstrated

Current infrastructure work includes:

- local Minikube setup,
- Windows/macOS/local development support,
- Linux VM setup automation,
- Kubernetes namespace setup,
- OpenObserve deployment,
- Helm-based deployment workflows,
- private multi-node K3s testing environment,
- sample application workloads,
- telemetry-generating workloads,
- OpenTelemetry collection,
- OpenObserve ingestion, and
- local end-to-end validation.

### Still In Progress or Future

The following should not yet be described as completed production infrastructure:

- complete workload parity between Minikube and K3s,
- cloud deployment,
- production-grade high availability,
- final persistent-storage architecture,
- formal backup/recovery implementation,
- production networking,
- complete security hardening,
- final release deployment architecture, and
- production STARS integration.

---

## 14. Environment Roadmap

The current environment progression is:

```text
Individual Development
Minikube on developer laptops
        |
        v
Multi-Node Integration Testing
School/private VMs using K3s
        |
        v
Future Environment
Cloud / broader deployment evaluation
```

This progression allows the team to develop features locally before validating them in a more representative multi-node environment.

---

## 15. Relationship to Other Workstreams

Infrastructure provides the execution environment for the rest of the project.

```text
Infrastructure
     |
     +--> Data/Test workloads
     |
     +--> Observability
     |
     +--> AI/ML experiments
     |
     `--> Automation & Self-Healing
```

The infrastructure architecture therefore supports, but does not itself define, the internal design of those workstreams.

Detailed component behavior belongs in each component's own documentation.

---

## Current Limitations and Items to Confirm

Before marking this architecture document final, the Infrastructure Sub-Lead should confirm:

- the current supported operating systems for local setup,
- whether all four K3s VM nodes remain part of the active test environment,
- which project workloads have been validated on the K3s cluster,
- whether local and K3s deployment procedures are intended to remain equivalent,
- the current storage/persistence configuration,
- backup and recovery expectations,
- any additional networking or service-access configuration,
- current resource sizing for the VM environment, and
- whether any infrastructure changes have occurred since the Fall 2026 presentation.

These confirmations are especially important for the preliminary Software Design Document.

---

## Related Documentation

- [System Overview](system-overview.md) - high-level architecture and project-component relationships.
- [Local Setup Guide](../onboarding/local-setup.md) - local developer onboarding.
- [Common Setup Errors](../onboarding/common-setup-errors.md) - known local setup problems.
- [Infrastructure README](../../infrastructure/README.md) - infrastructure workstream guidance.
- [Infrastructure Setup](../../infrastructure/SETUP.md) - setup instructions and scripts.
- [Applications README](../../apps/README.md) - sample applications and telemetry generation.
- [Observability README](../../observability/README.md) - OpenObserve and collector documentation.
- [AI README](../../ai/README.md) - AI/ML prototypes and experiments.
- [Automation README](../../automation/README.md) - remediation and local-healer documentation.

---

**Review status:** Updated by Documentation & Release using the current repository structure and Fall 2026 project presentation. Infrastructure Sub-Lead technical confirmation is recommended before this document is marked final.
