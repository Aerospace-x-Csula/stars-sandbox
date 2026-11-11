# Alert Grouping in OpenObserve

**Goal:** one problem produces one incident instead of many alerts, with a noise reduction

> **Status note.** The alerts, destination, test data, and test script below were built and run on the Enterprise Single Node instance (v1.1.2). The **Incidents** page loads, but the **Creates Incident** toggle described in OpenObserve's documentation did **not** appear in the alert form in this build, so automatic incident creation was **not confirmed**. Sections that depend on it are marked *(not yet verified)*. See [Known limitations](#8-known-limitations).

> **Why two test-data options?** The team's `error-generator` produces realistic, continuous errors from a real pod, which is the best way to test whether related alerts **merge**. But all of its errors come from one container in one namespace, so it cannot show **over-grouping** (unrelated alerts wrongly merged). The custom test script sends structured events from separate namespaces, so it can test both. Using the two gives full coverage: Option A for merging with realistic data, Option B for merging *and* keeping unrelated problems separate.

---

## 1. Background

When one service breaks, several alerts usually fire together. If a database slows down, the API, frontend, and queue worker that depend on it can all alert within minutes. That is one real problem but many notifications, which causes alert fatigue.

OpenObserve's Incident Management is meant to fix this. According to its documentation, alerts are matched into one incident using shared dimensions such as service name, cluster, region, or namespace. It is an Enterprise and Cloud feature, so the open-source edition cannot be used for this step.

---

## 2. Prerequisites

1. **OpenObserve Enterprise (Single Node)** running in the local Minikube cluster. The open-source Helm install from `install.md` does not include incidents. Use the Enterprise manifest instead:
   - Image: `o2cr.ai/openobserve/openobserve-enterprise:v1.1.2`
   - Namespace: `openobserve`
   - Admin credentials stored in a Kubernetes Secret, not in the YAML.
2. **The OpenObserve Collector** sending Kubernetes logs to the Enterprise instance (see `collector.md`). The collector endpoint must be `http://openobserve.openobserve.svc.cluster.local:5080/api/default`.
3. **Port-forward** to reach the UI:
   ```bash
   kubectl -n openobserve port-forward svc/openobserve 5080:5080
   ```
   Then open `http://localhost:5080`. The top of the page should say **Edition: Enterprise**.
4. **Never commit** credentials, access keys, or any `*.local.*` file. Run `git status` before committing.

---

## 3. Set up the notification destination

Alerts require a destination.

- **Do not use Email.** It fails with "Email destination must have SMTP configured" unless SMTP is set up.
- **Do not use internal addresses** such as `localhost`, `host.minikube.internal`, or cluster IPs. OpenObserve blocks them ("Access to internal domain ... is not allowed for security reasons").
- Use **Alerts → Notification Destinations → New Destination → Custom Destination → Web Hook** with:
  - Name: `test-webhook`
  - Template: `prebuilt_webhook`
  - Method: `post`
  - URL: a public throwaway receiver (for example one generated at webhook.site). Use it only with fake test data.

A placeholder destination is enough for testing grouping. Delivery does not need to succeed for the alert to fire.

---

## 4. Test data: two options

> Run **one option at a time** so alert and incident counts stay unambiguous. Stop the error-generator before running Option B (see the stop command below).

### Option A: the team's `error-generator` (realistic, continuous)

The `error-generator` is documented in `apps/error-generator/README.md`. It writes ERROR logs to the `default` stream through the collector: a spike of 20 errors, a 20-second wait, then repeat. Each spike rotates through five simulated error types.

| Error type | Log text contains |
|---|---|
| Authentication | `scenario=authentication` |
| Database | `scenario=database` |
| Connectivity | `scenario=connectivity` |
| Dependency | `scenario=dependency` |
| Service | `scenario=service` |

**Start it and confirm it works:**
```bash
kubectl apply -f apps/error-generator/deployment.yaml
kubectl get pods -n stars
kubectl logs -n stars -l app=error-generator -f
```

In OpenObserve, go to **Logs → default** and run:
```sql
k8s_container_name = 'error-generator' AND body LIKE '%level=ERROR%'
```

**What the data looks like:**
- Stream: `default`
- The whole log line, including `level=ERROR` and `scenario=...`, is stored in the `body` field. There are no structured `service_name` or `error_type` fields, so alerts must match on `body` text.
- Fields available for grouping: `k8s_container_name`, `k8s_namespace_name` (`stars`), `k8s_deployment_name`, `k8s_pod_name`.
- All errors come from one container in one namespace.

