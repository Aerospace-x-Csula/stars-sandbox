# STARS Project Documentation

This directory contains the cross-system technical, onboarding, operational, project, and release documentation for the **STARS AI-Powered Observability Platform** sandbox.

Documentation is maintained alongside the source code so that it can evolve with the implementation it describes.

Component-specific technical instructions remain near the component itself, while cross-system documentation belongs under `docs/`.

---

## Start Here

New team members should begin with:

1. [Local Development Setup](onboarding/local-setup.md)
2. [Repository Contribution Guide](../CONTRIBUTING.md)
3. [Team Roles](project/team-roles.md)
4. [System Overview](architecture/system-overview.md)
5. [Infrastructure Architecture](architecture/infrastructure-architecture.md)

If you run into setup problems, see:

- [Common Setup Errors](onboarding/common-setup-errors.md)

For help with GitHub pull requests:

- [Pull Request Guide](onboarding/pull-request-guide.md)

---

## Architecture

- [System Overview](architecture/system-overview.md)  
  High-level view of the current STARS sandbox, telemetry flow, AI/ML components, and automation work.

- [Infrastructure Architecture](architecture/infrastructure-architecture.md)  
  Current local Minikube and multi-node K3s infrastructure environments.

Architecture documentation should describe the system as it currently exists and clearly separate implemented functionality from planned work.

---

## Onboarding

- [Local Development Setup](onboarding/local-setup.md)
- [Common Setup Errors](onboarding/common-setup-errors.md)
- [Pull Request Guide](onboarding/pull-request-guide.md)

Onboarding documentation should allow a new student to understand the development workflow and reproduce the supported sandbox setup without depending on undocumented steps.

---

## Component Documentation

Technical documentation that belongs to a specific implementation area remains near that component.

### Infrastructure

- [Infrastructure README](../infrastructure/README.md)
- [Infrastructure Setup](../infrastructure/SETUP.md)

### Applications / Data-Test Engineering

- [Applications README](../apps/README.md)

The `apps/` area includes telemetry generators, Locust traffic generation, failure scenarios, and automated telemetry validation.

### Observability

- [Observability README](../observability/README.md)
- [OpenObserve Installation](../observability/install.md)
- [Collector Guide](../observability/collector.md)
- [OpenObserve Enterprise Guide](../observability/openobserve-enterprise-guide.md)
- [OpenObserve In-Place Enterprise Upgrade](../observability/openobserve-in-place-enterprise-upgrade.md)

### AI / ML

- [AI README](../ai/README.md)

The AI area currently contains work related to anomaly detection, forecasting, alert grouping, and related experiments.

### Automation & Self-Healing

- [Automation README](../automation/README.md)

The Automation area contains the low-risk local-healer prototype and related remediation work.

---

## Architecture Decisions

- [Architecture Decision Records](decisions/README.md)
- [ADR Template](decisions/ADR-template.md)

Architecture Decision Records should be used when the team makes an important technical decision that future team members may need to understand.

---

## Operator Runbooks

- [Runbook Index](runbooks/README.md)
- [Runbook Template](runbooks/runbook-template.md)

The runbook framework is established.

Incident-specific runbooks should be added as failure scenarios and remediation workflows become stable enough to test end-to-end.

Each operational runbook should eventually address:

- detection,
- investigation,
- evidence collection,
- remediation,
- validation,
- rollback, and
- escalation.

---

## Project Documentation

- [Team Roles](project/team-roles.md)
- [Documentation Status](project/documentation-status.md)

Additional project-level documentation, including the Software Requirements Document (SRD) and preliminary Software Design Document (SDD), will be added as those deliverables are completed.

---

## Release

- [Release Checklist](release/release-checklist.md)

The release documentation will expand as the project approaches a reproducible production-evaluation package.

Later release documentation is expected to include items such as:

- deployment instructions,
- rollback instructions,
- known limitations,
- versioned configuration,
- release notes, and
- final handoff material.

---

## Documentation Rules

- Keep the repository root `README.md` concise.
- Put cross-system documentation under `docs/`.
- Keep component-specific technical instructions near the component they describe.
- Link to authoritative instructions instead of duplicating the same procedure in multiple files.
- Describe current functionality accurately and label future functionality as planned.
- Do not invent technical details when implementation is unclear.
- Have the relevant technical workstream verify technical content.
- Test commands before marking procedural documentation as verified.
- Never place passwords, tokens, or other real secrets in documentation.
- Update documentation when a technical change makes existing instructions inaccurate.
- Prefer small, reviewable documentation pull requests.

---

## Documentation Ownership

Documentation & Release maintains the project documentation structure, cross-system documentation, onboarding material, operational documentation, and release documentation.

Technical workstream owners are responsible for validating technical details related to their components.

The documentation team owns clarity, consistency, organization, and knowledge transfer; technical teams own the correctness of component-specific engineering details.
