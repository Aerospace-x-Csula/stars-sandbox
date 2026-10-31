# Crash Deployment

This deployment is used to test how Kubernetes handles a container that crashes every time it starts.

The deployment file is located here:

[`automation/crash-deployment.yaml`](./automation/crash-deployment.yaml)

## Apply the Deployment

Make sure Minikube is running:

```bash
minikube start
```

Then, from the root directory of the project, apply the deployment:

```bash
kubectl apply -f automation/crash-deployment.yaml
```

You can check the pod with:

```bash
kubectl get pods
```

After the container fails a few times, you should see the pod enter `CrashLoopBackOff`.

To watch the restart behavior live:

```bash
kubectl get pods -w
```

## Why It Crashes

The container is intentionally configured to run:

```bash
exit 1
```

An exit code of `1` tells Kubernetes that the container failed. Because containers created by a Deployment are restarted automatically, Kubernetes keeps trying to start it again.

The result is:

```text
Start -> Crash -> Restart -> Crash -> Restart -> CrashLoopBackOff
```

This is different from Eric's Update Log Generator because Eric's version does not crash or restart the pod. It only creates warning logs, error logs, or error-spike logs manually so they can be viewed in OpenObserve. The pod continues running normally and is unaffected by those generated logs.

The crash deployment is different because the container actually exits with an error. Kubernetes then restarts the container, and repeated failures eventually cause the pod to enter CrashLoopBackOff

## Remove the Deployment

When you are finished testing:

```bash
kubectl delete deployment crash-on-start
```