**Stop it** (so it stops generating alerts):
```bash
kubectl scale deployment error-generator -n stars --replicas=0
```
Start again with `--replicas=1`.

### Option B: custom test script (structured, with an unrelated control)

Real application errors with structured fields are not available yet, so test errors are sent directly to a dedicated stream.

- **Stream:** `test_alerts` (created automatically on first ingest)
- **Ingest endpoint:** `POST http://localhost:5080/api/default/test_alerts/_json`
- **Fields per event:** `level`, `service_name`, `namespace`, `error_type`, `message`

The local script `observability/test_errors.local.sh` sends events in four rounds, 20 seconds apart:

| Round | Time | What is sent |
|---|---|---|
| 1 | t=0s | `postgres-db` timeouts (shop), `billing` errors (payments) |
| 2 | t=20s | `postgres-db` timeouts, `checkout-api` upstream errors (shop) |
| 3 | t=40s | `checkout-api` errors, `frontend` 502s, `queue-worker` job failures (shop) |
| 4 | t=60s | `postgres-db` timeouts, `billing` errors |

Run it with the port-forward active:

```bash
bash observability/test_errors.local.sh
```

It prompts for your OpenObserve email and password and does not store them. Create the alerts **before** running it, because a scheduled alert only sees events inside its evaluation window.

### Comparison

| | Option A: `error-generator` | Option B: test script |
|---|---|---|
| Data realism | High: real pod, real collector path | Low: synthetic events sent by hand |
| Runs | Continuously | Once per run (about 1 minute) |
| Stream | `default` | `test_alerts` |
| Fields | `body` text, `k8s_*` fields | Structured `service_name`, `namespace`, `error_type` |
| Namespaces | One (`stars`) | Two (`shop`, `payments`) |
| Tests merging | Yes | Yes |
| Tests over-grouping | No | Yes (`billing` should stay separate) |

---

## 5. Create the alerts

Go to **Reliability → Alerts** and click **New alert** (top right). The Alerts page has the tabs **All Alerts**, **Notification Destinations**, **Destination Templates**, and **Alert Library**, plus filter tabs for All, Scheduled, Realtime, Composite, and Anomaly alerts.

### The alert form, field by field

The form has a top bar, two tabs (**Alert Rules** and **Advanced**), and a live **Preview** and **Summary** panel on the right. Alert names cannot contain spaces or the characters `: # ? ' " % & /`, so use hyphens or underscores.

**Top bar**

| Field | What to enter |
|---|---|
| Alert name | Click the pencil icon next to the title at the top of the page. The subtitle reads "Add Alert in default" (the folder). |
| Alert Type | **Scheduled** (the other tabs are Realtime, Anomaly, and Composite) |
| Stream Type | `logs` |
| Stream Name | `default` for Option A, `test_alerts` for Option B |

**Alert Rules tab → Conditions**

A **Builder | SQL** toggle sits at the top of this section. Use **Builder**. SQL mode is available if a condition cannot be expressed with the builder.

| Field | What to enter |
|---|---|
| Alert if | `total events` matching logs found |
| Critical if | operator `>=`, value `1` |
| Add warning | Leave unused |
| Check every | `1` `Minutes` |
| on these **filters** | The filter group. See below. |

> **Watch the default.** The form may default **Critical if** to `!=` `3`, which fires constantly, including when there are zero events. Change it to `>=` `1`.

**Filters.** The filter area is a group with an **OR / AND** switch at the top. Set it to **AND** so every condition must match. Each row has three parts:

```
[ Column ]  [ operator (=) ]  [ Value ]   [X]
```

- Pick the column from the dropdown, keep the operator on `=` (other operators are in the dropdown), and type the value.
- **+ Condition** adds another row, **+ Condition Group** adds a nested group, and **Reorder** changes the order.
- The **X** at the end of a row deletes it. Delete any blank rows, because an empty row can cause validation errors or wrong matches.
- The form may show one row inside the group and another below it joined by "and". Both are ANDed, so either placement works; keeping all rows in the same group is tidier.
- Values are case-sensitive: `ERROR` must be uppercase.

**Alert Rules tab → Settings**

| Field | What to enter |
|---|---|
| Look back window | `1` Minutes |
| Cooldown period | `1` Minutes (testing only, see note below) |
| Hold for | `0` Minutes |
| Destination | `test-webhook` (use **Add Destination** to create one, and the refresh icon to reload the list; **New workflow** is also offered but not used here) |
| Notify on recovery | Off |
| Keep firing for | `5` Seconds (the default) |

> **Cooldown.** One minute is only for testing so alerts fire repeatedly. OpenObserve's guidance for real alerts is a cooldown of at least 10 minutes to avoid notification storms.

