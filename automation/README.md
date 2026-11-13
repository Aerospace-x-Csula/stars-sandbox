# Automation

Self-healing scripts, failure injection steps, and remediation guardrails
## Purpose
The automation directory contains tools and Kubernetes resources used to test failure scenarios and automated recovery behavior in the STARS Sandbox project.
It currently includes an intentionally crashing Kubernetes deployment and a Python-based local healer that monitors selected pods and attempts recovery when unhealthy pods are detected.

## Ownership
This directory is maintained by the Automation & Self-Healing team. 

## Directory Contents

[crash-deployment.yaml](crash-deployment.yaml): Defines a Kubernetes Deployment whose container intentionally exits with an error on startup.

[crash-deployment.md](crash-deployment.md): Explains how to apply, monitor, and remove the crash deployment.

[local-healer](local-healer/): Contains the Python self-healing script, its dependencies, and its component-specific README.

[Automation-Diagram.pdf](Automation-Diagram.pdf): Architecture diagram of the planned self-healing flow, from failure classification to the audit log.

# Usage

## Crash Deployment
The crash deployment tests how Kubernetes handles a container that repeatedly exits with an error. It can be applied to a cluster and monitored through pod status and restart behavior.
The [Crash Deployment Guide](crash-deployment.md) has the commands, expected behavior, and cleanup instructions. 

## Local Healer
The local healer tracks pods labeled `auto-heal=true` and deletes them so their controller recreates them. It tracks recovery attempts by application and namespace, and stops after 3 restarts within a 30 minute window so it cannot loop forever. Every action, and every time the limit
blocks one, prints an audit entry in the terminal (trigger, evidence, decision, action, result). Installation, dependencies, and launch instructions are available in the [Local Healer README](local-healer/README.md).

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

## Known limits

This is a first version for the sandbox. It restarts unhealthy pods and stops after 3 restarts in 30 minutes for the same app. 
The following are not implemented yet and are planned for the spring:

- **Checking the fix worked:** the healer does not yet confirm that a pod
  recovered after a restart (post-check).
- **Undoing a bad fix:** there is no automatic rollback to the previous
  version if a fix makes things worse.
- **Saving the action log:** actions are printed to the terminal only. Logs
  are not yet saved or sent to OpenObserve.
- **Running with limited permissions:** the healer uses the kubeconfig of
  whoever runs it. It does not yet run with a dedicated service account that
  has only the permissions it needs.

### Also planned for the spring

- Failure classification: decide whether a failure is the app or the
  infrastructure before choosing a fix.
- Pre-check: confirm it is safe to act.
- Human-in-the-loop gate: ask for approval before high or critical fixes.
- Remediation scripts for the medium to critical risk tiers.