# STARS Project Documentation

This directory contains the technical, onboarding, operational, and release documentation for the STARS AI-Powered Observability Platform sandbox.

The documentation is maintained alongside the source code so that project documentation can be versioned with the implementation it describes.

---

## Start Here

New team members should begin with:

1. [Local Development Setup](onboarding/local-setup.md)
2. [Repository Contribution Guide](../CONTRIBUTING.md)
3. [Team Roles](project/team-roles.md)
4. [System Overview](architecture/system-overview.md)

---

## Architecture

- [System Overview](architecture/system-overview.md)

Additional architecture and data-flow documentation will be added as the sandbox architecture stabilizes.

---

## Onboarding

- [Local Development Setup](onboarding/local-setup.md)

The onboarding documentation will expand as infrastructure, applications, observability, and automation become reproducible.

---

## Component Documentation

Technical documentation that belongs to a specific implementation area remains near that component:

- [Applications](../apps/)
- [Infrastructure](../infrastructure/)
- [Observability](../observability/)
- [Automation](../automation/)

Current OpenObserve installation instructions:

- [OpenObserve Local Installation](../observability/install.md)

---

## Architecture Decisions

- [Architecture Decision Records](decisions/README.md)
- [ADR Template](decisions/ADR-template.md)

---

## Operator Runbooks

- [Runbook Index](runbooks/README.md)
- [Runbook Template](runbooks/runbook-template.md)

Incident-specific runbooks will be added as failure scenarios and remediation actions are implemented and tested.

---

## Release

- [Release Checklist](release/release-checklist.md)

Deployment, rollback, known-limitation, and handoff documentation will be added as the project approaches release readiness.

---

## Project Documentation

- [Team Roles](project/team-roles.md)
- [Documentation Status](project/documentation-status.md)

---

## Documentation Rules

- Keep the repository root README concise.
- Put cross-system documentation in `docs/`.
- Keep component-specific technical instructions near the component they describe.
- Do not duplicate the same instructions in multiple files.
- Test commands before marking a guide as verified.
- Never place passwords, tokens, or other real secrets in documentation.
- Update documentation in the same pull request when a technical change makes existing instructions inaccurate.

---

## Documentation Ownership

Documentation & Release maintains this documentation structure and coordinates updates.

Technical workstream owners are responsible for validating technical details related to their components.