**Right panel.** The **Preview** evaluates your conditions against the last minute of data and says either "would trigger" or "would not trigger" with the number of matching data points. It reads "would not trigger" until matching events arrived within the last minute; that is normal. The **Summary** restates the alert in plain language (for example, "Alert me when 1+ events occur in any 1-minute period, but no more than once every 1 minute") and shows the **Query Condition**. Use it to confirm the filters were applied before saving.

Save the alert with the **Save** button at the bottom of the form.

### Settings summary used for every alert (both options)

| Field | Value |
|---|---|
| Alert Type | Scheduled |
| Alert if | total events |
| Critical if | `>=` `1` |
| Check every | 1 Minutes |
| Look back window | 1 Minutes |
| Cooldown period | 1 Minutes |
| Hold for | 0 |
| Destination | `test-webhook` |
| Notify on recovery | Off |
| Keep firing for | 5 Seconds |

### Option A alerts (stream type `logs`, stream `default`)

Each alert matches one error type from the `error-generator`. Use filters on `k8s_container_name` and `body`, or the SQL mode of the alert form. The `body LIKE` condition is the same pattern the STARS Error Monitoring dashboard uses.

| Alert name | Matches |
|---|---|
| `auth-errors` | `k8s_container_name = 'error-generator'` AND `body LIKE '%scenario=authentication%'` |
| `database-errors` | `k8s_container_name = 'error-generator'` AND `body LIKE '%scenario=database%'` |
| `connectivity-errors` | `k8s_container_name = 'error-generator'` AND `body LIKE '%scenario=connectivity%'` |
| `dependency-errors` | `k8s_container_name = 'error-generator'` AND `body LIKE '%scenario=dependency%'` |
| `service-errors` | `k8s_container_name = 'error-generator'` AND `body LIKE '%scenario=service%'` |

The available filter operators for `body` in the alert builder have not been confirmed. If the builder does not offer a "contains" style operator, use SQL mode.

### Option B alerts (stream type `logs`, stream `test_alerts`)

Use **filters** (AND) to build each condition. Values are case-sensitive: `ERROR` must be uppercase.

| Alert name | Filter 1 | Filter 2 |
|---|---|---|
| `db-timeout` | `service_name` = `postgres-db` | `error_type` = `timeout` |
| `api-upstream-errors` | `service_name` = `checkout-api` | `level` = `ERROR` |
| `frontend-errors` | `service_name` = `frontend` | `level` = `ERROR` |
| `queue-worker-errors` | `service_name` = `queue-worker` | `level` = `ERROR` |
| `billing-errors` | `service_name` = `billing` | `level` = `ERROR` |

### Enable incident creation *(not yet verified)*

OpenObserve's documentation places a **Creates Incident** toggle in the alert's **Settings** section, after Destination. When on, the alert creates an incident in the Incidents page, and it stops sending its regular notification. Instead it notifies only when a new incident is created or a new alert type joins an existing incident.

