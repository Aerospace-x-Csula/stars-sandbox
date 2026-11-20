# STARS Sandbox

Sandbox environment for the **STARS AI-Powered Observability Platform**, a CSULA Senior Design project in collaboration with The Aerospace Corporation.

## What we're building

The project follows this high-level flow:

```text
Generate → Observe → Detect → Explain → Heal
```

The sandbox is designed to generate realistic application activity and failures, collect logs/metrics/traces in OpenObserve, evaluate AI-assisted monitoring techniques, and safely automate approved remediation actions.

## Current Project State

The Fall 2026 implementation includes:

- Local Kubernetes development using Minikube
- A multi-node K3s testing environment
- Log, metric, trace, and traffic generators
- Failure scenarios and automated telemetry validation
- OpenTelemetry collection
- OpenObserve deployment and dashboards
- AI/ML prototypes for:
  - anomaly detection
  - resource forecasting
  - alert grouping
  - log-pattern detection
- A low-risk local self-healing prototype with guardrails and audit output

The full root-cause-analysis and expanded self-healing workflow is still in development.

## Repo Layout

| Folder | What goes here |
|---|---|
| `infrastructure/` | Local and VM-based Kubernetes setup and infrastructure configuration |
| `apps/` | Sample applications, telemetry generators, traffic generation, failure scenarios, and tests |
| `observability/` | OpenObserve, OpenTelemetry collectors, dashboards, and observability configuration |
| `ai/` | Anomaly detection, forecasting, alert grouping, and AI/ML experiments |
| `automation/` | Self-healing and remediation development |
| `docs/` | Architecture, onboarding, runbooks, project documentation, and release guidance |

## Getting Started

1. Read [CONTRIBUTING.md](CONTRIBUTING.md).
2. Clone this repository:

   ```bash
   git clone https://github.com/Aerospace-x-Csula/stars-sandbox.git
   ```

3. Enter the repository:

   ```bash
   cd stars-sandbox
   ```

4. Follow the [local setup guide](docs/onboarding/local-setup.md).
5. Review the [documentation index](docs/README.md).
6. Check the **STARS Tasks** board for your assigned task.

## Documentation

The main project documentation index is:

[docs/README.md](docs/README.md)

Useful starting points:

- [System Overview](docs/architecture/system-overview.md)
- [Infrastructure Architecture](docs/architecture/infrastructure-architecture.md)
- [Local Setup Guide](docs/onboarding/local-setup.md)
- [Common Setup Errors](docs/onboarding/common-setup-errors.md)
- [Documentation Status](docs/project/documentation-status.md)
- [Runbooks](docs/runbooks/README.md)
- [Release Checklist](docs/release/release-checklist.md)

## How We Work

- **Tasks** live on the STARS Tasks project board, one issue per task.
- **Every repeatable step should work outside the original developer's machine.** If only one person can reproduce it, the work is not finished.
- **Commits** use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`.
- **Link work to its issue:** `Refs #3` or `Closes #3`.
- **Use small pull requests** so changes are easier to review and integrate.
- **Do not push directly to `main`.**
- **Do not commit passwords, tokens, or other real credentials.**
- **Stuck?** Comment on the issue or post in Slack.

## Project Direction

The project is progressing from the sandbox and baseline observability foundation toward:

```text
AI Monitoring
     ↓
Root-Cause Analysis
     ↓
Expanded Self-Healing
     ↓
Advanced Features
     ↓
Hardening and Final Release
```

The repository represents a development and testing sandbox. It is not a production STARS deployment.
