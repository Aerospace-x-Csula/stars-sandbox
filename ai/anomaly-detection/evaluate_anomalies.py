"""Measure how accurate an OpenObserve anomaly detection rule is.

Compares what the rule flagged (the _anomalies stream) with when the
synthetic-metrics generator actually injected a problem (its
"CPU spike started/ended" and "Memory leak started/ended" log lines).

Reports:
  precision         share of flagged minutes that were real anomalies (specificity goal)
  recall            share of injected events that were caught
  F1                balance of precision and recall
  false alarms/hr   flagged minutes that were not near any event, per hour
  avg delay         time from an event starting to its first flag

It also re-scores the same results at sensitivity levels from 2 to 25 sigma
(OpenObserve's score is in sigma units), so you can see how tuning would
change the numbers without retraining.

Uses only the Python standard library. Example:

  export O2_USER="you@example.com"
  export O2_PASSWORD="your-password"
  python3 ai/anomaly-detection/evaluate_anomalies.py \
      --rule cpu-spike --run-id test01 --metric cpu --label default-sigma6
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

MARKERS = {
    "cpu": ("CPU spike started", "CPU spike ended"),
    "memory": ("Memory leak started", "Memory leak ended"),
}
RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
NAME_RE = re.compile(r"^[A-Za-z0-9 _.-]{1,128}$")


# ---------- OpenObserve API ----------

def search(args, sql, start, end, size=10000, missing_ok=False):
    """Run one SQL search against the OpenObserve _search API and return the rows.

    missing_ok: return [] instead of stopping if the stream does not exist yet."""
    url = "%s/api/%s/_search?type=logs" % (args.url.rstrip("/"), args.org)
    body = json.dumps({"query": {
        "sql": sql,
        "start_time": int(start.timestamp() * 1_000_000),
        "end_time": int(end.timestamp() * 1_000_000),
        "from": 0,
        "size": size,
    }}).encode()
    token = base64.b64encode(("%s:%s" % (args.user, args.password)).encode()).decode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": "Basic " + token,
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp).get("hits", [])
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        if missing_ok and "stream not found" in detail.lower():
            return []
        if e.code == 401:
            sys.exit("OpenObserve rejected the login (HTTP 401). Check O2_USER and O2_PASSWORD.")
        sys.exit("OpenObserve returned HTTP %s: %s\nQuery was:\n%s" % (e.code, detail, sql))
    except urllib.error.URLError as e:
        sys.exit("Could not reach OpenObserve at %s (%s). Is the port-forward running?"
                 % (args.url, e.reason))


def ts_from_row(value):
    """_timestamp comes back in microseconds since the epoch."""
    return datetime.fromtimestamp(int(value) / 1_000_000, tz=timezone.utc)


def ts_from_body(body):
    """Generator lines start with an ISO time, e.g. 2026-10-28T16:21:55Z."""
    m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z", body or "")
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


# ---------- Data loading ----------

def load_events(args, start, end):
    """Return the injected events as a list of (start, end) times."""
    on_msg, off_msg = MARKERS[args.metric]
    sql = ("SELECT _timestamp, body FROM \"default\" "
           "WHERE k8s_container_name = 'synthetic-metrics' "
           "AND body LIKE '%%run_id=%s %%' "
           "AND (body LIKE '%%%s%%' OR body LIKE '%%%s%%') "
           "ORDER BY _timestamp" % (args.run_id, on_msg, off_msg))
    rows = search(args, sql, start, end)
    marks = []
    for r in rows:
        t = ts_from_body(r.get("body")) or ts_from_row(r["_timestamp"])
        marks.append((t, on_msg in r.get("body", "")))
    marks.sort()

    events, opened = [], None
    for t, is_start in marks:
        if is_start and opened is None:
            opened = t
        elif not is_start and opened is not None:
            events.append((opened, t))
            opened = None
    if opened is not None:          # still running at the end of the window
        events.append((opened, end))
    return events, rows


def load_scores(args, start, end):
    """Return every scored point for the rule: (time, score, is_anomaly, value)."""
    sql = ("SELECT * FROM \"_anomalies\" WHERE anomaly_name = '%s' "
           "ORDER BY _timestamp" % args.rule)
    rows = search(args, sql, start, end, missing_ok=True)   # stream appears after the first rule runs
    points = []
    for r in rows:
        flag = r.get("is_anomaly")
        if isinstance(flag, str):
            flag = flag.lower() == "true"
        points.append({
            "time": ts_from_row(r["_timestamp"]),
            "score": float(r.get("score") or 0),
            "flag": bool(flag),
            "value": r.get("actual_value"),
            "threshold": float(r["threshold_value"]) if r.get("threshold_value") is not None else None,
        })
    return points, rows


# ---------- Scoring ----------

def evaluate(points, events, flag_of, resolution, tolerance, hours):
    """Score one set of flags against the injected events."""
    def near_event(t):
        b_start, b_end = t, t + resolution
        for i, (e_start, e_end) in enumerate(events):
            if b_start < e_end + tolerance and b_end > e_start:
                return i
        return None

    flagged = [p for p in points if flag_of(p)]
    tp = fp = 0
    first_flag = {}
    for p in flagged:
        i = near_event(p["time"])
        if i is None:
            fp += 1
        else:
            tp += 1
            first_flag.setdefault(i, p["time"])

    caught = len(first_flag)
    precision = tp / len(flagged) if flagged else 0.0
    recall = caught / len(events) if events else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    delays = [max(0.0, ((t + resolution) - events[i][0]).total_seconds())
              for i, t in first_flag.items()]
    return {
        "flags": len(flagged), "tp": tp, "fp": fp,
        "caught": caught, "events": len(events),
        "precision": precision, "recall": recall, "f1": f1,
        "fa_per_hr": fp / hours if hours else 0.0,
        "delay_s": sum(delays) / len(delays) if delays else None,
    }


def fmt_row(name, m):
    delay = "-" if m["delay_s"] is None else "%.0f s" % m["delay_s"]
    return "| %s | %d | %d/%d | %.2f | %.2f | %.2f | %.2f | %s |" % (
        name, m["flags"], m["caught"], m["events"], m["precision"], m["recall"],
        m["f1"], m["fa_per_hr"], delay)


# ---------- Main ----------

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rule", required=True, help="Anomaly rule name exactly as shown in OpenObserve")
    p.add_argument("--run-id", required=True, help="synthetic-metrics RUN_ID of the test run, e.g. test01")
    p.add_argument("--metric", choices=MARKERS, default="cpu")
    p.add_argument("--label", default="run", help="Name for this result, e.g. the sensitivity setting")
    p.add_argument("--hours", type=float, default=3, help="How many hours back to look (default 3)")
    p.add_argument("--resolution", type=int, default=60, help="Rule's detection resolution in seconds (default 60)")
    p.add_argument("--tolerance", type=int, default=60,
                   help="Seconds after an event ends that a flag still counts as a hit (default 60)")
    p.add_argument("--inspect", action="store_true", help="Print a few raw rows and stop (to check field names)")
    p.add_argument("--url", default=os.getenv("O2_URL", "http://127.0.0.1:5080"))
    p.add_argument("--org", default=os.getenv("O2_ORG", "default"))
    p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = p.parse_args()

    args.user = os.getenv("O2_USER")
    args.password = os.getenv("O2_PASSWORD")
    if not args.user or not args.password:
        sys.exit("Set O2_USER and O2_PASSWORD first (your OpenObserve login).")
    if not RUN_ID_RE.match(args.run_id):
        sys.exit("--run-id may only contain letters, digits, _ and -")
    if not NAME_RE.match(args.rule):
        sys.exit("--rule may only contain letters, digits, spaces, _ . and -")

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=args.hours)
    events, event_rows = load_events(args, start, end)
    points, score_rows = load_scores(args, start, end)

    if args.inspect:
        print("Event marker rows found: %d" % len(event_rows))
        for r in event_rows[:4]:
            print("  ", r.get("body"))
        print("\n_anomalies rows found for rule '%s': %d" % (args.rule, len(score_rows)))
        if not score_rows:
            print("   (none yet: the _anomalies stream appears after a rule has trained and run)")
        for r in score_rows[:3]:
            print("  ", json.dumps(r, default=str))
        return

    if not events:
        sys.exit("No '%s' events found for run_id=%s in the last %.1f h. "
                 "Check --run-id and that ANOMALIES=on." % (args.metric, args.run_id, args.hours))
    if not points:
        sys.exit("No _anomalies rows for rule '%s' in the last %.1f h. "
                 "Check the rule name, and that it has been running." % (args.rule, args.hours))

    # Only score the time the rule was actually running
    first, last = points[0]["time"], points[-1]["time"]
    events = [e for e in events if e[1] > first and e[0] < last + timedelta(seconds=args.resolution)]
    hours = max((last - first).total_seconds() / 3600, 1e-9)
    res = timedelta(seconds=args.resolution)
    tol = timedelta(seconds=args.tolerance)

    header = ("| Setting | Flags | Events caught | Precision | Recall | F1 | False alarms/hr | Avg delay |\n"
              "|---|---|---|---|---|---|---|---|")
    rows = [fmt_row("OpenObserve flags (as configured)",
                    evaluate(points, events, lambda q: q["flag"], res, tol, hours))]

    # What-if: re-score the same points at other sensitivity levels.
    # OpenObserve's score is in sigma units (threshold_value matches the rule's k),
    # so "score > k" is what the rule would flag at Level = k sigma.
    current_k = points[-1].get("threshold")
    for k in (2, 3, 4, 5, 6, 8, 10, 15, 20, 25):
        m = evaluate(points, events, lambda q, c=k: q["score"] > c, res, tol, hours)
        mark = " (current)" if current_k is not None and abs(current_k - k) < 1e-9 else ""
        rows.append(fmt_row("Level %d sigma%s" % (k, mark), m))

    # How close normal minutes came to being flagged, and how weak the weakest real hit was
    def near_any(t):
        return any(t < e_end + tol and t + res > e_start for e_start, e_end in events)
    normal = [q["score"] for q in points if not near_any(q["time"])]
    event_peaks = []
    for e_start, e_end in events:
        s = [q["score"] for q in points if q["time"] < e_end + tol and q["time"] + res > e_start]
        if s:
            event_peaks.append(max(s))
    margin = []
    if normal:
        margin.append("- Highest score on a normal minute: %.2f sigma (%d normal minutes)"
                      % (max(normal), len(normal)))
    if event_peaks:
        margin.append("- Lowest peak score of a real spike: %.2f sigma (%d spikes scored)"
                      % (min(event_peaks), len(event_peaks)))
    if normal and event_peaks:
        lo, hi = max(normal), min(event_peaks)
        if hi > lo:
            margin.append("- Any level between %.2f and %.2f sigma separates every spike from every normal minute"
                          % (lo, hi))
        else:
            margin.append("- No single level separates them: some normal minutes score above the weakest spike")

    report = "\n".join([
        "# Anomaly detection accuracy: %s" % args.label,
        "",
        "- Rule: `%s` (metric: %s, resolution: %ss)" % (args.rule, args.metric, args.resolution),
        "- Test run: `run_id=%s`" % args.run_id,
        "- Scored window: %s to %s UTC (%.1f h, %d scored points)"
        % (first.strftime("%Y-%m-%d %H:%M"), last.strftime("%H:%M"), hours, len(points)),
        "- Injected events in window: %d" % len(events),
        "- A flag counts as a hit if its bucket overlaps an event or the %ss after it." % args.tolerance,
        "",
        header,
        *rows,
        "",
        "The first row is what OpenObserve actually alerted on. The other rows re-score the same",
        "points at other sensitivity levels (score is in sigma units), to show what a stricter",
        "or looser setting would do without retraining.",
        "",
        "## Separation",
        "",
        *margin,
    ])
    print(report)

    os.makedirs(args.out, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", args.label)
    path = os.path.join(args.out, "%s-%s.md" % (args.run_id, safe))
    with open(path, "w") as f:
        f.write(report + "\n")
    print("\nSaved to %s" % path)


if __name__ == "__main__":
    main()
