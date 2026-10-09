import time
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Configure logging format for clean output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configuration Constants
TARGET_NAMESPACE = "stars"
CHECK_INTERVAL_SECONDS = 10
MAX_RESTART_LIMIT = 3

# Audit state tracker: {pod_name: restart_count}
restart_tracker = {}

def load_k8s_config():
    """Loads local kubeconfig (Minikube / out-of-cluster context)."""
    try:
        config.load_kube_config()
        logging.info("Successfully connected to local Kubernetes cluster.")
    except Exception as e:
        logging.error(f"Failed to load kubeconfig: {e}")
        exit(1)

def log_audit_trail(trigger, evidence, decision, action, result, approval="Automated (Low-Risk)"):
    """Prints a structured audit log entry"""
    print("\n--- [AUDIT TRAIL ENTRY] ---")
    print(f"Trigger:     {trigger}")
    print(f"Evidence:    {evidence}")
    print(f"Decision:    {decision}")
    print(f"Action:      {action}")
    print(f"Result:      {result}")
    print(f"Approval:    {approval}")
    print("---------------------------\n")

def is_pod_unhealthy(pod):
    """
    Evaluates pod health using phase and container status conditions.
    Returns (bool_is_unhealthy, reason_string)
    """
    # 1. Check top-level pod phase
    if pod.status.phase in ["Failed", "Unknown"]:
        return True, f"Pod phase is '{pod.status.phase}'"

    # 2. Check container status details (e.g., CrashLoopBackOff, Error, or Unhealthy probes)
    if pod.status.container_statuses:
        for container in pod.status.container_statuses:
            # Check if container is waiting due to an error state
            if container.state.waiting:
                reason = container.state.waiting.reason
                if reason in ["CrashLoopBackOff", "ImagePullBackOff", "Error", "ContainerCreating"]:
                    if reason != "ContainerCreating":  # Allow standard initialization
                        return True, f"Container '{container.name}' waiting state: {reason}"
            
            # Check container readiness / crash states
            if container.state.terminated and container.state.terminated.exit_code != 0:
                return True, f"Container '{container.name}' terminated with exit code {container.state.terminated.exit_code}"

            if not container.ready and pod.status.phase == "Running":
                # Container is running but readiness probe is failing
                return True, f"Container '{container.name}' readiness probe failing (ready=False)"

    return False, "Healthy"

def run_healer_loop():
    load_k8s_config()
    v1 = client.CoreV1Api()
    
    logging.info(f"Starting local_healer.py targeting namespace: '{TARGET_NAMESPACE}'")
    logging.info(f"Safety Guardrail: Max {MAX_RESTART_LIMIT} restarts per pod.")

    while True:
        try:
            # Step 1: Query the Kubernetes API for pods in the target namespace
            pod_list = v1.list_namespaced_pod(namespace=TARGET_NAMESPACE)
            
            for pod in pod_list.items:
                pod_name = pod.metadata.name
                unhealthy, reason = is_pod_unhealthy(pod)

                if unhealthy:
                    current_restarts = restart_tracker.get(pod_name, 0)

                    # Step 2: Enforce Guardrail (Cap maximum restarts)
                    if current_restarts >= MAX_RESTART_LIMIT:
                        log_audit_trail(
                            trigger=f"Unhealthy Pod Detected ({pod_name})",
                            evidence=f"{reason} | Current Restarts: {current_restarts}",
                            decision="Guardrail Triggered: Max restart limit reached. Escalation required.",
                            action="NO_ACTION (Halted auto-recovery)",
                            result="BLOCKED_BY_GUARDRAIL"
                        )
                        continue

                    # Step 3: Execute Remediation Action (Pod Deletion)
                    logging.warning(f"Unhealthy pod '{pod_name}' detected. Triggering self-healing...")
                    
                    try:
                        v1.delete_namespaced_pod(name=pod_name, namespace=TARGET_NAMESPACE)
                        restart_tracker[pod_name] = current_restarts + 1
                        
                        log_audit_trail(
                            trigger=f"Pod Degradation / Failure",
                            evidence=f"Pod: {pod_name} | Reason: {reason}",
                            decision=f"Issue programmatic pod deletion (Attempt {restart_tracker[pod_name]}/{MAX_RESTART_LIMIT})",
                            action=f"v1.delete_namespaced_pod('{pod_name}', '{TARGET_NAMESPACE}')",
                            result="SUCCESS (Pod deletion requested, k8s recreation pending)"
                        )
                    except ApiException as api_err:
                        logging.error(f"Failed to delete pod {pod_name}: {api_err}")

        except ApiException as e:
            logging.error(f"Kubernetes API Exception: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in healer loop: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_healer_loop()
