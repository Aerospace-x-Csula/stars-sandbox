# STARS Sandbox

Sandbox environment for the STARS AI-Powered Observability Platform, a CSULA Senior Design project with The Aerospace Corporation.

## What we're building

Sandbox (Minikube) → Sample Apps → OpenObserve → AI Detection → Auto-Fix

**Current goal:** the first three steps working together.

## Repo layout

| Folder | What goes here |
|---|---|
| `infrastructure/` | Cluster setup |
| `apps/` | Sample apps that generate logs |
| `observability/` | OpenObserve + collector setup |
| `automation/` | Automation and remediation |
| `docs/` | Guides and documentation |

## Getting started

1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Clone this repo:
   ```
   git clone https://github.com/Aerospace-x-Csula/stars-sandbox.git
   ```
3. Enter the repository:
   ```
   cd stars-sandbox
   ```
4. Follow the [local-setup.md](docs/onboarding/local-setup.md).
5. Check the **STARS Tasks** board for your assigned task.

## Documentation

The documentation index is available at:
[README.md](docs/README.md)

## How we work

- **Tasks** live on the STARS Tasks project board, one issue per task.
- **Every step must work on everyone's laptop.** If it only works on yours, it's not done.
- **Commits** use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`
- **Link your work** to its issue: `Refs #3` or `Closes #3`
- **Stuck?** Comment on the issue or post in Slack
