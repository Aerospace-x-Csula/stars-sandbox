# Anomaly Detection Accuracy Report

**Author:** Eric | **Requested by:** Jayden (AI/ML sub-lead) | **Pipeline step:** 1, Learn "normal" and flag anomalies

## Summary

OpenObserve's built-in anomaly detection (Random Cut Forest), trained on 24 hours of normal CPU data, caught **all 23 injected CPU spikes with zero false alarms** (precision 1.00, recall 1.00) at its default sensitivity of 6σ, flagging each spike about 28 seconds after it started. Re-scoring the same run from 2σ to 25σ showed no false alarms at any level, so the default is already fully specific on this data. Stricter settings (15σ and above) only missed spikes. **Recommended setting: keep the default (Auto, 6σ).**

## Method

1. Upgraded the local OpenObserve to the Enterprise edition, which includes the built-in anomaly detection (Random Cut Forest).
2. Collected 24 hours of clean, normal CPU data from `synthetic-metrics` with injected anomalies turned off (`ANOMALIES=off`).
3. Created an anomaly detection rule on that data and trained it once, with retraining turned off so the test anomalies are never learned as normal.
4. Turned the generator's scheduled CPU spikes on (`ANOMALIES=on`) and let the rule score every minute.
5. Compared the rule's flags (the `_anomalies` stream) against the generator's `CPU spike started/ended` log lines (ground truth) using `evaluate_anomalies.py`.
6. Re-scored the same run at sensitivity levels from 2σ to 25σ (the `_anomalies` score is in σ units) to see how tuning trades specificity against recall, without retraining.

## Setup

| Item | Value |
|---|---|
| OpenObserve | Enterprise v1.1.2 (Helm chart `openobserve-standalone`, `enterprise.enabled=true`), local Minikube cluster |
| Data source | `synthetic-metrics` logs, `cpu_percent` averaged per 1-minute bucket |
| Normal behavior | CPU ~25% (1-minute averages stayed between ~23 and ~26) |
| Injected anomaly | CPU spike to ~80% for 1 minute, in the last minute of every 5 minutes |
| Baseline run | `run_id=baseline01`, 2026-10-28 16:21:55 UTC to 2026-10-29 16:45 UTC (~24.4 h, >17,000 lines; a full day is 17,280) |
| Test run | `run_id=test01`, 2026-10-29 16:45:38 to 18:41 UTC (2.0 h, 103 scored minutes, 23 CPU spikes) |
| Alert destination | Placeholder webhook (OpenObserve requires one to create alerts); notifications disabled |

### Rule settings (`cpu-spike`)

| Setting | Value |
|---|---|
| Stream | Logs / `default` |
| Query | SQL: 1-minute average of `cpu_percent` for container `synthetic-metrics` |
| Detection resolution | 1 minute |
| Check every | 1 minute |
| Look back window | 2 minutes |
| Training window | 1 day |
| Retrain every | Never |
| Sensitivity (default) | Auto, trained threshold k = 6σ |
| Direction | Above or below |
| Window share | 100% of a 1-bucket window |

```sql
SELECT histogram(_timestamp, '1 minute') AS time_bucket,
       avg(TRY_CAST(regexp_replace(body, '.*cpu_percent=([0-9.]+).*', '\1') AS DOUBLE)) AS value
FROM "default"
WHERE k8s_container_name = 'synthetic-metrics'
  AND body LIKE '%cpu_percent=%'
GROUP BY time_bucket
ORDER BY time_bucket
```

## How accuracy is measured

| Metric | Meaning |
|---|---|
| Precision | Share of flagged minutes that were real spikes. **Raising this is the specificity goal.** |
| Recall | Share of injected spikes that were caught |
| F1 | Balance of precision and recall |
| False alarms/hr | Flagged minutes not near any spike, per hour of scoring |
| Avg delay | Time from a spike starting to its first flag |

A flag counts as a hit if its 1-minute bucket overlaps a spike or the 60 seconds after it. Time when the laptop was asleep has no data and is not scored.

## Results

Run `test01`. The first row is what OpenObserve flagged at its default setting. The other rows re-score the same 103 minutes at other sensitivity levels (the score is in σ units), which shows the effect of tuning without retraining.

| Setting | Flags | Events caught | Precision | Recall | F1 | False alarms/hr | Avg delay |
|---|---|---|---|---|---|---|---|
| **OpenObserve flags (Auto, 6σ)** | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 2σ | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 3σ | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 4σ | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 5σ | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 6σ (current) | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 8σ | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 10σ | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 15σ | 30 | 21/23 | 1.00 | 0.91 | 0.95 | 0.00 | 51 s |
| Level 20σ | 20 | 20/23 | 1.00 | 0.87 | 0.93 | 0.00 | 80 s |
| Level 25σ | 17 | 17/23 | 1.00 | 0.74 | 0.85 | 0.00 | 80 s |

**Separation between normal and anomalous minutes**

- Highest score on a normal minute: 1.09σ (43 normal minutes)
- Lowest peak score of a real spike: 14.45σ (23 spikes)
- Any level between 1.09σ and 14.45σ separates every spike from every normal minute.

Each spike usually produced 2 flags (40 flags for 23 spikes), because a 1-minute spike that starts mid-minute overlaps two 1-minute buckets. Both flags count as correct.

## Tuning decisions

- **Goal:** make the flags more specific (fewer false alarms) without missing real spikes.
- **Finding:** the default 6σ already had zero false alarms. Normal minutes never scored above 1.09σ, so loosening to as low as 2σ still added no false alarms.
- **Stricter levels only cost recall:** at 15σ, 2 spikes were missed. At 25σ, 6 were missed, and average detection delay rose from 28 s to 80 s. The missed spikes were the ones split across two buckets, which halves their 1-minute average.
- **Margin:** 6σ is about 5.5× above the noisiest normal minute and about 8σ below the weakest spike, so it should tolerate somewhat noisier data without retuning.

## Chosen setting

**Keep the default: Auto sensitivity, k = 6σ.** It gave perfect precision and recall with the fastest detection, and it sits in the middle of the safe range (1.09σ–14.45σ).

## Observations

- The rule showed a "Buckets skipped" notice, probably from the few seconds of missing data while the generator restarted between runs.
- The rule form says training "reads at least 21 days, if the stream keeps that much." Older data from before the baseline (when spikes were on) did not hurt the results: the learned normal range was 17.5–32.6% CPU (expected 25.1%), and every spike was caught.
- 103 of ~119 minutes in the test window were scored. The rest were skipped buckets, likely from the generator restart and short collection delays.
- The generator's memory leaks during the test (minutes 35–50 of each hour) produced no CPU flags, as expected.

## Limitations and next steps

- **The test was easy:** spikes (~80% CPU) are far from normal (~25%), so every setting from 2σ to 10σ scored perfectly. A harder test with smaller spikes (for example +10–15% CPU) would show where tuning actually changes the results.
- Small sample: 23 spikes and 43 clearly normal minutes in 2 hours. A longer run would make the false-alarm rate more reliable.
- Synthetic data with one anomaly type. Real app traffic will be noisier.
- Laptop cluster: 1-day training window, with gaps whenever the laptop slept. Rerun with 7–14 days on the always-on cluster.
- Next: add a memory-leak rule (a slow-building anomaly), then apply the same method to real `stars-app` streams.
