# STARS Error Generator

## Overview

The `error-generator` is a Kubernetes Deployment used to create simulated application logs for testing OpenObserve.

The generated ERROR messages are fake. This is just for testing :>

Log flow:

```text
Workflow:
error-generator > Kubernetes logs > OpenObserve Collector > STARS Error Monitoring Dashboard
```

The generator creates four types of logs:

```text
INFO    request completed successfully
WARN    high latency detected
ERROR   authentication failure
ERROR   database timeout
```

---

## Files

```text
apps/error-generator/
├── deployment.yaml                              # Kubernetes Deployment that generates simulated logs
└── README.md                                    # Instructions for using the generator and dashboard
```

---

## 1. Deploy the Error Generator

Make sure Minikube, OpenObserve, and the OpenObserve Collector are already running.

If you forgot how to do it, please go to `observability/collector.md` and follow the prerequisite steps.

Go to the error-generator directory:

```powershell
cd apps/error-generator                         	      # Enter the error-generator folder
```

Optional: Check the YAML before deploying:

```powershell
kubectl apply --dry-run=client -f deployment.yaml       # Validate YAML without creating anything
```

Deploy the error generator:

```powershell
kubectl apply -f deployment.yaml                        # Create the error-generator Deployment
```

Expected output:

```text
deployment.apps/error-generator created
```

If it already exists, the output may say:

```text
deployment.apps/error-generator configured
```

---

## 2. Check the Error Generator Pod

Run:

```powershell
kubectl get pods -n stars -l app=error-generator        # Show only error-generator Pods in stars
```

Expected result:

```text
error-generator-#-#   1/1     Running
```

Important values:

```text
READY:   1/1                                       	    # Container started successfully
STATUS:  Running                                   	    # Pod is currently running
```

---

## 3. Check the Generated Logs

Run:

```powershell
kubectl logs -n stars -l app=error-generator --tail=20  # Show latest 20 generated logs
```

Expected logs:

```text
2026-10-08T01:48:40Z INFO request completed successfully status=200
2026-10-08T01:48:45Z WARN high latency detected latency_ms=1800
2026-10-08T01:48:50Z ERROR authentication failure user_id=test-user reason=invalid_token
2026-10-08T01:48:55Z ERROR database timeout database=stars-db timeout_ms=5000
```

The generator repeats these logs continuously.

```text
INFO                     # Simulated successful request
WARN                     # Simulated high latency warning
ERROR authentication     # Simulated authentication failure
ERROR database timeout   # Simulated database timeout
```

---

## 4. Verify Logs in OpenObserve

Open OpenObserve:

```text
http://localhost:5080
```

Go to:

```text
Logs >> default
```

To show only logs from the error generator, use:

```sql
k8s_container_name = 'error-generator'
```

NOTE: put the sql command in the textbox under the [Search | Visualize] tab. Then, click "Run query".

Explanation:

```text
k8s_container_name                              # Kubernetes container metadata field
error-generator                                 # Name of the container we want to find
```

The logs should contain Kubernetes metadata similar to:

```text
k8s_container_name:  error-generator            # Container name
k8s_deployment_name: error-generator            # Deployment name
k8s_namespace_name:  stars                      # Kubernetes namespace
k8s_pod_name:        error-generator-...        # Pod name
```

`k8s_container_name` is useful for filtering because the Pod name may change when Kubernetes recreates the Pod.

---

## 5. Filter Only ERROR Logs

Use this query in the OpenObserve Logs page:

```sql
k8s_container_name = 'error-generator' AND body LIKE '%ERROR%'
```

Explanation:

```text
k8s_container_name = 'error-generator'          # Only logs from the error generator
AND                                             # Both conditions must be true
body LIKE '%ERROR%'                             # Body must contain the word ERROR
```

Expected results:

```text
ERROR authentication failure ...
ERROR database timeout ...
```

INFO and WARN logs should not appear.

---

# STARS Error Monitoring Dashboard

Create a dashboard in OpenObserve named:

```text
STARS Error Monitoring
```

The dashboard contains five panels:

```text
1. Total Errors
2. Database Timeouts
3. Authentication Failures
4. Errors Over Time
5. Latest Error Logs
```

The dashboard is stored inside the local OpenObserve instance.

```text
deployment.yaml           # Creates the simulated logs
OpenObserve dashboard     # Must be created/imported separately
```

If the dashboard is not exported and shared, each developer can recreate it using the steps below.

---

## 6. Total Errors

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

Where to find each option:

```text
123 / Single Value   -> Look at the visualization icons on the far-left side of the panel editor.
                        Click the icon labeled "123".

Custom               -> Look at the bottom-right of the query editor.
                        You should see: SQL | Builder | Custom
                        Click "Custom".

Panel Name           -> Look at the top-left of the panel editor.
                        Click the pencil icon next to the current name
                        (for example "Record count" or "Default overview"),
                        then rename it to "Total Errors".

SQL Query Box        -> Located at the bottom of the panel editor.
                        Delete the existing query and paste the query below.

Apply                -> Purple button in the upper-right.
                        Click this to run the query and preview the result.

Save                 -> Button in the upper-right next to Apply.
                        Click this after confirming the panel works.
```

Use this query:

```sql
SELECT count(_timestamp) as "y_axis_1"          -- Count matching logs
FROM "default"                                  -- Search the default stream
WHERE k8s_container_name = 'error-generator'    -- Only error-generator logs
  AND body LIKE '%ERROR%'                       -- Only ERROR messages
```

After pasting the query, click:

```text
Apply -> Check that a number appears -> Save
```

This panel shows the total number of simulated ERROR logs during the selected dashboard time range.

For example:

```text
Total Errors
90
```

The exact number may change because the dashboard uses a moving time range such as **Past 15 Minutes**.

## 7. Database Timeouts

Create another panel using the **same steps and locations described in Task 6**.

Use these settings:

```text
Visualization: 123 / Single Value
Query Mode:    Custom
Panel Name:    Database Timeouts
```

Paste this query into the SQL query box at the bottom:

```sql
SELECT count(_timestamp) as "y_axis_1"          -- Count matching logs
FROM "default"                                  -- Search the default stream
WHERE k8s_container_name = 'error-generator'    -- Only error-generator logs
  AND body LIKE '%database timeout%'            -- Only database timeout logs
```

Then:

```text
Apply -> Check that a number appears -> Save
```

This panel detects logs such as:

```text
ERROR database timeout database=stars-db timeout_ms=5000
```

---

## 8. Authentication Failures

Create another panel using the **same steps and locations described in Task 6**.

Use these settings:

```text
Visualization: 123 / Single Value
Query Mode:    Custom
Panel Name:    Authentication Failures
```

Paste this query into the SQL query box at the bottom:

```sql
SELECT count(_timestamp) as "y_axis_1"             -- Count matching logs
FROM "default"                                     -- Search the default stream
WHERE k8s_container_name = 'error-generator'       -- Only error-generator logs
  AND body LIKE '%authentication failure%'         -- Only authentication failures
```

Then:

```text
Apply -> Check that a number appears -> Save
```

This panel detects logs such as:

```text
ERROR authentication failure user_id=test-user reason=invalid_token
```

---

## 9. Errors Over Time

Create another panel using the **same panel creation steps described in Task 6**.

This panel is a little different because it uses a **Line Chart** instead of a single number.

Use these settings:

```text
Visualization: Line Chart
Query Mode:    Custom
Panel Name:    Errors Over Time
```

The **Line Chart** icon is located in the visualization list on the far-left side of the panel editor.

After selecting the Line Chart, switch the query mode to **Custom** at the bottom-right.

Paste this query into the SQL query box:

```sql
SELECT histogram(_timestamp, '1 minute') as "x_axis_1",  -- Group logs into 1-minute buckets
       count(_timestamp) as "y_axis_1"                   -- Count errors in each bucket
FROM "default"                                           -- Search the default stream
WHERE k8s_container_name = 'error-generator'             -- Only error-generator logs
  AND body LIKE '%ERROR%'                                -- Only ERROR messages
GROUP BY x_axis_1                                        -- Group counts by time
ORDER BY x_axis_1 ASC                                    -- Oldest time to newest
```

Then:

```text
Apply -> Check that the line graph appears -> Save
```

The current generator creates approximately:

```text
3 authentication failures per minute
3 database timeouts per minute
----------------------------------
6 total errors per minute
```

Because the error generator produces errors at a constant rate, the graph may appear mostly flat around 6.

## 10. Latest Error Logs

Create another panel using the **same panel creation steps described in Task 6**.

This panel is different because it uses a **Table** to display the actual error messages instead of showing a number or graph.

Use these settings:

```text
Visualization: Table
Query Mode:    Custom
Panel Name:    Latest Error Logs
```

The **Table** icon is located in the visualization list on the far-left side of the panel editor.

After selecting the Table visualization, switch the query mode to **Custom** at the bottom-right.

Paste this query into the SQL query box:

