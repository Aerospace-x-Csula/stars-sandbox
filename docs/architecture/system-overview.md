# STARS Sandbox System Overview

> **Status:** Draft. This document describes the current high-level project architecture and will be updated as implementation decisions are finalized.

## Purpose

The STARS sandbox is a local, reproducible environment for developing and evaluating the STARS AI-Powered Observability Platform.

The project is intended to progress from local infrastructure and sample applications to observability, AI-assisted detection and investigation, and controlled remediation.

## Current High-Level Flow

```text
Local Developer Workstation
          |
          v
        Docker
          |
          v
       Minikube
          |
          v
 Kubernetes Sandbox
          |
          +--> Sample Applications
          |
          +--> OpenObserve
          |
          +--> Telemetry Collection
          |
          v
   Future AI Detection / RCA
          |
          v
 Controlled Remediation
