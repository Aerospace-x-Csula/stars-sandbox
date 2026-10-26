# STARS Log Generator: Failure Scenario Test Catalog

Documentation of the failure scenarios supported by the log-generator, with the expected logs and behavior for each. The catalog at the bottom is written so its pass/fail criteria can be turned into automated checks later.

## Contents

1. [How the generator works](#how-the-generator-works)
2. [Log format](#log-format)
3. [How to trigger a scenario](#how-to-trigger-a-scenario)
4. [Scenarios](#scenarios): `warn`, `error`, `error-spike`, `connectivity`, `crash`
5. [Test case catalog](#test-case-catalog)
6. [Notes and observations](#notes-and-observations)

---

## How the generator works

The container runs a single shell script as PID 1. It does two things in a loop:

1. **Heartbeat:** emits a `STARS heartbeat` INFO line roughly every 5 seconds with an incrementing `count`.
2. **Scenario handling:** checks `/tmp/stars-control` once per tick (about 1 second) for a queued request and runs **at most one** scenario per tick.

Scenarios are triggered on demand with `/tmp/stars-trigger`, which writes a request file that the main loop picks up. Requests are ephemeral: on every container start the control directory is cleaned, so **no scenario repeats automatically after a restart**.

## Log format

Scenario logs:

```
<UTC timestamp> level=<LEVEL> service=log-generator scenario=<scenario> run_id=<RUN_ID> message="<message>"
```

Heartbeat logs (no `scenario` or `run_id` fields):

```
<UTC timestamp> level=INFO service=log-generator message="STARS heartbeat" count=<N>
```

Timestamps are UTC, ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`).

Every non-crash scenario follows the same envelope:

```
INFO  ... message="Scenario started"
<scenario-specific lines>
INFO  ... message="Scenario completed"
```

## How to trigger a scenario

```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger <SCENARIO> <RUN_ID>
```

| Argument | Allowed values |
|----------|----------------|
| `SCENARIO` | `warn`, `error`, `error-spike`, `connectivity`, `crash` |
| `RUN_ID` | Letters, digits, `_` and `-` only; max 64 characters. Use a unique ID per run so logs can be filtered. |

The trigger command only **queues** the request (it prints `Queued scenario=<scenario> run_id=<RUN_ID>`). The scenario logs appear in the container's log stream within about 1 second.

To watch output live:

```bash
kubectl -n stars logs -f deployment/log-generator -c log-generator
```

To check one run after the fact:

```bash
kubectl -n stars logs deployment/log-generator -c log-generator | grep 'run_id=<RUN_ID>'
```

---

## Scenarios

### 1. `warn`

**Purpose:** Emit a single warning-level log to simulate a degraded condition.

**Trigger:**
```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger warn warn01
```

**Observed output:**
```
2026-10-22T00:26:36Z level=INFO service=log-generator message="STARS heartbeat" count=144
2026-10-22T00:26:40Z level=INFO service=log-generator scenario=warn run_id=warn01 message="Scenario started"
2026-10-22T00:26:40Z level=WARN service=log-generator scenario=warn run_id=warn01 message="On-demand warning; synthetic degraded condition"
2026-10-22T00:26:40Z level=INFO service=log-generator scenario=warn run_id=warn01 message="Scenario completed"
2026-10-22T00:26:41Z level=INFO service=log-generator message="STARS heartbeat" count=145
```

**Expected logs:**
- 1 `INFO` "Scenario started"
- Exactly 1 `WARN` with message `On-demand warning; synthetic degraded condition`
- 1 `INFO` "Scenario completed"
- No `ERROR` lines

**Expected behavior:** Container keeps running. Heartbeats continue. No restart.

---

### 2. `error`

**Purpose:** Emit a single error-level log to simulate an application failure.

**Trigger:**
```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger error error01
```

**Observed output:**
```
2026-10-22T00:28:47Z level=INFO service=log-generator message="STARS heartbeat" count=170
2026-10-22T00:28:49Z level=INFO service=log-generator scenario=error run_id=error01 message="Scenario started"
2026-10-22T00:28:49Z level=ERROR service=log-generator scenario=error run_id=error01 message="On-demand error; synthetic application failure"
2026-10-22T00:28:49Z level=INFO service=log-generator scenario=error run_id=error01 message="Scenario completed"
2026-10-22T00:28:52Z level=INFO service=log-generator message="STARS heartbeat" count=171
```

**Expected logs:**
- 1 `INFO` "Scenario started"
- Exactly 1 `ERROR` with message `On-demand error; synthetic application failure`
- 1 `INFO` "Scenario completed"

**Expected behavior:** Container keeps running. Heartbeats continue. No restart.

---

### 3. `error-spike`

**Purpose:** Emit a burst of errors in a very short time to simulate an error-rate spike.

**Trigger:**
```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger error-spike spike01
```

**Observed output (abridged; lines 3 through 19 follow the same pattern):**
```
2026-10-22T00:31:02Z level=INFO service=log-generator message="STARS heartbeat" count=197
2026-10-22T00:31:03Z level=INFO service=log-generator scenario=error-spike run_id=spike01 message="Scenario started"
2026-10-22T00:31:03Z level=ERROR service=log-generator scenario=error-spike run_id=spike01 message="Injected application error 1 of 20"
2026-10-22T00:31:03Z level=ERROR service=log-generator scenario=error-spike run_id=spike01 message="Injected application error 2 of 20"
...
2026-10-22T00:31:03Z level=ERROR service=log-generator scenario=error-spike run_id=spike01 message="Injected application error 20 of 20"
2026-10-22T00:31:03Z level=INFO service=log-generator scenario=error-spike run_id=spike01 message="Scenario completed"
2026-10-22T00:31:07Z level=INFO service=log-generator message="STARS heartbeat" count=198
```

**Expected logs:**
- 1 `INFO` "Scenario started"
- Exactly 20 `ERROR` lines, numbered `Injected application error N of 20` for N = 1 to 20, in order
- 1 `INFO` "Scenario completed"
- All 20 errors land within the same second (burst, no delay between them)

**Expected behavior:** Container keeps running. Heartbeats continue. No restart.

---

### 4. `connectivity`

**Purpose:** Simulate a network connection failure. The generator attempts an HTTP request to a closed loopback port (`127.0.0.1:1`), which always fails. No external network target is used.

**Trigger:**
```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger connectivity network01
```

**Observed output:**
```
2026-10-22T00:33:52Z level=INFO service=log-generator message="STARS heartbeat" count=231
2026-10-22T00:33:53Z level=INFO service=log-generator scenario=connectivity run_id=network01 message="Scenario started"
2026-10-22T00:33:53Z level=ERROR service=log-generator scenario=connectivity run_id=network01 message="Controlled connection failure target=127.0.0.1:1 wget_exit=1"
2026-10-22T00:33:53Z level=INFO service=log-generator scenario=connectivity run_id=network01 message="Scenario completed"
2026-10-22T00:33:57Z level=INFO service=log-generator message="STARS heartbeat" count=232
```

**Expected logs:**
- 1 `INFO` "Scenario started"
- Exactly 1 `ERROR` with message `Controlled connection failure target=127.0.0.1:1 wget_exit=1`
- 1 `INFO` "Scenario completed"

**Alternate path (not observed):** If the request were ever to succeed, the script would log a `WARN` with `Unexpected HTTP success; connectivity test invalid` instead of the `ERROR`. Seeing this message means the test environment is invalid, not that the generator is broken.

**Expected behavior:** Container keeps running. Heartbeats continue. No restart.

---

### 5. `crash`

**Purpose:** Simulate a container crash. The generator logs an error and exits with a non-zero code, so Kubernetes restarts the container.

**Trigger:**
```bash
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger crash crash01
```

**Before the crash:**
```
NAME                             READY   STATUS    RESTARTS   AGE
log-generator-74b84654d9-gj9hx   1/1     Running   0          20m
```

**Observed output:**
```
2026-10-22T00:36:17Z level=INFO service=log-generator message="STARS heartbeat" count=260
2026-10-22T00:36:21Z level=INFO service=log-generator scenario=crash run_id=crash01 message="Scenario started"
2026-10-22T00:36:21Z level=ERROR service=log-generator scenario=crash run_id=crash01 message="Injected container crash; exiting with code 42"
```

The log stream stops here. There is **no** "Scenario completed" line, because the process exits before reaching it.

**After the crash:**
```
NAME                             READY   STATUS    RESTARTS      AGE
log-generator-74b84654d9-gj9hx   1/1     Running   1 (62s ago)   22m
```

**From `kubectl describe pod`:**
```
State:          Running
  Started:      Wed, 21 Oct 2026 17:36:22 -0700
Last State:     Terminated
  Reason:       Error
  Exit Code:    42
  Started:      Wed, 21 Oct 2026 17:14:40 -0700
  Finished:     Wed, 21 Oct 2026 17:36:21 -0700
Ready:          True
Restart Count:  1
```

Events show `Created` and `Started` with `(x2 over 24m)`, confirming the container was restarted in place (same pod, same node).

**Logs after recovery** (heartbeat counter restarted from 1, since the process is new):
```
2026-10-22T00:40:52Z level=INFO service=log-generator message="STARS heartbeat" count=55
2026-10-22T00:40:57Z level=INFO service=log-generator message="STARS heartbeat" count=56
...
2026-10-22T00:42:27Z level=INFO service=log-generator message="STARS heartbeat" count=74
```

**Expected logs:**
- 1 `INFO` "Scenario started"
- Exactly 1 `ERROR` with message `Injected container crash; exiting with code 42`
- **No** "Scenario completed" line
- After restart: a new `STARS generator started` line and heartbeats resume with `count` reset to low values

**Expected behavior:**
- Container process exits with **code 42**
- Pod `RESTARTS` increases by 1
- Pod returns to `1/1 Running` within a few seconds (the gap between crash and restart was about 1 second in the observed run)
- The crash does **not** repeat after restart (request files are cleaned on startup)

**How to verify:**
```bash
kubectl get pods -n stars
kubectl describe pod <pod-name> -n stars | grep -A4 "Last State"
kubectl logs <pod-name> -n stars --previous   # logs from the crashed container
```

---

## Test case catalog

Use a **unique RUN_ID per execution** so each check only looks at its own lines. "Window" means time after the trigger command returns.

| ID | Scenario | Trigger (`/tmp/stars-trigger ...`) | Expected log output | Expected behavior | Pass criteria |
|----|----------|------------------------------------|---------------------|-------------------|---------------|
| TC-01 | `warn` | `warn <RUN_ID>` | `Scenario started` (INFO), 1 WARN `On-demand warning; synthetic degraded condition`, `Scenario completed` (INFO) | Container stays up; no restart | Within 5s: exactly 1 line with `level=WARN scenario=warn run_id=<RUN_ID>`; 0 ERROR lines for that run_id; started and completed lines both present, in order; restart count unchanged |

| TC-02 | `error` | `error <RUN_ID>` | `Scenario started` (INFO), 1 ERROR `On-demand error; synthetic application failure`, `Scenario completed` (INFO) | Container stays up; no restart | Within 5s: exactly 1 line with `level=ERROR scenario=error run_id=<RUN_ID>`; started and completed lines both present, in order; restart count unchanged |

| TC-03 | `error-spike` | `error-spike <RUN_ID>` | `Scenario started`, 20 ERROR lines `Injected application error N of 20` (N=1..20), `Scenario completed` | Burst of errors in one second; container stays up; no restart | Within 5s: exactly 20 lines with `level=ERROR scenario=error-spike run_id=<RUN_ID>`; N values 1..20 each appear once, in order; all 20 within a 2s span; completed line present; restart count unchanged |

| TC-04 | `connectivity` | `connectivity <RUN_ID>` | `Scenario started`, 1 ERROR `Controlled connection failure target=127.0.0.1:1 wget_exit=1`, `Scenario completed` | Container stays up; no restart; no external traffic | Within 10s: exactly 1 ERROR line for run_id containing `target=127.0.0.1:1` and `wget_exit=1`; 0 lines containing `Unexpected HTTP success`; completed line present; restart count unchanged |

| TC-05 | `crash` | `crash <RUN_ID>` | `Scenario started`, 1 ERROR `Injected container crash; exiting with code 42`, no `Scenario completed` | Container exits with code 42, then restarts automatically | Within 60s: ERROR line present; **no** `Scenario completed` for that run_id; pod `lastState.terminated.exitCode` = 42; restart count increased by exactly 1; pod back to `1/1 Running`; heartbeats resume after restart; scenario does not re-run after restart |

> **Status:** TC-01 to TC-05 are based on observed runs (outputs above).

### Example automated check (TC-03)

```bash
RUN_ID="spike-$(date +%s)"
kubectl -n stars exec deployment/log-generator -c log-generator -- /tmp/stars-trigger error-spike "$RUN_ID"
sleep 3
COUNT=$(kubectl -n stars logs deployment/log-generator -c log-generator \
  | grep "run_id=$RUN_ID" | grep -c "level=ERROR")
[ "$COUNT" -eq 20 ] && echo "PASS" || echo "FAIL (found $COUNT errors, expected 20)"
```

---

## Notes and observations

- **Pod status stays `Running` after a crash.** Kubernetes restarts the container in place, so the only visible signs are the `RESTARTS` counter and the previous container's `Exit Code: 42`. Tests must check the restart count and exit code, not pod status alone.
- **Heartbeat counter resets on restart.** Before the crash the count was around 260; after the restart it started again from 1. A drop in `count` indicates a container restart.
- **Crash scenario produces no completion log.** The absence of `Scenario completed` is part of the expected result.
- **The trigger is asynchronous.** The `kubectl exec` command returns as soon as the request is queued. The scenario runs on the next loop tick (up to about 1 second later), so tests should wait briefly before checking logs.
- **One scenario per tick.** If several triggers are queued at once, they are processed one per second, not in parallel.
- **Heartbeat interval is approximately 5 seconds**, not exact, because of the 1-second sleep loop. Use a tolerance in automated checks.
- **Timezones.** Log timestamps are UTC (`Z`); `kubectl describe` shows local time (`-0700` in the observed run).
- **Connectivity scenario is self-contained.** It targets a closed loopback port, so it never touches an external network and fails the same way every time.
