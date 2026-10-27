# OpenObserve searches for the load tests

These searches read two streams that the locustfile sends when OpenObserve is
configured (see "Send results to OpenObserve" in the main README):

| Stream | What it holds |
|---|---|
| `locust` | One row per request: run_id, scenario, name, status_code, response_time_ms, failed, error |
| `locust_runs` | One row per test start and stop, with run_id and scenario |

## How to run a search

1. Open OpenObserve (`kubectl -n observability port-forward svc/openobserve 5080:5080`, then http://localhost:5080).
2. Go to **Logs** and select the stream (`locust` or `locust_runs`).
3. Turn on **SQL mode**, paste a query below, and set the time range (for example, Last 15 minutes).
4. Run the query. To keep it, save it as a view from the Logs page.

## Traffic logs (the main search)

Every request, newest first:

```sql
SELECT _timestamp, run_id, scenario, method, name, status_code,
       response_time_ms, failed, error
FROM "locust"
ORDER BY _timestamp DESC
```

Only one run (replace the id with one from the runs search below):

```sql
SELECT _timestamp, scenario, method, name, status_code,
       response_time_ms, failed, error
FROM "locust"
WHERE run_id = 'abc12345'
ORDER BY _timestamp DESC
```

Only failed requests:

```sql
SELECT _timestamp, run_id, scenario, name, status_code, response_time_ms, error
FROM "locust"
WHERE failed = true
ORDER BY _timestamp DESC
```

## Find runs

Test start and stop events, with the run_id to use above:

```sql
SELECT _timestamp, event, run_id, scenario, users, duration_s,
       requests, failures, avg_ms, p95_ms
FROM "locust_runs"
ORDER BY _timestamp DESC
```

## Summaries

Requests by scenario and status code:

```sql
SELECT scenario, status_code, count(*) AS requests
FROM "locust"
GROUP BY scenario, status_code
ORDER BY scenario, status_code
```

Request rate and failures over time:

```sql
SELECT histogram(_timestamp, '10 seconds') AS ts,
       count(*) AS requests,
       sum(CASE WHEN failed THEN 1 ELSE 0 END) AS failures
FROM "locust"
GROUP BY ts
ORDER BY ts
```

p95 latency per request name:

```sql
SELECT name, approx_percentile_cont(response_time_ms, 0.95) AS p95_ms
FROM "locust"
GROUP BY name
ORDER BY p95_ms DESC
```

## App-side logs

The access logs written by `stars-app` itself come from the OpenTelemetry
collector, not from Locust. Their stream and field names depend on your
collector setup, so check the Logs stream list and filter on the `stars`
namespace field you find there.