```sql
SELECT to_timestamp(_timestamp / 1000000) AS "time",     -- Convert timestamp to readable time
       body AS "error"                                   -- Show the actual error message
FROM "default"                                           -- Search the default stream
WHERE k8s_container_name = 'error-generator'             -- Only error-generator logs
  AND body LIKE '%ERROR%'                                -- Only ERROR messages
ORDER BY _timestamp DESC                                 -- Newest errors first
LIMIT 20                                                 -- Show only the latest 20 errors
```

After applying the query, look at the table field settings near the top of the panel editor.

OpenObserve may still show the old default fields:

```text
x_axis_1
y_axis_1
```

Remove or replace those fields, then configure the table as:

```text
First Column:   time
Other Columns:  error
```

The `time` and `error` fields come from this part of the SQL query:

```sql
to_timestamp(_timestamp / 1000000) AS "time"     -- Creates the time field
body AS "error"                                  -- Creates the error field
```

Then:

```text
Apply -> Check that the timestamp and error messages appear -> Save
```

The table should look similar to:

```text
time                  error
---------------------------------------------------------------------------
2026-10-07 20:00:33   ERROR database timeout database=stars-db timeout_ms=5000
2026-10-07 20:00:28   ERROR authentication failure user_id=test-user reason=invalid_token
```

The newest error should appear at the top of the table.

---

## 11. Why Custom SQL Is Used? (._.)?

The normal OpenObserve Dashboard Builder was tested first.

A filter such as:

```text
k8s_container_name = error-generator
```

worked correctly on the Logs page, but caused a field/schema error when used with the aggregated single-value dashboard panel.

Because of this, the dashboard panels use Custom SQL.

Example:

```sql
SELECT count(_timestamp)
FROM "default"
WHERE k8s_container_name = 'error-generator'
  AND body LIKE '%ERROR%'
```

The filtering order is:

```text
default log stream >> error-generator logs only >> ERROR logs only >> count/display matching logs
```

Custom SQL gives direct control over how the logs are filtered and counted.

---

## 12. Dashboard Time Range

For testing, the dashboard can use:

```text
Past 15 Minutes
```

The numbers may change slightly because this is a moving time range.

Example:

```text
Total Errors               89 - 90
Database Timeouts          44 - 45
Authentication Failures    44 - 45
```

This is normal.

As older logs leave the 15-minute window, new logs enter the window.

---

## 13. Stop the Error Generator

To stop generating logs without deleting the Deployment:

```powershell
kubectl scale deployment error-generator -n stars --replicas=0   # Stop the Pod
```

Verify:

```powershell
kubectl get pods -n stars -l app=error-generator                 # Check Pod status
```

To start it again:

```powershell
kubectl scale deployment error-generator -n stars --replicas=1   # Start one Pod again
```

---

## 14. Remove the Error Generator

Make sure you are at the root of the STARS repository.

Your path should end with:

```text
stars-sandbox
```

To completely remove the error-generator Deployment from Kubernetes:

```powershell
kubectl delete -f apps/error-generator/deployment.yaml   # Delete the Kubernetes resources created by the YAML file
```

Expected result:

```text
deployment.apps "error-generator" deleted from stars namespace
```

**DONT WORRIES** ( ´ ▽ ` )b

This does **not** delete the `deployment.yaml` file from the repository. It only removes the Kubernetes Deployment and its Pod.

To verify it was removed:

```powershell
kubectl get pods -n stars -l app=error-generator         # Check for any remaining error-generator Pods
```

Expected result:

```text
No resources found in stars namespace.
```

To recreate the error generator later:

```powershell
kubectl apply -f apps/error-generator/deployment.yaml    # Create the Deployment again
```

Expected result:

```text
deployment.apps/error-generator created
```

Then verify that the Pod is running:

```powershell
kubectl get pods -n stars -l app=error-generator         # Check the recreated Pod
```

Expected result:

```text
error-generator-#-#   1/1     Running   0          ...
```

---

## Summary

The complete test flow is:

```text
deployment.yaml
      |
error-generator Pod
      |
Simulated INFO / WARN / ERROR logs
      |
Kubernetes logs
      |
OpenObserve Collector
      |
OpenObserve default stream
      |
STARS Error Monitoring Dashboard
```

The dashboard monitors:

```text
Total Errors                  # Total simulated ERROR logs
Database Timeouts             # Simulated database timeout errors
Authentication Failures       # Simulated authentication errors
Errors Over Time              # Error count grouped by minute
Latest Error Logs             # Latest actual ERROR messages
```

All generated failures are simulated log messages only and are intended for observability testing.

You can also customize the dashboard panels by resizing, editing, or moving them around.