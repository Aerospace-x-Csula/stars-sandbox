# STARS Error Monitoring Dashboard

## Overview

This README explains how to use the **STARS Error Monitoring** dashboard in OpenObserve.

The dashboard now uses logs from the shared `log-generator` instead of the old `error-generator`.

To deploy the log generator and generate WARN / ERROR / connectivity / crash test logs, follow:

```text
apps/log-generator/README.md
```

Log flow:

```text
Workflow:
log-generator > Kubernetes logs > OpenObserve Collector > STARS Error Monitoring Dashboard
```

The dashboard monitors:

```text
Total Errors
Total Warnings
Connectivity Failures
Container Crashes
Errors Over Time
Latest Error Logs
```

The `error-spike` test does not need its own panel anymore because it can already be seen in **Total Errors** and **Errors Over Time**.

---

## Files

```text
apps/error-generator/
└── README.md                                    # Dashboard instructions and queries

observability/dashboards/
└── error-generator-dashboard.json              # Exported OpenObserve dashboard
```

The dashboard JSON keeps the existing filename for now so teammates can continue using the same file.

---

## 1. Generate Test Logs

Make sure Minikube, OpenObserve, and the OpenObserve Collector are already running.

If you forgot how to set up the collector, go to:

```text
observability/collector.md
```

For deploying the `log-generator` and generating test logs, follow:

```text
apps/log-generator/README.md
```

The log generator supports test scenarios such as:

```text
WARN
ERROR
Error Spike
Connectivity Failure
Container Crash
```

Run one scenario at a time and wait for it to complete before starting the next one.

---

## 2. Verify Logs in OpenObserve

Open OpenObserve:

```text
http://localhost:5080
```

Go to:

```text
Logs >> default
```

To show only logs from the log generator, use:

```sql
k8s_container_name = 'log-generator'
```

NOTE: put the SQL command in the textbox under the **Search | Visualize** tab, then click **Run query**.

Explanation:

```text
k8s_container_name                              # Kubernetes container metadata field
log-generator                                   # Name of the container we want to find
```

The logs should contain Kubernetes metadata similar to:

```text
k8s_container_name:  log-generator
k8s_deployment_name: log-generator
k8s_namespace_name:  stars
k8s_pod_name:        log-generator-...
```

`k8s_container_name` is useful for filtering because the Pod name may change when Kubernetes recreates or restarts the Pod.

---

## 3. Filter Only ERROR Logs

Use this query in the OpenObserve Logs page:

```sql
k8s_container_name = 'log-generator' AND body LIKE '%level=ERROR%'
```

Explanation:

```text
k8s_container_name = 'log-generator'            # Only logs from log-generator
AND                                               # Both conditions must be true
body LIKE '%level=ERROR%'                        # Only ERROR-level logs
```

WARN and INFO logs should not appear.

---

# STARS Error Monitoring Dashboard

The dashboard contains six panels:

```text
1. Total Errors
2. Total Warnings
3. Connectivity Failures
4. Container Crashes
5. Errors Over Time
6. Latest Error Logs
```

The easiest way to use the dashboard is to import the exported JSON from:

```text
observability/dashboards/error-generator-dashboard.json
```

The steps below are still useful for understanding how each panel works or recreating the dashboard manually.

---

## 4. Total Errors

Go to:

```text
OpenObserve -> Dashboards -> STARS Error Monitoring
```

Click the **+** button near the top of the dashboard, then select **Add Panel**.

### Configure the Panel

```text
Visualization: 123 / Single Value
Query Mode:    Custom
Panel Name:    Total Errors
```

Use this query:

```sql
SELECT count(_timestamp) AS "y_axis_1"             -- Count all matching ERROR logs
FROM "default"                                     -- Search the default log stream
WHERE k8s_container_name = 'log-generator'         -- Only logs from log-generator
  AND body LIKE '%level=ERROR%'                    -- Only logs with ERROR level
```

Then:

```text
Apply -> Check that a number appears -> Save
```

This panel shows the total number of ERROR logs during the selected dashboard time range.

---

## 5. Total Warnings

Create another **123 / Single Value** panel.

Use these settings:

```text
Visualization: 123 / Single Value
Query Mode:    Custom
Panel Name:    Total Warnings
```

Use this query:

```sql
SELECT count(_timestamp) AS "y_axis_1"             -- Count all matching WARN logs
FROM "default"                                     -- Search the default log stream
WHERE k8s_container_name = 'log-generator'         -- Only logs from log-generator
  AND body LIKE '%level=WARN%'                     -- Only WARN-level logs
```

Then:

```text
Apply -> Check that a number appears -> Save
```

This panel shows WARN logs separately from ERROR logs.

---

## 6. Connectivity Failures

Create another **123 / Single Value** panel.

Use these settings:

```text
Visualization: 123 / Single Value
Query Mode:    Custom
Panel Name:    Connectivity Failures
```

Use this query:

```sql
SELECT count(_timestamp) AS "y_axis_1"             -- Count connectivity failure logs
FROM "default"                                     -- Search the default log stream
WHERE k8s_container_name = 'log-generator'         -- Only logs from log-generator
  AND body LIKE '%level=ERROR%'                    -- Only ERROR-level logs
  AND body LIKE '%scenario=connectivity%'          -- Only connectivity failure scenarios
```

Then:

```text
Apply -> Check that a number appears -> Save
```

Using `scenario=connectivity` means the panel works with different run IDs such as `network01`, `network02`, etc.

---

## 7. Container Crashes

Create another **123 / Single Value** panel.

Use these settings:

```text
Visualization: 123 / Single Value
Query Mode:    Custom
Panel Name:    Container Crashes
```

Use this query:

```sql
SELECT count(_timestamp) AS "y_axis_1"             -- Count container crash ERROR logs
FROM "default"                                     -- Search the default log stream
WHERE k8s_container_name = 'log-generator'         -- Only logs from log-generator
  AND body LIKE '%level=ERROR%'                    -- Only ERROR-level logs
  AND body LIKE '%scenario=crash%'                 -- Only crash scenario logs
```

Then:

```text
Apply -> Check that a number appears -> Save
```

This panel counts crash scenarios separately from the other ERROR logs.

The crash test is different from the normal ERROR tests because the container actually exits and Kubernetes restarts it.

---

## 8. Errors Over Time

Create another panel using a **Bar Chart**.

Use these settings:

```text
Visualization: Bar Chart
Query Mode:    Custom
Panel Name:    Errors Over Time
```

Use this query:

```sql
SELECT
    histogram(_timestamp) AS "x_axis_1",        -- Group ERROR logs into time buckets
    count(_timestamp) AS "y_axis_1"             -- Count how many ERROR logs are in each bucket
FROM "default"                                  -- Search the default OpenObserve log stream
WHERE k8s_container_name = 'log-generator'      -- Only logs from log-generator
  AND str_match(body, 'level=ERROR')            -- Only logs that contain level=ERROR
GROUP BY x_axis_1                               -- Create one count for each time bucket
ORDER BY x_axis_1 ASC                           -- Show oldest time to newest time
```

Configure the fields as:

```text
X-Axis: x_axis_1
Y-Axis: y_axis_1
```

Then:

```text
Apply -> Check that the bar chart appears -> Save
```

This panel is useful for seeing sudden increases in errors.

For example, an `error-spike` test should appear as a large bar because many ERROR logs happen at about the same time.

---

## 9. Latest Error Logs

Create another panel using a **Table**.

Use these settings:

```text
Visualization: Table
Query Mode:    Custom
Panel Name:    Latest Error Logs
```

Use this query:

```sql
SELECT to_timestamp(_timestamp / 1000000) AS "time",     -- Convert timestamp to readable time
       body AS "error"                                   -- Show the actual error message
FROM "default"                                           -- Search the default log stream
WHERE k8s_container_name = 'log-generator'               -- Only logs from log-generator
  AND body LIKE '%level=ERROR%'                          -- Only ERROR logs
ORDER BY _timestamp DESC                                 -- Newest errors first
LIMIT 50                                                 -- Only show the latest 50 errors
```

After applying the query, configure the table as:

```text
First Column:   time
Other Columns:  error
```

Then:

```text
Apply -> Check that the timestamp and error messages appear -> Save
```

The newest error should appear at the top of the table.

The limit is set to 50 so a full error spike can still be viewed together with other recent errors.

---

## 10. Why Custom SQL Is Used? (._.)?

The normal OpenObserve Dashboard Builder can work for simple panels, but Custom SQL gives more direct control over what each panel counts and displays.

For example:

```sql
SELECT count(_timestamp)
FROM "default"
WHERE k8s_container_name = 'log-generator'
  AND body LIKE '%level=ERROR%'
```

The filtering order is:

```text
default log stream >> log-generator logs only >> ERROR logs only >> count/display matching logs
```

Custom SQL is also useful for filtering specific scenarios such as:

```text
scenario=connectivity
scenario=crash
```

and for formatting the Latest Error Logs table.

---

## 11. Dashboard Time Range

For testing, you can use:

```text
Past 5 Minutes
Past 15 Minutes
Past 1 Hour
```

The dashboard only counts logs inside the selected time range.

For example, if you generate:

```text
1 normal ERROR
20 error-spike ERROR logs
1 connectivity ERROR
```

while they are all inside the selected time range, you may see:

```text
Total Errors               22
Connectivity Failures       1
```

The error spike will also be visible in **Errors Over Time** as a large bar.

If older test logs move outside the selected time range, the numbers will decrease or return to `0`.

This is normal :>

---

## 12. Stop or Remove the Log Generator

For stopping, restarting, or removing the log generator, follow:

```text
apps/log-generator/README.md
```

This keeps the log-generator instructions in one place instead of repeating them here.

---

## Summary

The complete flow is:

```text
log-generator
      |
      | INFO / WARN / ERROR / failure test logs
      v
Kubernetes logs
      |
      v
OpenObserve Collector
      |
      v
OpenObserve default stream
      |
      v
STARS Error Monitoring Dashboard
```

The dashboard monitors:

```text
Total Errors             # Total ERROR-level logs
Total Warnings           # Total WARN-level logs
Connectivity Failures    # Connectivity scenario ERROR logs
Container Crashes        # Crash scenario ERROR logs
Errors Over Time         # ERROR count grouped over time
Latest Error Logs        # Latest actual ERROR messages
```

The `error-spike` test is still useful even without its own panel because it increases **Total Errors** and appears clearly in **Errors Over Time**.

You can also customize the dashboard panels by resizing, editing, or moving them around.
