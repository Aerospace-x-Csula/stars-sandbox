from collections import deque
import logging
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException

WINDOW_SECONDS = 1800         # 30-minute sliding window for the trigger
MAX_HEALS_IN_WINDOW = 3       # heals allowed inside the window
STABLE_RESET_SECONDS = 600    # healthy time required to clear a block (10 minutes)
CHECK_INTERVAL_SECONDS = 10   # polling frequency

# Configure logging format for clean output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Tracker structure: 
# {(namespace, app): {"heals": deque(), "blocked": bool, "healthy_since": float | None}}
heal_tracker = {}

def get_app_key(pod):
    """Extracts a stable tracking key based on namespace and app labels."""
    labels = pod.metadata.labels or {}
    app = labels.get("app") or labels.get("app.kubernetes.io/name")
    return (pod.metadata.namespace, app) if app else None

def get_entry(key):
    """Retrieves or initializes the tracking entry for a given app key."""
    return heal_tracker.setdefault(
        key, {"heals": deque(), "blocked": False, "healthy_since": None}
    )

def can_heal(entry, now):
    """Evaluates the sliding window circuit breaker and updates block state."""
    while entry["heals"] and now - entry["heals"][0] > WINDOW_SECONDS:
        entry["heals"].popleft()

    if len(entry["heals"]) >= MAX_HEALS_IN_WINDOW:
        entry["blocked"] = True

    return not entry["blocked"]

def update_reset_state(unhealthy_keys, now):
    """Runs once per loop to manage recovery and clear blocks after stable health."""
    for key, entry in list(heal_tracker.items()):
        if key in unhealthy_keys:
            entry["healthy_since"] = None
        elif entry["healthy_since"] is None:
            entry["healthy_since"] = now
        elif now - entry["healthy_since"] >= STABLE_RESET_SECONDS:
            del heal_tracker[key]

def log_audit_trail(trigger, evidence, decision, action, result, approval="Automated (Low-Risk)"):
    print("\n--- [AUDIT TRAIL ENTRY] ---")
    print(f"Trigger:     {trigger}")
    print(f"Evidence:    {evidence}")
    print(f"Decision:    {decision}")
    print(f"Action:      {action}")
    print(f"Result:      {result}")
    print(f"Approval:    {approval}")
    print("---------------------------\n")

def is_pod_unhealthy(pod):

    phase = pod.status.phase
    if phase in ["Failed", "Unknown"]:
        return True, f"Pod phase is '{phase}'"

    if pod.status.container_statuses:
        for container in pod.status.container_statuses:
            if container.state.waiting:
                reason = container.state.waiting.reason
                if reason in ["CrashLoopBackOff", "ImagePullBackOff", "Error"]:
                    return True, f"Container '{container.name}' waiting state: {reason}"
            
            if container.state.terminated and container.state.terminated.exit_code != 0:
                return True, f"Container '{container.name}' terminated with exit code {container.state.terminated.exit_code}"

            if not container.ready and phase == "Running":
                return True, f"Container '{container.name}' readiness probe failing (ready=False)"

    return False, "Healthy"

def main():
    try:
        config.load_kube_config()
        logging.info("Successfully connected to local Kubernetes cluster.")
    except Exception as e:
        logging.error(f"Failed to load kubeconfig: {e}")
        exit(1)

    v1 = client.CoreV1Api()
    logging.info("Starting local healer...")

    while True:
        now = time.time()
        unhealthy_keys = set()
        
        try:
            ret = v1.list_pod_for_all_namespaces(label_selector="auto-heal=true", watch=False)
            
            for pod in ret.items:
                namespace = pod.metadata.namespace
                pod_name = pod.metadata.name
                
                # Skip pods that are currently terminating
                if pod.metadata.deletion_timestamp:
                    continue

                # Skip unmanaged / ownerless pods (must have ownerReferences like a ReplicaSet/Deployment)
                if not pod.metadata.owner_references:
                    continue

                # Skip pods currently starting up (ContainerCreating, PodInitializing)
                is_starting = False
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        if container.state.waiting and container.state.waiting.reason in ["ContainerCreating", "PodInitializing"]:
                            is_starting = True
                            break
                if is_starting:
                    continue

                labels = pod.metadata.labels or {}
                if labels.get("auto-heal") != "true":
                    continue
                
                app_key = get_app_key(pod)
                if not app_key:
                    logging.warning(f"Pod {pod_name} in namespace {namespace} has auto-heal=true but is missing a valid 'app' label. Skipping.")
                    continue
                
                unhealthy, reason = is_pod_unhealthy(pod)

                if unhealthy:
                    entry = get_entry(app_key)
                    
                    # Limit to one heal per app per loop pass
                    if app_key in unhealthy_keys:
                        continue
                    unhealthy_keys.add(app_key)
                    
                    if not can_heal(entry, now):
                        log_audit_trail(
                            trigger=f"Unhealthy Pod Detected ({pod_name})",
                            evidence=f"{reason} | App: {app_key[1]} (Namespace: {app_key[0]}) | Heals in window: {len(entry['heals'])}",
                            decision="Circuit Breaker Tripped: Max heal limit reached in 30m window. Escalation required.",
                            action="NO_ACTION (Halted auto-recovery)",
                            result="BLOCKED_BY_CIRCUIT_BREAKER"
                        )
                        continue
                    
                    logging.warning(f"Unhealthy pod '{pod_name}' detected for app '{app_key[1]}'. Triggering self-healing...")
                    
                    try:
                        v1.delete_namespaced_pod(
                            name=pod_name,
                            namespace=namespace,
                            body=client.V1DeleteOptions()
                        )
                        entry["heals"].append(now)
                        
                        log_audit_trail(
                            trigger="Pod Degradation / Failure",
                            evidence=f"Pod: {pod_name} | App: {app_key[1]} | Reason: {reason}",
                            decision=f"Issue programmatic pod deletion (Heal count: {len(entry['heals'])}/{MAX_HEALS_IN_WINDOW})",
                            action=f"v1.delete_namespaced_pod('{pod_name}', '{namespace}')",
                            result="SUCCESS (Pod deletion requested, k8s recreation pending)"
                        )
                    except ApiException as api_err:
                        logging.error(f"Failed to delete pod {pod_name}: {api_err}")

            update_reset_state(unhealthy_keys, now)

        except ApiException as e:
            logging.error(f"Kubernetes API Exception: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in healer loop: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()