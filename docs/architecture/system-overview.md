# STARS Sandbox System Overview

> **Status:** Draft. This document describes the current high-level project architecture and will be updated as implementation decisions are finalized.

## Purpose

The STARS sandbox is a local, reproducible environment for developing and evaluating the STARS AI-Powered Observability Platform.

The project is intended to progress from local infrastructure and sample applications to observability, AI-assisted detection and investigation, and controlled remediation.

## Current High-Level Flow

Local Developer Workstation --> Docker --> Minikube --> Kubernetes Sandbox (Sample Applications, OpenObserve, Telemetry Collection) --> Future AI Detection / RCA --> Controlled Remediation

## Current Repository Areas

- **Infrastructure:** (infrastructure/)

Owns the local cluster and sandbox infrastructure configuration.

- **Applications:** (apps/)

Contains sample applications and telemetry-generation workloads used by the sandbox.

- **Observability:** (observability/)

Contains OpenObserve and telemetry collection configuration and documentation.

- **Automation:** (automation/)

Contains automation and remediation-related implementation.

- **Documentation:** (docs/)

Contains cross-system architecture, onboarding, operational, runbook, and release documentation.

## Current Project Focus

The current repository README describes the project flow as:

Sandbox (Minikube) --> Sample Apps --> OpenObserve --> AI Detection --> Auto-Fix

The current near-term goal is to get the sandbox, sample applications, and OpenObserve working together reliably.

## Documentation Principle

Component-specific implementation documentation should remain near the component. Cross-system documentation should live under docs/.

## Planned Architecture Documentation

As implementation stabilizes, this architecture documentation should expand to cover:
- VM and Kubernetes topology
- Networking
- Storage
- Applications and dependencies
- Telemetry sources
- Collectors and agents
- OpenObserve
- Logs, metrics, and traces
- Dashboards and alerting
- AI/ML workflows
- Root-cause analysis
- Remediation workflows
- Security and RBAC
- CI/CD and release packaging

## Related Documents

- [../onboarding/local-setup.md]
- [../README.md]
- [../../observability/install.md]
