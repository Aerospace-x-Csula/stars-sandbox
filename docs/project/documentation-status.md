# Documentation Status

This page tracks the current state of major STARS project documentation.

It is maintained by the Documentation & Release team and should be updated as documents are created, reviewed, tested, or replaced.

## Status Definitions

- **Draft** — document exists but has not been fully reviewed or verified.
- **In Progress** — document is actively being created or substantially updated.
- **Verified** — technical content has been reviewed by the appropriate owner and procedural instructions have been successfully tested where applicable.
- **Planned** — documentation is expected later but does not yet need to be created.
- **Not Applicable Yet** — the related technical feature or workflow is not mature enough to document accurately.

---

## Current Documentation

| Document | Status | Primary Owner | Technical Reviewer |
|---|---|---|---|
| Documentation Index | Draft | Documentation & Release | Documentation & Release |
| Repository README | Draft | Documentation & Release | Project Lead / Relevant Sub-Leads |
| Local Development Setup | Draft | Documentation & Release | Infrastructure |
| Common Setup Errors | Draft | Documentation & Release | Infrastructure / Observability |
| Pull Request Guide | Draft | Documentation & Release | Project Lead |
| Team Roles | Draft | Documentation & Release | Project Lead |
| System Overview | Draft | Documentation & Release | Relevant Sub-Leads |
| Infrastructure Architecture | Draft | Documentation & Release | Infrastructure |
| Architecture Decision Record Process | Draft | Documentation & Release | Relevant Sub-Leads |
| Runbook Framework / Template | Draft | Documentation & Release | Automation / Data-Test Engineering |
| Release Checklist | Draft | Documentation & Release | Project Lead |

---

## Component Documentation

| Document | Status | Primary Owner | Technical Reviewer |
|---|---|---|---|
| Infrastructure README / Setup Documentation | Draft | Infrastructure | Infrastructure Sub-Lead |
| Applications README | Draft | Data / Test Engineering | Data / Test Engineering Sub-Lead |
| Observability README / Installation Documentation | Draft | Observability | Observability Sub-Lead |
| AI README / Experiment Documentation | Draft | AI / ML | AI / ML Sub-Lead |
| Automation README / Local-Healer Documentation | Draft | Automation & Self-Healing | Automation & Self-Healing Sub-Lead |

---

## Current Major Documentation Work

| Document | Status | Primary Owner | Technical Reviewer |
|---|---|---|---|
| Requirements Inventory | In Progress | Documentation & Release | Relevant Sub-Leads |
| Component Inventory | In Progress | Documentation & Release | Relevant Sub-Leads |
| Software Requirements Document (SRD) | In Progress | Documentation & Release Sub-Lead | Project Lead / Relevant Sub-Leads |
| Preliminary Software Design Document (SDD) | In Progress | Documentation & Release Sub-Lead | Relevant Technical Sub-Leads |

---

## Planned Operational Documentation

| Document | Status | Primary Owner | Technical Reviewer |
|---|---|---|---|
| Incident-Specific Operator Runbooks | Planned | Documentation & Release | Automation / Data-Test Engineering |
| Operations Guide | Planned | Documentation & Release | Relevant Sub-Leads |
| Monitoring Guide | Planned | Documentation & Release | Observability |
| Troubleshooting Guide | Planned | Documentation & Release | Relevant Sub-Leads |
| Backup / Recovery Guide | Not Applicable Yet | Documentation & Release | Infrastructure |
| Failure-Injection Catalog Documentation | Planned | Documentation & Release / Data-Test Engineering | Data / Test Engineering |

---

## Planned Security Documentation

| Document | Status | Primary Owner | Technical Reviewer |
|---|---|---|---|
| RBAC Documentation | Planned | Documentation & Release | Infrastructure / Automation |
| Secrets Management Documentation | Planned | Documentation & Release | Infrastructure / Observability |
| Permissions Matrix | Not Applicable Yet | Documentation & Release | Infrastructure / Automation |

---

## Planned Release and Handoff Documentation

| Document | Status | Primary Owner | Technical Reviewer |
|---|---|---|---|
| Release Process | Planned | Documentation & Release | Project Lead |
| Deployment Guide | Planned | Documentation & Release | Relevant Sub-Leads |
| Rollback Guide | Planned | Documentation & Release | Automation / Infrastructure |
| Known Limitations | Planned | Documentation & Release | Relevant Sub-Leads |
| Operator Training Material | Planned | Documentation & Release | Project Lead / Relevant Sub-Leads |
| Developer Training Material | Planned | Documentation & Release | Project Lead |
| Demo Script | Planned | Documentation & Release | Project Lead |
| Final Handoff Checklist | Planned | Documentation & Release | Project Lead |

---

## Verification Rule

A document should **not** be marked `Verified` simply because it has been written or merged.

Verification should include:

1. review by the appropriate technical owner,
2. confirmation that the document reflects the current implementation,
3. successful execution of documented procedures where applicable,
4. working links and commands,
5. confirmation that no credentials or sensitive information are included.

If implementation changes invalidate a verified document, its status should return to `Draft` or `In Progress` until it is reviewed again.

---

## Current Documentation Priorities

The current Documentation & Release priorities are:

1. Complete the **Requirements Inventory**.
2. Complete the **Component Inventory**.
3. Complete the **Software Requirements Document (SRD)**.
4. Complete the **preliminary Software Design Document (SDD)**.
5. Keep the System Overview and Infrastructure Architecture synchronized with the implementation.
6. Resume expansion of operational, security, release, and handoff documentation after the SRD/SDD milestone.