In the STARS v1.1.2 Enterprise build, the **Settings** section on the scheduled alert form contains only these fields: Look back window, Cooldown period, Hold for, Destination, Notify on recovery, and Keep firing for. **There is no Creates Incident toggle.** See [Known limitations](#8-known-limitations).

---

## 6. What each alert does and how they group

### Option A: alert reference

| Alert | Detects | Role in the test |
|---|---|---|
| `auth-errors` | Simulated authentication failures | One symptom of a single failing source |
| `database-errors` | Simulated database failures | One symptom |
| `connectivity-errors` | Simulated connectivity failures | One symptom |
| `dependency-errors` | Simulated dependency failures | One symptom |
| `service-errors` | Simulated service failures | One symptom |

All five come from the same container and namespace and fire within seconds of each other, repeatedly, because the generator spikes every 20 seconds.

**Intended grouping:** same container and namespace within 5 minutes means one incident. Repeated firings of the same alert should join that incident rather than create new ones.

**Expected result *(not yet verified)*:**

| Without grouping | With grouping |
|---|---|
| Five alerts firing every minute, so many firings over a 10-minute run | 1 incident containing all five alerts |

### Option B: alert reference

| Alert | Service | What it detects | Role in the scenario |
|---|---|---|---|
| `db-timeout` | `postgres-db` | Database queries timing out | **Root cause.** Starts the cascade. |
| `api-upstream-errors` | `checkout-api` | API errors because the database is unavailable | Downstream symptom. |
| `frontend-errors` | `frontend` | Gateway errors (HTTP 502) shown to users | Downstream symptom, further up the chain. |
| `queue-worker-errors` | `queue-worker` | Background jobs failing after retries | Downstream symptom. |
| `billing-errors` | `billing` | Payment processor errors | **Unrelated.** Different namespace, different cause. Must stay separate. |

**Assumed dependency map (test scenario):**

```
frontend ──> checkout-api ──> postgres-db
                                  ^
queue-worker ─────────────────────┘

billing (independent, namespace: payments)
```

This map is an assumption for the test scenario. Replace it with the real map when Observability's alert list and service dependencies are available.

**Intended grouping:**

1. **Same namespace within 5 minutes → one incident.** The four `shop` alerts should merge: they share a namespace and fire within seconds of each other. One failing database, four alerts, one incident.
2. **Different namespace → separate incident.** `billing-errors` (namespace `payments`) must not merge with the `shop` incident, even though it fires at the same time. Merging unrelated problems is **over-grouping** and hides real issues.
3. **Repeated firings of the same alert → collapse into the same incident**, not a new one each minute.

**Expected result *(not yet verified)*:**

| Without grouping | With grouping |
|---|---|
| Many separate firings across 5 alerts | 2 incidents |
| | Incident 1 (`shop`): `db-timeout`, `api-upstream-errors`, `frontend-errors`, `queue-worker-errors` |
| | Incident 2 (`payments`): `billing-errors` |
---

## 8. Known limitations

1. **No Creates Incident toggle in v1.1.2.** The documented toggle is not on the scheduled alert form. The Settings section ends at **Keep firing for**, even in a full-screen browser, and the Advanced tab has no incident option either. Automatic incident creation was therefore not confirmed. A Realtime alert may expose it; this has not been tested. The **Composite** alert type, which is also offered in the form, has not been explored.
2. **The Incidents page is not in the sidebar.** It loads at `http://localhost:5080/web/incidents`, but there was no menu link under Reliability. It was empty ("No active incidents") during testing.
3. **Email destinations need SMTP**, and **internal webhook addresses are blocked**. Use a public throwaway webhook for testing.
4. **Option A has no structured service fields.** Everything is inside `body`, and all errors come from one container in one namespace, so it cannot test over-grouping.
5. **`service_name` is blank for the log generator's logs.** Real STARS logs carry `k8s_namespace_name`, `k8s_deployment_name`, and `k8s_pod_name` instead. Grouping real alerts will need alerts that carry one of those fields, or a generator that emits a proper service field.
6. **The alert list is not final.** The Observability team is still defining real alerts. These alerts are stand-ins modeled on typical cascades.
7. **Single test environment.** Results come from a local Minikube cluster with synthetic data and should not be treated as production behavior.

---

## 9. Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Alert shows "would not trigger" | No matching events in the last minute. For Option A, confirm the generator pod is running. For Option B, run the test script, then refresh the preview within a minute. |
| An alert does not fire while others do | Check its filters in the **Summary** panel (Query Condition) on the right of the form. Wrong case (`error` vs `ERROR`), a wrong column name, a typo in the `scenario=` text, or a stray space. |
| Alerts fire constantly with no data | The threshold was left at `!=` `3`. Set it to `>=` `1`. |
| Option A alerts keep firing after testing | The generator is still running. `kubectl scale deployment error-generator -n stars --replicas=0`. |
| Destination test fails with an SMTP error | Email destination selected. Use a Web Hook. |
| Destination test fails with "internal domain" | Internal address used. Use a public receiver. |
| Script reports `Unauthorized` | Wrong email or password, or the placeholder email was left in. |
| No logs in `default` stream after a restart | Restart the collector: `kubectl rollout restart statefulset -n openobserve-collector o2c-openobserve-collector-gateway-collector` and `kubectl rollout restart daemonset -n openobserve-collector o2c-openobserve-collector-agent-collector`. |
| Logs are not searchable with `message = '...'` | The whole line is stored in `body`. Use `match_all('text')` or `body LIKE '%text%'`. |

---

## 10. Daily start and stop

**Stop (keeps everything):**
```bash
kubectl scale deployment error-generator -n stars --replicas=0   # if Option A is running
minikube stop
```
Do not run `minikube delete` or delete the `openobserve` namespace; that removes the instance, alerts, and data.

**Start:**
```bash
minikube start
kubectl get pods -n openobserve
kubectl get pods -n openobserve-collector
kubectl get pods -n stars
kubectl -n openobserve port-forward svc/openobserve 5080:5080
```
All pods should be `1/1 Running` before you test. Scale the error-generator back to 1 replica only when you are ready to run Option A.

---