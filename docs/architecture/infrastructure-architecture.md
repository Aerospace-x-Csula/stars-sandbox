# STARS Sandbox Infrastructure Architecture

> **Status:** Draft — pending technical review by the Infrastructure Sub-Lead.
> **Scope:** The local development sandbox described by the repository documentation and setup scripts. This is **not** a description of a deployed production STARS environment. Actual cluster state and any undocumented components still need to be confirmed.

## Purpose

This document explains how the current STARS sandbox infrastructure fits together so that a new student can understand the development environment, the Kubernetes cluster, and how the project components connect. It describes what the repository currently documents or provisions, rather than treating the project's longer-term goals as completed work.

For installation steps, use the [local setup guide](../onboarding/local-setup.md) and [infrastructure setup instructions](../../infrastructure/SETUP.md) rather than this architecture overview.

## Current Environment

The STARS sandbox is designed to run locally on a student's computer. Docker provides the container environment used by Minikube, which starts a local Kubernetes cluster. Kubernetes hosts sandbox workloads; Helm is used to install OpenObserve into the `stars` namespace.

```text
Student workstation (Windows or macOS)
  |-- Git and stars-sandbox repository
  |-- Docker Desktop (container engine)
  |     `-- Minikube (local Kubernetes cluster)
  |           `-- Kubernetes namespace: stars
  |                 `-- OpenObserve (Helm release: openobserve)
  |                       `-- Kubernetes Service: openobserve-openobserve-standalone
  `-- kubectl / Helm
        `-- local port-forward to OpenObserve at http://localhost:5080

Sample applications and telemetry collection:
  repository areas exist; exact deployed workloads and telemetry paths
  require confirmation before they can be shown as live components.
```

This is a **per-developer local sandbox**, not a confirmed shared or production cluster. The diagram illustrates the supported setup path, not a live inventory of all running Pods.

## Developer Workstation

The workstation is where a student clones the repository, runs the setup scripts, manages Minikube, and accesses OpenObserve through a web browser. The documented tools are Git, Docker Desktop, Minikube, `kubectl`, and Helm.

- **Windows:** The setup script uses Docker Desktop's WSL 2 Linux-container backend, without requiring an Ubuntu distribution. It starts Minikube with the Docker driver, **2 CPUs**, and **4 GB of memory**.
- **macOS:** The setup script installs missing tools with Homebrew, starts Docker Desktop, then runs `minikube start` with Minikube's configured defaults; no fixed CPU or memory allocation is specified in that script. It clones or reuses `~/stars-sandbox`.

The scripts are located at [`infrastructure/setup-windows.ps1`](../../infrastructure/setup-windows.ps1) and [`infrastructure/macsetup.sh`](../../infrastructure/macsetup.sh). See [`infrastructure/SETUP.md`](../../infrastructure/SETUP.md) for operating-system-specific instructions.

## Docker

Docker Desktop provides the local Linux container engine used by the documented Minikube setup. On Windows, the setup script explicitly selects the WSL 2 backend and starts Minikube with `--driver=docker`. On macOS, the setup script starts Docker Desktop before starting Minikube, but does not explicitly pass a Minikube driver flag.

Docker is therefore a dependency for the documented setup. The repository materials reviewed do **not** establish a separate Docker Compose application stack or a documented custom image-build pipeline.

## Minikube and Kubernetes Cluster

Minikube provides the local Kubernetes environment. Students use `kubectl` to inspect nodes, namespaces, Pods, and Services, and use Helm to manage the documented OpenObserve installation.

The setup scripts demonstrate a local cluster with a Minikube node and wait for node or Pod readiness. They do not establish a multi-node topology, separate worker-node pool, external load balancer, or production-grade high-availability configuration.

Useful inspection commands (run against your own sandbox):

```bash
minikube status
kubectl --context=minikube get nodes
kubectl --context=minikube get namespaces
kubectl --context=minikube -n stars get pods,services
helm --kube-context minikube -n stars list
```

These commands inspect the *current* running environment; successful cluster startup alone does not prove that every application or telemetry pipeline is healthy.

## `stars` Namespace

The project convention is to place STARS sandbox resources in the Kubernetes namespace named `stars`. The Windows setup script creates this namespace through Helm's `--create-namespace` option. The macOS script uses `kubectl create namespace stars` before installing OpenObserve.

`stars` is a logical separation within the local Kubernetes cluster. It is **not** a separate cluster. Other Kubernetes system namespaces may also exist, but their exact resources are not inventoried here.

## Current Workloads and Components

