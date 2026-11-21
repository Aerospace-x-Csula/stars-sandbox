# STARS Development Prerequisites:

## Purpose
This document provides new STARS team members with a checklist of the project access and software required before beginning local development setup.

## Required Access
### GitHub Organization and Repository Access
Confirm access to the following project resources:

- the Aerospace-x-Csula GitHub organization
- the stars-sandbox repository

Access the STARS task/project board to view and track assigned work.

## Required Software
- Git - Used to clone and manage the STARS repository.
- Docker or Docker Desktop - Required for the local Minikube setup.
- Minikube - Used to run the local Kubernetes cluster.
- kubectl - Used to interact with Kubernetes.
- Helm - Used to install and manage Kubernetes applications.

## Verify Your Tools/Commands
Open PowerShell or a terminal and run the following commands:

```
git --version
docker --version
minikube version
kubectl version --client
helm version
```

These commands display version information and check that the tools are available from your terminal.


## Recommended Background
New team members can refer to the project documentation and contribution guidelines while becoming familiar with the STARS Sandbox.

## Next Step
After confirming the required software and project access, continue to the [Local Development Setup](local-setup.md) guide.

## Related Documentation
[STARS Project Documentation](../README.md) - Browse the project's technical, onboarding, and release documentation.

[Contributing Guidelines](../../CONTRIBUTING.md) - Learn how to contribute changes and follow the team's workflow.

[Infrastructure Documentation](../../infrastructure/README.md) - Understand the infrastructure environment.

[Observability Documentation](../../observability/README.md) - Learn about monitoring and telemetry.

[OpenObserve Local Installation](../../observability/install.md) - Follow the OpenObserve installation process.
