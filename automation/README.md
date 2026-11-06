# Automation

Self-healing scripts, failure injection steps, and remediation guardrails
## Purpose
The automation directory contains tools and Kubernetes resources used to test failure scenarios and automated recovery behavior in the STARS Sandbox project.
It currently includes an intentionally crashing Kubernetes deployment and a Python-based local healer that monitors selected pods and attempts recovery when unhealthy pods are detected.

## Ownership
This directory is maintained by the Automation & Self-Healing team. Angel Hurtado (sub-lead), Moises De Arcos, Jonas Mendoza, Jayden Darling.

## Directory Contents

[crash-deployment.yaml](crash-deployment.yaml): Defines a Kubernetes Deployment whose container intentionally exits with an error on startup.

[crash-deployment.md](crash-deployment.md): Explains how to apply, monitor, and remove the crash deployment.

[local-healer](local_healer/): Contains the Python self-healing script, its dependencies, and its component-specific README.

# Usage

## Automation Workflow Diagram
[View Automation Diagram (PDF)](Automation_Diagram.pdf)

## Crash Deployment
The crash deployment tests how Kubernetes handles a container that repeatedly exits with an error. It can be applied to a cluster and monitored through pod status and restart behavior.
The [Crash Deployment Guide](crash-deployment.md) has the commands, expected behavior, and cleanup instructions. 

## Local Healer
The local healer also tracks recovery attempts by application and namespace. It limits healing attempts within a time window and can block further automated recovery when that limit is reached. These safeguards are intended to prevent repeated automated actions from continuing indefinitely. Installation, dependencies, and launch instructions are available in the [Local Healer README](local-healer/README.md).

# Verification 
Verification should confirm that each component behaves as documented, rather than simply confirming that its commands execute without errors.

## Crash Deployment
After applying the deployment, run the following command from the repository root to inspect pod status. 

    kubectl get pods

The container is expected to fail repeatedly, and the pod should eventually enter CrashLoopBackOff. The [Crash Deployment Guide](crash-deployment.md) explains how to observe its restart behavior.

# Removal and Shutdown

## Crash Deployment
Cleanup instructions are available in the [Crash Deployment Guide](crash-deployment.md).

## Additional Documentation
- [Crash Deployment Guide](crash-deployment.md) - Instructions for applying, monitoring, and removing the crash deployment.
- [Local Healer README](local-healer/README.md) -  Prerequisites, installation, dependencies, and usage.
- [CONTRIBUTING.md](../CONTRIBUTING.md) - repository conventions, ownership, documentation requirements, and contribution workflow.
