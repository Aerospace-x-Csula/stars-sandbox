# Anomaly Detection: Tuning and Accuracy (Pipeline Step 1)

**Goal:** learn what normal behavior looks like, flag anomalies, tune the flags to be more specific, and measure and report accuracy, using OpenObserve Enterprise Anomaly Detection.

**Test data:** `apps/synthetic-metrics` (on the `apps` branch). It logs `cpu_percent` and `memory_percent` every 5 seconds. With `ANOMALIES=on`, it adds a CPU spike in the last minute of every 5 minutes and a memory leak from minute 35 to 50 of every hour. It logs `started`/`ended` marker lines for each event, which serve as the ground truth.

## Prerequisites

- OpenObserve **Enterprise** running in Minikube (`--set enterprise.enabled=true`; Observability's install guide covers this)
- `synthetic-metrics` and the OpenObserve collector running
- Port-forward to the UI: `kubectl --namespace stars port-forward svc/openobserve-openobserve-standalone 5080:5080`
- At least one notification destination. OpenObserve greys out **New alert** until one exists. If you don't need notifications, create a placeholder:
  1. **Destination Templates → New template**: Name `placeholder`, Title `Anomaly: {alert_name}`, Body `{"text": "{alert_name}"}`
  2. **Notification Destinations → New destination**: Name `placeholder`, URL `https://example.com/stars-placeholder`, Method POST, Template `placeholder`. Local addresses such as `127.0.0.1` are blocked by OpenObserve's SSRF guard.

## Procedure

### 1. Collect a clean baseline (24 h)

The model must train on normal data only. The test anomalies repeat often (CPU spikes are 20% of all minutes), so a model trained on them would learn them as normal.

```bash
kubectl set env deployment/synthetic-metrics -n stars RUN_ID=baseline01 ANOMALIES=off
```

Keep the cluster running for 24 hours. Do not restart `synthetic-metrics` or stop Minikube.

### 2. Create the CPU rule (after 24 h of baseline)

In OpenObserve, go to **Reliability → All Alerts → New alert** and choose the **Anomaly** alert type.

| Field | Value |
|---|---|
| Name | `cpu-spike` |
| Stream type / name | Logs / `default` |
| Query mode | SQL (below) |
| Detection Resolution | 1 minute |
| Check Every | 1 minute |
| Look Back Window | 2 minutes |
| Training Window | 1 day |
| Retrain Every | **Never** (so test anomalies are never learned as normal) |
| Sensitivity | Auto (default; trained k = 6σ) |
| Alerting tab | Notifications off |

```sql
SELECT histogram(_timestamp, '1 minute') AS time_bucket,
       avg(TRY_CAST(regexp_replace(body, '.*cpu_percent=([0-9.]+).*', '\1') AS DOUBLE)) AS value
FROM "default"
WHERE k8s_container_name = 'synthetic-metrics'
  AND body LIKE '%cpu_percent=%'
GROUP BY time_bucket
ORDER BY time_bucket
```

Click **Save & Train** while the stream still holds only baseline data, and wait until the rule's status shows **Ready** before step 3.

### 3. Run the test

```bash
kubectl set env deployment/synthetic-metrics -n stars RUN_ID=test01 ANOMALIES=on
```

Let it run for at least 2 hours, which gives about 24 CPU spikes. The laptop may sleep in between: the test pauses and resumes, and only minutes with data are scored. If you measure more than 3 hours after the test started, add `--hours N` to cover the whole run.

### 4. Measure

```bash
export O2_USER="your-openobserve-email"
read -s -p "OpenObserve password: " O2_PASSWORD; export O2_PASSWORD; echo

# First time only: check that the script can see events and anomaly rows
python3 ai/anomaly-detection/evaluate_anomalies.py --rule cpu-spike --run-id test01 --inspect

# Score the run
python3 ai/anomaly-detection/evaluate_anomalies.py --rule cpu-spike --run-id test01 --label default-sigma6
```

The result prints to the terminal and is saved in `ai/anomaly-detection/results/`.

| Metric | Meaning |
|---|---|
| Precision | Share of flagged minutes that were real anomalies. **Raising this is the specificity goal.** |
| Recall | Share of injected events that were caught |
| F1 | Balance of precision and recall |
| False alarms/hr | Flags not near any event, per hour |
| Avg delay | Time from an event starting to its first flag |

The script also re-scores the same points at sensitivity levels from 2σ to 25σ. OpenObserve's anomaly score is in σ units, so "score > k" is what the rule would flag at Level = kσ, which shows the effect of tuning without retraining. A **Separation** section reports the highest score on a normal minute and the lowest peak score of a real spike; any level between the two catches every spike with no false alarms.

### 5. Tune

Use the sensitivity-level rows and the Separation section to pick a setting. To change it, edit the rule and set **Sensitivity** to a preset (Conservative / Balanced / Aggressive) or a custom **Level** in σ. A higher σ gives fewer, more confident flags (more specific); a lower σ catches more but risks false alarms. To confirm a new setting, run a fresh test (`RUN_ID=test02`, and so on) and record its numbers.

### 6. Report

`REPORT.md` holds the results for run `test01`: baseline and test times, rule settings, the accuracy table, tuning decisions, the chosen setting (Auto, 6σ), and the limitations.

### 7. Clean up

Return `synthetic-metrics` to its normal setting (spikes on, default run ID):

```bash
kubectl set env deployment/synthetic-metrics -n stars RUN_ID=metrics01
```

## Optional next tests

A harder CPU test with smaller spikes (for example +10–15% CPU) would show where tuning actually changes the results; this needs a change to the `synthetic-metrics` generator (Data/Test team).

To add a memory rule, repeat steps 2–5 with `memory_percent` in the SQL, rule name `memory-leak`, and `--metric memory`. The leak lasts 15 minutes once an hour, so run the test for at least 3 hours.
