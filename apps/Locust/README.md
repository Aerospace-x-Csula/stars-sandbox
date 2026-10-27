# Load testing the `stars` app on minikube with Locust

Generate HTTP traffic against an application running in the `stars` namespace of a local minikube cluster. Locust runs **inside** the cluster, so it reaches the app through cluster DNS with no ingress needed.

It simulates four scenarios:

| Scenario | What it does |
|---|---|
| `normal` | Steady, human-paced requests, no errors |
| `high-traffic` | Many users sending near-continuous requests |
| `failing` | Server errors (500), missing pages (404) and requests that time out |
| `mixed` | All three user types at once |

Each scenario can be run from the Locust web UI or with no UI as a Kubernetes Job.

> **Placeholders:** the test app is httpbin, so the endpoints in `apps/Locust/locustfile.py` (`/`, `/get`, `/status/500`, `/delay/5`) are httpbin's. If you test your own app, edit `apps/Locust/stars-app.yaml` and replace those paths.

## Prerequisites

- [minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

**Run every command from the folder that contains this README.**

## Windows and macOS

Every command here works the same in macOS Terminal (zsh or bash), Windows PowerShell and Windows cmd:

- Paths use forward slashes (`apps/Locust/locust.yaml`), which kubectl accepts on Windows.
- One command per line. There are no `\` line continuations, `&&`, `grep` or `export`, which differ between shells.
- `locust/locustfile.py` is ASCII-only, so PowerShell 5.1 can pipe it without corrupting characters. Keep it that way when you edit it.
- Stop a running `port-forward` or `logs -f` with Ctrl+C on both systems.

## 1. Prepare the cluster

```bash
minikube start
minikube addons enable metrics-server
kubectl apply -f apps/Locust/namespace.yaml
kubectl apply -f apps/Locust/stars-app.yaml
kubectl -n stars rollout status deployment/stars-app
```

The metrics-server addon lets you watch load with `kubectl top`. `apps/Locust/stars-app.yaml` deploys httpbin as `stars-app` with a startup probe and a readiness probe on `/get`, plus a Service so Locust can reach it at `http://stars-app.stars.svc.cluster.local`.

## 2. The locustfile

`locust/locustfile.py` has one user class per traffic pattern:

| Class | Behavior |
|---|---|
| `NormalUser` | `homepage` and `list_items`, 1-3 s between requests, no errors |
| `HighTrafficUser` | Same requests, 0.05-0.3 s between them. Use with many users |
| `FailingUser` | `server_error` (500), `missing_page` (404), `slow_request` (see below) |

`slow_request` calls `/delay/5` with a 1 second client timeout. The server waits 5 seconds, the client gives up after 1, and Locust records a failed request with status 0 and a timeout error. On your own app, replace it with a genuinely slow endpoint or remove it.

Every run also gets a `run_id` (random, 8 characters) and a `scenario` label. See [Test start and stop logs](#6-test-start-and-stop-logs).

## 3. Deploy Locust into the namespace

Optional: to send run events and request logs to OpenObserve, first create a Secret (change the values to match your OpenObserve):

```bash
kubectl -n stars create secret generic openobserve-credentials --from-literal=url=http://openobserve-openobserve-standalone.stars.svc.cluster.local:5080/api/default --from-literal=user=root@example.com --from-literal=password="Complexpass#123"
```
Skip this if you aren't using OpenObserve. Locust works without it. If you create the Secret later, run `kubectl -n stars rollout restart deployment/locust`.

Create (or update) the ConfigMap from `locust/locustfile.py`, then deploy:

```bash
kubectl -n stars create configmap locustfile --from-file=locust/locustfile.py --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f apps/Locust/locust.yaml
kubectl -n stars rollout status deployment/locust
kubectl -n stars port-forward svc/locust 8089:8089
```

Open <http://localhost:8089>. The deployment has a startup probe and a readiness probe on the web UI, so `rollout status` only finishes once the UI is answering.

The `--class-picker` flag in `apps/Locust/locust.yaml` is what shows the **User Classes** selector in the UI. Without it, Locust runs every class at once.

## 4. Run each scenario

### In the web UI

Tick the user class, set the users and ramp up, and optionally fill in the **Scenario** field so the run is labeled (the default label is `adhoc`). The Scenario field is only a label; the ticked classes decide what runs.

| Scenario | Tick | Users | Ramp up |
|---|---|---|---|
| `normal` | `NormalUser` | 20 | 2/s |
| `high-traffic` | `HighTrafficUser` | 200 | 20/s |
| `failing` | `FailingUser` | 20 | 5/s |
| `mixed` | all three | 50 | 5/s |

While a test runs, watch the app's resource usage in another terminal:

```bash
kubectl -n stars top pods
```

### Without the UI (headless)

Each scenario has a Job in `apps/Locust/jobs/` that runs for 5 minutes, prints a stats table in its logs, and exits. The three lines for each are: remove any previous run of that Job, start it, follow its logs. If the logs command says the container is still creating, wait a few seconds and run it again.

**normal** (20 users, 2/s)

```bash
kubectl -n stars delete job locust-normal --ignore-not-found
kubectl apply -f apps/Locust/jobs/normal.yaml
kubectl -n stars logs -f job/locust-normal
```

**high-traffic** (200 users, 20/s)

```bash
kubectl -n stars delete job locust-high-traffic --ignore-not-found
kubectl apply -f apps/Locust/jobs/high-traffic.yaml
kubectl -n stars logs -f job/locust-high-traffic
```

**failing** (20 users, 5/s)

```bash
kubectl -n stars delete job locust-failing --ignore-not-found
kubectl apply -f apps/Locust/jobs/failing.yaml
kubectl -n stars logs -f job/locust-failing
```

**mixed** (50 users, 5/s, all three classes)

```bash
kubectl -n stars delete job locust-mixed --ignore-not-found
kubectl apply -f apps/Locust/jobs/mixed.yaml
kubectl -n stars logs -f job/locust-mixed
```
#Make sure to delete any jobs you've created once you're done.
```bash
kubectl -n stars delete job locust-normal --ignore-not-found
kubectl -n stars delete job locust-high-traffic --ignore-not-found
kubectl -n stars delete job locust-failing --ignore-not-found
kubectl -n stars delete job locust-mixed --ignore-not-found
```


To change the number of users, ramp up or duration, edit `-u`, `-r` and `-t` in the Job file. The `failing` and `mixed` Jobs pass `--exit-code-on-error 0`, because failures are expected there and shouldn't mark the Job as failed.

After you edit `locust/locustfile.py`, rerun the ConfigMap command from step 3. Jobs pick up the new file when they start; for the web UI also run `kubectl -n stars rollout restart deployment/locust`.

## 5. Simulate failures in the app itself

The `failing` scenario only sends bad *requests*. To see how the app copes when the infrastructure fails, run `normal` and break things mid-test:

```bash
kubectl -n stars scale deployment/stars-app --replicas=0
kubectl -n stars scale deployment/stars-app --replicas=3
kubectl -n stars delete pod -l app=stars-app
```

The first command causes a total outage (connection errors), the second recovers, the third kills the pods so Kubernetes replaces them. Because `stars-app` has a readiness probe, new pods only receive traffic once they answer `/get`.

## 6. Test start and stop logs

Each test start and stop is logged by Locust with the `run_id` and `scenario`, as one JSON line prefixed with `loadtest`:

```
loadtest {"event": "test_start", "run_id": "a1b2c3d4", "scenario": "normal", "host": "http://stars-app.stars.svc.cluster.local", "users": 20}
loadtest {"event": "test_stop", "run_id": "a1b2c3d4", "scenario": "normal", "duration_s": 300.1, "requests": 2400, "failures": 0, "avg_ms": 8.2, "p95_ms": 14}
```

(The numbers above are an illustration of the format.) See them with:

```bash
kubectl -n stars logs deploy/locust
kubectl -n stars logs job/locust-normal
```

If you configured OpenObserve, the same events go to the `locust_runs` stream.

## 7. Search the traffic logs in OpenObserve

With the Secret from step 3 in place, every request is sent to the `locust` stream, tagged with `run_id` and `scenario`. Ready-to-paste searches (traffic logs, failed requests, runs, summaries) are in [`openobserve/queries.md`](openobserve/queries.md). The main one:

```sql
SELECT _timestamp, run_id, scenario, method, name, status_code,
       response_time_ms, failed, error
FROM "locust"
ORDER BY _timestamp DESC
```

## Tips

- **Scaling the generator:** one Locust process tops out around a few thousand requests per second, and minikube will likely limit you first. Start with more headroom using `minikube start --cpus=4 --memory=8g`. For larger loads, Locust supports a master plus worker pods.
- **Auth and POST bodies:** add headers or logins in `on_start()` or in the task calls, for example `self.client.post("/login", json={...})`.
- **Logs from the app:** `kubectl -n stars logs -f deploy/stars-app`.


