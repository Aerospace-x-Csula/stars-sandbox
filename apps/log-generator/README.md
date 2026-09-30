# Log Generator

Simple Kubernetes application that continuously writes log lines to stdout in the `stars` namespace.

## Prerequisites
Make sure Minikube is running:

```bash
minikube status
```

Make sure the stars namespace exists:

```bash
kubectl get namespace stars
```

If the namespace does not exist, create it:

```bash
kubectl create namespace stars
```

## Deploy the Application 
From the root of the repository, run: 

```bash
kubectl apply -f apps/log-generator/deployment.yaml
```

## Verify the Pod
Run:

```bash
kubectl get pods -n stars
```

Copy the pod name shown in the output

## View the Logs
Replace <pod-name> with the actual pod name.

Then run:
```bash
kubectl logs <pod-name> -n stars
```

To continuously follow new log lines as they appear, run:
```bash
kubectl logs -f <pod-name> -n stars
```

You should see new log lines appearing every 5 seconds

Press Ctrl+C to stop following the logs.

## Delete the Application
To remove the deployment, run:
```bash
kubectl delete -f apps/log-generator/deployment.yaml
```
