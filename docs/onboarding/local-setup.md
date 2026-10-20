# Local Development Setup

> **Status:** Draft. This guide covers the local workstation and base Minikube setup currently used by the STARS sandbox. It should be verified on a clean machine before being considered complete onboarding documentation.

This guide prepares a student workstation to work with the STARS AI-Powered Observability Platform sandbox.

For repository contribution rules, read [`CONTRIBUTING.md`](../../CONTRIBUTING.md) before making changes.

---

## 1. Required Access

Before starting, make sure you have:

- Access to the Aerospace-x-Csula GitHub organization
- Access to the `stars-sandbox` repository
- Access to the STARS task/project board used by the team

If you cannot open the repository or project board, contact the project lead before continuing.

---

## 2. Required Software

Install the following tools:

- Git
- Docker or Docker Desktop
- Minikube
- kubectl
- Helm

You can verify the installed command-line tools with:

```bash
git --version
docker --version
minikube version
kubectl version --client
helm version
