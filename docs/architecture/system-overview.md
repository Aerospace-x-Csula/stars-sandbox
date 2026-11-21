# STARS Sandbox System Overview

> **Status:** Updated Draft - reflects the Fall 2026 implementation presented by the project team. Technical review by the relevant sub-leads is recommended before this document is treated as final.
>
> **Scope:** The STARS student sandbox and its current development/test components. This document does **not** describe a production STARS deployment.

## Purpose

The STARS sandbox is a development and testing environment for the **STARS AI-Powered Observability Platform**, a CSULA Senior Design project in collaboration with The Aerospace Corporation.

The project is building a representative STARS-like environment that can:

1. generate realistic application activity and failure conditions,
2. collect logs, metrics, and traces,
3. send telemetry to OpenObserve,
4. detect abnormal behavior,
5. support investigation and root-cause analysis, and
6. safely remediate approved problems.

The long-term project flow is:

```text
Observe -> Detect -> Explain -> Heal
```

The sandbox is intentionally isolated from production STARS infrastructure.

---

## Current Project Status

The Fall 2026 work focused primarily on the sandbox foundation, baseline observability, and the readiness gate.

The project now has working components across Infrastructure, Data/Test Engineering, Observability, AI/ML, and Automation & Self-Healing.

Some Phase 3 and Phase 4 concepts have already been prototyped, including anomaly detection, forecasting, alert grouping, log-pattern detection, and low-risk automated remediation.

However, the full AI monitoring, root-cause-analysis, and self-healing architecture is **not yet complete**.

The planned Spring 2027 work continues with:

- AI monitoring,
- root-cause analysis,
- expanded self-healing,
- advanced features,
- hardening, and
- final system integration and demonstration.

---

## High-Level Architecture

```text
                       STARS Sandbox
                            |
                            v
+---------------------------------------------------------+
|                   Infrastructure                        |
|                                                         |
|  Developer laptops: Docker + Minikube                  |
|  Multi-node testing: private K3s VM environment        |
+---------------------------+-----------------------------+
                            |
                            v
+---------------------------------------------------------+
|             Data / Test Engineering                     |
|                                                         |
|  Log Generator                                          |
|  Synthetic Metrics                                      |
|  Trace Generator                                        |
|  Locust Traffic                                         |
|  Failure Scenarios                                      |
|  Telemetry Validation Tests                             |
+---------------------------+-----------------------------+
                            |
                   logs / metrics / traces
                            |
                            v
+---------------------------------------------------------+
|                    Observability                        |
|                                                         |
|  OpenTelemetry Collector                                |
|  OpenObserve                                            |
|  Dashboards                                             |
|  Telemetry Search / Validation                          |
+---------------------------+-----------------------------+
                            |
                            v
+---------------------------------------------------------+
|                       AI / ML                           |
|                                                         |
|  Anomaly Detection                                      |
|  Resource Forecasting                                   |
|  Alert Grouping                                         |
|  Log-Pattern Detection                                  |
|  Root-Cause Analysis - planned / future integration     |
+---------------------------+-----------------------------+
                            |
                            v
+---------------------------------------------------------+
|             Automation & Self-Healing                   |
|                                                         |
|  Local Healer - low-risk prototype                      |
|  Circuit-breaker guardrail                              |
|  Audit entries                                          |
|  Higher-risk remediation - future work                  |
+---------------------------+-----------------------------+
                            |
                            |
                  Remediates approved faults
                            |
                            +---------> Applications
```

The diagram represents the major current project components and intended information flow. It does **not** imply that every AI component is already integrated directly with the automation system.

---

## 1. Infrastructure

The Infrastructure workstream provides the Kubernetes environments used to develop and test the sandbox.

### Local Developer Environment

The primary developer environment uses:

- Docker,
- Minikube,
- Kubernetes,
- `kubectl`,
- Helm, and
- the `stars` Kubernetes namespace.

Students use local Minikube clusters on their laptops for development and testing.

Repository setup scripts support multiple operating systems.

### Multi-Node K3s Testing Environment

The Infrastructure team has also established a private VM-based environment for multi-node Kubernetes testing.

The current documented topology is:

```text
STARS Team
    |
    | SSH / kubectl / Helm
    v
Private VM Network
    |
    +-- stars1 - K3s control plane
    |
    +-- stars2 - K3s worker
    |
    +-- stars3 - K3s worker
    |
    `-- stars4 - K3s worker