| Component | Current documented state | Role |
| --- | --- | --- |
| Minikube Kubernetes cluster | Started by both platform setup scripts | Runs local Kubernetes resources. |
| `stars` namespace | Created by setup scripts | Groups project workloads in Kubernetes. |
| OpenObserve | Installed by Helm as release `openobserve` using chart `openobserve/openobserve-standalone` | Local observability interface and intended telemetry destination. |
| OpenObserve Service | Referenced as `svc/openobserve-openobserve-standalone` | Target for local `kubectl port-forward`. |
| Sample applications | [`apps/`](../../apps/README.md) is the designated repository area; deployed applications are **not confirmed** by the supplied infrastructure scripts | Intended to simulate application behavior and generate telemetry. |
| Telemetry collectors/agents | [`observability/`](../../observability/README.md) is the designated repository area; deployed collectors and ingestion paths are **not confirmed** by the supplied infrastructure scripts | Intended to send logs, metrics, and/or traces to OpenObserve. |

OpenObserve's installation is supported by the checked setup-script text, but a successful installation on every developer machine has **not** been independently verified. The actual Pods and Services must be checked in a running cluster. A Helm release alone is not evidence that applications are sending telemetry.

## Networking and Service Access

The documented way to access OpenObserve is a **local Kubernetes port-forward**:

```bash
kubectl --context=minikube --namespace=stars port-forward svc/openobserve-openobserve-standalone 5080:5080
```

While this command is running, the student accesses the OpenObserve web interface at <http://localhost:5080>. Stopping the command stops this local access path. The Windows script tells the user to start port-forwarding after setup; the macOS script starts it at the end of setup.

No repository evidence reviewed for this draft confirms an Ingress controller, public DNS name, externally exposed application endpoint, or cross-workstation access. Internal application-to-application networking and telemetry transport should be added only after verification.

## Storage and Local Configuration

The setup scripts create or use a **local, Git-ignored** file at `observability/values.local.yaml` for OpenObserve Helm authentication values. This file is workstation-specific configuration, **not** a shared database or documented backup. Do not commit it or copy credentials into documentation.

The available setup materials do not specify OpenObserve's active Kubernetes volume type, StorageClass, persistence settings, retention period, backup process, or data recovery guarantees. These details must be verified against the installed Helm release and live Kubernetes resources before this document describes persistent storage.

Stopping Minikube with `minikube stop` is distinct from deleting the cluster with `minikube delete`. The latter removes cluster-managed resources and may remove data stored only within the cluster; do not assume stored telemetry survives deletion.

## Current Dependencies

The documented startup and access relationships are:

1. The student workstation runs Docker Desktop.
2. Minikube depends on a functioning local container environment (explicit Docker driver on Windows).
3. Kubernetes must be reachable before the `stars` namespace and OpenObserve Helm release can be created.
4. The OpenObserve Service and a running port-forward are required for the documented browser access at `localhost:5080`.
5. Sample applications and collectors are intended to integrate with this cluster and OpenObserve, but their actual deployment and telemetry connections remain unverified.

## Current Limitations and Items to Confirm

This is a first-draft description of the **documented setup**, not a full infrastructure audit. Before removing this draft status, confirm with the Infrastructure Sub-Lead:

- Which workloads (including sample apps and collectors) are *actually running* in `stars`, and their Kubernetes resource names.
- Whether macOS Minikube consistently uses the Docker driver and what resource allocation is expected.
- Whether OpenObserve uses persistent storage, which volume/StorageClass is used (if any), and what happens to telemetry after restarts or cluster deletion.
- Whether there are additional network access methods, internal application dependencies, or configured telemetry endpoints.
- Whether the scripts represent the currently supported, repeatable setup on both operating systems, including any known rerun/installation issues.

Until confirmed, do not assume multi-node operation, managed VMs, production networking, automatic backups, complete telemetry collection, or recovery automation.

## Planned Infrastructure (Not Current)

The project outline describes possible later work such as representative VMs, richer networking/storage design, sample application dependencies, expanded collection of logs/metrics/traces, AI detection and root-cause analysis, controlled remediation, and reproducible release packaging. These are **project goals**, not verified features of today's sandbox.

The repository's immediate integration goal is **Minikube → sample applications → OpenObserve**. AI detection and automatic remediation are subsequent stages; their implementation should be documented separately as they become real.

## Related Documentation

- [Repository README](../../README.md) — project goals and repository layout.
- [Contributing guidelines](../../CONTRIBUTING.md) — naming and contribution conventions.
- [Documentation index](../README.md) — other guides.
- [System overview](system-overview.md) — high-level project architecture.
- [Local setup guide](../onboarding/local-setup.md) — onboarding and prerequisites.
- [Infrastructure README](../../infrastructure/README.md) — infrastructure team scope and verification commands.
- [Infrastructure setup instructions](../../infrastructure/SETUP.md) — Windows and macOS setup scripts and access instructions.
- [Applications README](../../apps/README.md) — sample-application area.
- [Observability README](../../observability/README.md) — observability area.

---

**Review status:** Infrastructure Sub-Lead technical confirmation pending; Documentation & Release review pending. Update this draft with verified running resources before marking it approved.
