# Anomaly Detection Accuracy Report

**Author:** Eric | **Requested by:** Jayden (AI/ML sub-lead) | **Pipeline step:** 1, Learn "normal" and flag anomalies

## Summary

_One or two sentences: the chosen setting and its precision, recall, and false alarms/hr._

## Setup

| Item | Value |
|---|---|
| OpenObserve | Enterprise v1.1.2, Minikube (local laptop) |
| Data source | `synthetic-metrics`, `cpu_percent` (1-minute average) |
| Baseline (normal) run | `baseline01`, 2026-10-28 16:21 UTC to ____ |
| Test run(s) | `test01`: ____ to ____ UTC |
| Injected anomalies | CPU spike to ~80% for 1 min, every 5 min (normal ~25%) |
| Rule | `cpu-spike`, resolution 1 min, training window 1 day, retrain Never |

## Results

| Setting | Flags | Events caught | Precision | Recall | F1 | False alarms/hr | Avg delay |
|---|---|---|---|---|---|---|---|
| Default slider | | | | | | | |
| Tuned setting 1 | | | | | | | |
| Tuned setting 2 | | | | | | | |

## Tuning decisions

- _What you changed (slider range, resolution) and why_
- _What it did to precision (specificity) vs. recall_

## Chosen setting

_The setting and the reason for choosing it._

## Limitations and next steps

- Synthetic data with one obvious anomaly type. Real app traffic will be noisier.
- The laptop cluster gives only a 1-day training window. Rerun with 7–14 days on the always-on cluster.
- Next: add the memory-leak rule (slow-building anomaly), then apply the same method to real `stars-app` streams.
