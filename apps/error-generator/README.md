# STARS Error Monitoring Dashboard

## Overview

This README explains how to use the **STARS Error Monitoring** dashboard in OpenObserve.

The dashboard now looks at logs from both:

```text
log-generator
error-generator
```

The shared `log-generator` is used for manual WARN / ERROR / connectivity / crash tests.

The `error-generator` automatically creates a spike of **20 ERROR logs**, waits **20 seconds**, then repeats.

Each spike rotates through 5 simulated error types:

```text
authentication
database
connectivity
dependency
service
```

Each 20-error spike contains about 4 of each type.

All failures are simulated for observability testing only :>

```text
log-generator -----\
                    > Kubernetes logs > OpenObserve Collector > STARS Error Monitoring Dashboard
error-generator ---/
```

Dashboard panels:

```text
1. Total Errors
2. Total Warnings
3. Connectivity Failures
4. Container Crashes
5. Errors Over Time
6. Latest Error Logs
7. Errors by Type
```

---

## Files

```text
apps/log-generator/README.md                     # Manual log-generator tests
apps/error-generator/deployment.yaml             # Automatic 20-error spikes
apps/error-generator/README.md                   # This file
observability/dashboards/error-generator-dashboard.json
```

---

## 1. Start the Generators

Make sure Minikube, OpenObserve, and the collector are already running.

If you forgot the collector setup, go to:

```text
observability/collector.md
```

For the shared `log-generator`, follow:

```text
apps/log-generator/README.md
```

Start/update both generators:

```powershell
kubectl apply -f apps/log-generator/deployment.yaml      # Start/update log-generator
kubectl apply -f apps/error-generator/deployment.yaml    # Start/update error-generator
```

Check Pods:

```powershell
kubectl get pods -n stars
```

Watch the automatic error spikes:

```powershell
kubectl logs -n stars -l app=error-generator -f
```

Expected pattern:

```text
20 ERROR logs almost instantly
wait 20 seconds
20 ERROR logs almost instantly
repeat forever (ง'̀-'́)ง
```

---

## 2. Verify Logs in OpenObserve

Open:

```text
http://localhost:5080
```

Go to:

```text
Logs >> default
```

Show logs from both generators:

```sql
(k8s_container_name = 'log-generator' OR k8s_container_name = 'error-generator')
```

Show only ERROR logs from both:

```sql
(k8s_container_name = 'log-generator' OR k8s_container_name = 'error-generator')
AND body LIKE '%level=ERROR%'
```

`k8s_container_name` is used because Pod names can change when Kubernetes recreates Pods.

---

# Dashboard Queries

For each panel:

```text
Dashboard -> + -> Add Panel -> choose visualization -> Custom -> paste query -> Apply -> Save
```

Easy enough :>

---

## 3. Total Errors

```text
Visualization: 123 / Single Value
```

```sql
SELECT count(_timestamp) AS "y_axis_1"                 -- Count matching ERROR logs
FROM "default"                                         -- Search the default stream
WHERE (
        k8s_container_name = 'log-generator'           -- Include log-generator
        OR
        k8s_container_name = 'error-generator'         -- Include error-generator
      )
  AND body LIKE '%level=ERROR%'                        -- Only ERROR-level logs
```

Counts ERROR logs from both generators.

---

## 4. Total Warnings

```text
Visualization: 123 / Single Value
```

```sql
SELECT count(_timestamp) AS "y_axis_1"                 -- Count matching WARN logs
FROM "default"                                         -- Search the default stream
WHERE (
        k8s_container_name = 'log-generator'           -- Include log-generator
        OR
        k8s_container_name = 'error-generator'         -- Include error-generator
      )
  AND body LIKE '%level=WARN%'                         -- Only WARN-level logs
```

The current `error-generator` only creates ERROR logs, so WARN logs will normally come from `log-generator`.

---

## 5. Connectivity Failures

```text
Visualization: 123 / Single Value
```

```sql
SELECT count(_timestamp) AS "y_axis_1"                 -- Count connectivity errors
FROM "default"                                         -- Search the default stream
WHERE (
        k8s_container_name = 'log-generator'           -- Include log-generator
        OR
        k8s_container_name = 'error-generator'         -- Include error-generator
      )
  AND body LIKE '%level=ERROR%'                        -- Only ERROR-level logs
  AND body LIKE '%scenario=connectivity%'              -- Only connectivity scenarios
```

Both generators can use `scenario=connectivity`, so both can appear here.

---

## 6. Container Crashes

```text
Visualization: 123 / Single Value
```

```sql
SELECT count(_timestamp) AS "y_axis_1"                 -- Count crash ERROR logs
FROM "default"                                         -- Search the default stream
WHERE (
        k8s_container_name = 'log-generator'           -- Include log-generator
        OR
        k8s_container_name = 'error-generator'         -- Include error-generator
      )
  AND body LIKE '%level=ERROR%'                        -- Only ERROR-level logs
  AND body LIKE '%scenario=crash%'                     -- Only crash scenarios
```