```

The local Minikube environment remains useful for individual development, while the K3s environment supports testing a more representative multi-node architecture.

Cloud deployment remains future work.

For more detail, see [Infrastructure Architecture](infrastructure-architecture.md).

---

## 2. Data / Test Engineering

The Data/Test Engineering workstream provides repeatable workloads, telemetry generators, failure scenarios, and automated validation.

Current repository components include:

### Log Generator

The log generator produces application activity such as:

- heartbeat logs,
- warnings,
- simulated errors,
- error spikes,
- connectivity failures, and
- crash scenarios.

Runs can be associated with a `run_id` so generated events can be correlated with tests.

### Synthetic Metrics

The synthetic-metrics component produces CPU and memory telemetry.

It can generate:

- normal baseline data,
- scheduled CPU spikes, and
- memory-leak behavior.

The normal-data mode provides baseline information that can be used by AI/ML experiments.

### Trace Generator

The trace generator creates OpenTelemetry traces for a simulated distributed application.

A trace may represent activity across example services such as:

```text
frontend -> api -> db -> payment
```

Supported test scenarios include normal operation, slow database behavior, and payment errors.

### Locust Traffic

Locust generates repeatable application traffic and stress scenarios.

This provides realistic workload activity and contributes data that can be used by the observability and AI portions of the project.

### Failure Scenarios and Automated Validation

The project maintains a failure-scenario catalog covering telemetry such as:

- logs,
- metrics,
- traces,
- Locust traffic, and
- injected spikes.

Automated pytest-based tests validate expected behavior and preserve test results for later review.

---

## 3. Telemetry Flow

The current local sandbox contains an end-to-end telemetry path from generated workloads into OpenObserve.

A simplified view is:

```text
Data/Test Workloads
        |
        | logs / metrics / traces
        v
OpenTelemetry Collector
        |
        v
OpenObserve
        |
        +--> Search
        |
        +--> Dashboards
        |
        `--> Data used for AI/ML experiments
```

A more detailed local architecture includes:

```text
trace-generator
      |
      | OTLP traces
      v
OpenTelemetry Collector Gateway
      |
      v
OpenObserve


log-generator --------\
synthetic-metrics -----+--> Collector / container logs --> OpenObserve
stars-app -------------/


Locust
   |
   +--> application traffic
   |
   `--> Locust result streams where configured
