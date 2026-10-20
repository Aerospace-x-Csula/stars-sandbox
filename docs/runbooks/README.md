# Operator Runbooks

This directory contains operational runbooks for detecting, investigating, remediating, validating, rolling back, and escalating STARS sandbox incidents.

Runbooks should be based on tested project behavior rather than theoretical procedures.

## Required Runbook Sections

Each runbook should document:

1. Detection
2. Symptoms
3. Impact
4. Preconditions
5. Investigation
6. Evidence collection
7. Likely causes
8. Remediation
9. Post-remediation validation
10. Rollback
11. Escalation
12. Audit/evidence requirements
13. Related dashboards or queries
14. Owner
15. Last tested date

## Planned Incident Runbooks

Runbooks are expected as relevant failure scenarios become implemented and testable, including:

- crash-looping application or pod
- failed readiness/liveness checks
- CPU saturation
- memory pressure / OOM
- disk pressure
- network or service connectivity failure
- application error-rate spike
- latency increase
- bad deployment or version
- dependency failure
- telemetry pipeline failure
- sudden traffic/load increase

## Creating a Runbook

Copy:

`runbook-template.md`

Do not mark a runbook as verified until someone has successfully followed it against the sandbox.