The current `error-generator` does not actually crash, so this panel will normally increase from the `log-generator` crash test.

---

## 7. Errors Over Time

```text
Visualization: Bar Chart
X-Axis:        x_axis_1
Y-Axis:        y_axis_1
```

```sql
SELECT
    histogram(_timestamp) AS "x_axis_1",               -- Group ERROR logs into time buckets
    count(_timestamp) AS "y_axis_1"                    -- Count ERROR logs in each bucket
FROM "default"                                         -- Search the default stream
WHERE (
        k8s_container_name = 'log-generator'           -- Include log-generator
        OR
        k8s_container_name = 'error-generator'         -- Include error-generator
      )
  AND str_match(body, 'level=ERROR')                   -- Only ERROR-level logs
GROUP BY x_axis_1                                      -- One count per time bucket
ORDER BY x_axis_1 ASC                                  -- Oldest to newest
```

The automatic `error-generator` should show clear bars around 20 because each spike happens almost instantly.

---

## 8. Latest Error Logs

```text
Visualization: Table
First Column:  time
Other Columns: error
```

```sql
SELECT to_timestamp(_timestamp / 1000000) AS "time",     -- Readable timestamp
       body AS "error"                                   -- Actual ERROR message
FROM "default"                                           -- Search the default stream
WHERE (
        k8s_container_name = 'log-generator'             -- Include log-generator
        OR
        k8s_container_name = 'error-generator'           -- Include error-generator
      )
  AND body LIKE '%level=ERROR%'                          -- Only ERROR-level logs
ORDER BY _timestamp DESC                                 -- Newest first
LIMIT 50                                                 -- Latest 50 ERROR logs
```

Newest errors should appear at the top.

---

## 9. Errors by Type

This panel shows the 5 automatic error types from `error-generator`.

```text
Visualization: Bar Chart
X-Axis:        x_axis_1
Y-Axis:        y_axis_1
```

```sql
SELECT
    CASE
        WHEN body LIKE '%scenario=authentication%' THEN 'Authentication'
        WHEN body LIKE '%scenario=database%'       THEN 'Database'
        WHEN body LIKE '%scenario=connectivity%'   THEN 'Connectivity'
        WHEN body LIKE '%scenario=dependency%'     THEN 'Dependency'
        WHEN body LIKE '%scenario=service%'        THEN 'Service'
    END AS "x_axis_1",                              -- Error type

    count(_timestamp) AS "y_axis_1"                 -- Count each type

FROM "default"

WHERE k8s_container_name = 'error-generator'       -- Only automatic error-generator logs
  AND body LIKE '%level=ERROR%'                    -- Only ERROR logs
  AND (
       body LIKE '%scenario=authentication%'
       OR body LIKE '%scenario=database%'
       OR body LIKE '%scenario=connectivity%'
       OR body LIKE '%scenario=dependency%'
       OR body LIKE '%scenario=service%'
  )

GROUP BY x_axis_1                                  -- Group by error type
ORDER BY y_axis_1 DESC                             -- Highest count first
```

A complete spike should be around:

```text
Authentication    4
Database          4
Connectivity      4
Dependency        4
Service           4
-------------------
Total            20
```

This panel intentionally looks only at `error-generator` because these five scenarios belong to the automatic spike generator.

---

## 10. Why Custom SQL? (._.)?

Custom SQL makes it easier to control exactly which generator, log level, and scenario each panel uses.

Basically:

```text
default stream
      |
log-generator + error-generator
      |
filter level/scenario
      |
count/display logs
```

Less magic, less confusion :>

---

## 11. Dashboard Time Range

For testing, use something like:

```text
Past 5 Minutes
Past 15 Minutes
Past 1 Hour
```

The automatic generator creates about:

```text
20 errors every 20 seconds
~60 errors per minute
```

The exact number will move up/down as logs enter and leave the selected time range. Manual `log-generator` tests can also add extra errors.

This is normal, dont panic lol.

---

## 12. Stop / Restart

For `log-generator`, follow:

```text
apps/log-generator/README.md
```

Stop automatic spikes:

```powershell
kubectl scale deployment error-generator -n stars --replicas=0
```

Start them again:

```powershell
kubectl scale deployment error-generator -n stars --replicas=1
```

Remove the error-generator from Kubernetes:

```powershell
kubectl delete -f apps/error-generator/deployment.yaml
```

**DONT WORRIES** ( ´ ▽ ` )b

This only removes the Kubernetes Deployment/Pod. It does **not** delete `deployment.yaml` from the repo.

---

## Summary

```text
log-generator -----------------\
                                > OpenObserve Collector -> default stream -> STARS Error Monitoring
error-generator ---------------/
```

```text
log-generator    = manual WARN / ERROR / connectivity / crash tests
error-generator  = automatic 20-error spikes every 20 seconds
```

The dashboard combines both generators, while **Errors by Type** focuses only on the 5 automatic `error-generator` scenarios.

You can resize or move the dashboard panels however you want. Make it pretty :>