```

The project has performed end-to-end validation showing generated logs being collected, ingested into OpenObserve, searched, and displayed through dashboards.

---

## 4. Observability

OpenObserve is the central observability platform used by the sandbox.

The Observability workstream has implemented documentation and configuration for:

- OpenObserve deployment using Kubernetes and Helm,
- OpenTelemetry collector deployment/configuration,
- telemetry forwarding,
- OpenObserve installation,
- enterprise deployment/migration guidance, and
- dashboards.

### OpenObserve

The local environment exposes OpenObserve through the Kubernetes environment.

The standard local interface is available through port forwarding at:

```text
http://localhost:5080
```

### Collector

The OpenTelemetry collector receives telemetry from sandbox workloads and forwards supported telemetry into OpenObserve.

### Dashboards

Current dashboard work includes monitoring application logs and errors.

The error-monitoring dashboard can display information such as:

- total errors,
- warnings,
- connectivity failures,
- crashes, and
- error categories.

Dashboards provide human-readable operational visibility before more advanced AI-assisted monitoring is added.

---

## 5. AI / ML

The AI/ML workstream has moved beyond planning and now contains several working experiments and prototypes.

### Anomaly Detection

The anomaly-detection work uses normal CPU data from the synthetic-metrics generator to establish an expected range.

CPU spikes outside the learned range can then be flagged as anomalies.

In the Fall 2026 demonstration dataset, the anomaly-detection experiment detected all 23 injected CPU spikes with no false alarms in that specific test.

This result should be treated as an experiment result, not as a general production-performance guarantee.

### Resource Forecasting

A Python-based resource-exhaustion forecasting prototype has been developed to explore predicting resource problems before they occur.

### Alert Grouping

Alert-grouping work explores combining related alerts into a single incident using shared dimensions such as namespace or service.

The purpose is to reduce duplicate notifications and alert fatigue.

### Log-Pattern Detection

The team has also evaluated log-pattern behavior and SQL-based rules for detecting new warning/error activity that may not appear in a baseline pattern view.

### Root-Cause Analysis

Full root-cause analysis remains a future integration area.

The longer-term goal is to correlate telemetry and other evidence to identify likely causes of incidents rather than treating individual alerts independently.

---

## 6. Automation & Self-Healing

The Automation & Self-Healing workstream has implemented an initial **low-risk remediation prototype** called the local healer.

Higher-risk remediation remains future work.

### Local Healer

The local healer operates only on eligible Kubernetes workloads.

Current safeguards include:

- the workload must be controller-managed,
- it must be explicitly labeled `auto-heal=true`,
- the healer detects unhealthy/crash-looping behavior,
- a circuit breaker limits repeated healing attempts, and
- heal/block decisions produce audit output.

The current demonstrated remediation approach deletes an unhealthy eligible Pod so its Kubernetes controller can recreate it.

### Current Guardrail

The demonstrated circuit-breaker behavior allows a maximum of:

```text
3 heals per application within a 30-minute window
```

After the threshold is reached, automated healing stops.

A period of healthy operation resets the limit.

### Future Automation Work

The current local healer is intentionally limited to low-risk actions.

Future work includes:

- fuller pre-action checks,
- post-action validation,
- human-in-the-loop approval,
- integration of audit information with OpenObserve,
- medium-risk remediation,
- high-risk remediation,
- critical-risk handling, and
- expanded rollback/escalation behavior.

Medium- through critical-risk remediation has been researched but is not currently implemented as complete automated functionality.

---

## 7. Current Integration State

The major project components now exist, but the project should not yet be described as a fully integrated autonomous self-healing platform.

### Working or Demonstrated

Current work includes:

- local Kubernetes development environments,
- a multi-node K3s testing environment,
- log generation,
- synthetic metrics,
- trace generation,
- traffic generation,
- failure scenarios,
- automated telemetry tests,
- OpenTelemetry collection,
- OpenObserve ingestion,
- OpenObserve dashboards,
- anomaly-detection experiments,
- forecasting experiments,
- alert-grouping work,
- log-pattern detection, and
- low-risk local healing with guardrails.

### Still Incomplete / Future Integration

The following remain future or incomplete work:

- full production-like environment scaling,
- cloud deployment,
- complete AI monitoring integration,
- evidence-based root-cause-analysis workflow,
- closed-loop AI-to-remediation integration,
- medium/high/critical remediation actions,
- complete human-approval workflow,
- complete post-remediation validation and rollback,
- final production-evaluation packaging, and
- final hardening.

---

## 8. Repository Areas

| Directory | Responsibility |
| --- | --- |
| [`infrastructure/`](../../infrastructure/README.md) | Local and VM-based Kubernetes environment setup and infrastructure configuration. |
| [`apps/`](../../apps/README.md) | Sample applications, telemetry generators, traffic generation, failure scenarios, and telemetry tests. |
| [`observability/`](../../observability/README.md) | OpenObserve, collectors, dashboards, and observability configuration. |
| [`ai/`](../../ai/README.md) | Anomaly detection, forecasting, alert grouping, and related AI/ML experiments. |
| [`automation/`](../../automation/README.md) | Local healing and future remediation/self-healing work. |
| [`docs/`](../README.md) | Cross-system architecture, onboarding, runbooks, project documentation, and release guidance. |

Component-specific instructions should remain close to their implementation. Cross-system documentation belongs under `docs/`.

---

## 9. Current and Future Development Flow

The project can be summarized as:

```text
Generate
   |
   v
Observe
   |
   v
Detect
   |
   v
Explain
   |
   v
Heal
```

### Fall 2026

Primary emphasis:

```text
Sandbox Foundation
        +
Baseline Observability
        +
Readiness Validation
```

The team also produced early AI/ML and low-risk remediation prototypes.

### Spring 2027

Planned emphasis:

```text
AI Monitoring
        |
        v
Root-Cause Analysis
        |
        v
Expanded Self-Healing
        |
        v
Advanced Features
        |
        v
Hardening + Final Demo
```

---

## 10. Important Boundaries

The STARS sandbox is a development and testing environment.

It should **not** be interpreted as:

- a production STARS deployment,
- permission for unsupervised production changes,
- a production-ready autonomous remediation platform, or
- proof that experimental AI results generalize beyond the test datasets used.

Higher-risk actions must remain controlled and should require the safeguards and approval process defined by the project as those capabilities are implemented.

---

## Related Documentation

- [Infrastructure Architecture](infrastructure-architecture.md) - current infrastructure environments and topology.
- [Local Setup Guide](../onboarding/local-setup.md) - developer environment setup.
- [Common Setup Errors](../onboarding/common-setup-errors.md) - common local setup problems.
- [Infrastructure README](../../infrastructure/README.md) - infrastructure implementation guidance.
- [Applications README](../../apps/README.md) - workloads, generators, and testing.
- [Observability README](../../observability/README.md) - observability implementation.
- [AI README](../../ai/README.md) - AI/ML implementation and experiments.
- [Automation README](../../automation/README.md) - self-healing implementation.
- [Runbooks](../runbooks/README.md) - operational runbook guidance.
- [Release Checklist](../release/release-checklist.md) - release-readiness checklist.

---

**Review status:** Updated by Documentation & Release using the current repository structure and Fall 2026 project presentation. Relevant technical sub-leads should confirm their sections before this document is marked final.
