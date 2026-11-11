# Anomaly detection accuracy: default-sigma6

- Rule: `cpu-spike` (metric: cpu, resolution: 60s)
- Test run: `run_id=test01`
- Scored window: 2026-10-29 16:42 to 18:41 UTC (2.0 h, 103 scored points)
- Injected events in window: 23
- A flag counts as a hit if its bucket overlaps an event or the 60s after it.

| Setting | Flags | Events caught | Precision | Recall | F1 | False alarms/hr | Avg delay |
|---|---|---|---|---|---|---|---|
| OpenObserve flags (as configured) | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 2 sigma | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 3 sigma | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 4 sigma | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 5 sigma | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 6 sigma (current) | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 8 sigma | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 10 sigma | 40 | 23/23 | 1.00 | 1.00 | 1.00 | 0.00 | 28 s |
| Level 15 sigma | 30 | 21/23 | 1.00 | 0.91 | 0.95 | 0.00 | 51 s |
| Level 20 sigma | 20 | 20/23 | 1.00 | 0.87 | 0.93 | 0.00 | 80 s |
| Level 25 sigma | 17 | 17/23 | 1.00 | 0.74 | 0.85 | 0.00 | 80 s |

The first row is what OpenObserve actually alerted on. The other rows re-score the same
points at other sensitivity levels (score is in sigma units), to show what a stricter
or looser setting would do without retraining.

## Separation

- Highest score on a normal minute: 1.09 sigma (43 normal minutes)
- Lowest peak score of a real spike: 14.45 sigma (23 spikes scored)
- Any level between 1.09 and 14.45 sigma separates every spike from every normal minute
