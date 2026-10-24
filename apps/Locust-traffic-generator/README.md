# Load Testing on Minikube with Locust

Generate HTTP traffic against an application running in the `stars` namespace of a local minikube cluster. Locust runs **inside** the cluster, so it reaches the app through cluster DNS with no ingress needed.

It simulates three traffic patterns:

- **Normal traffic:** steady, human-paced requests
- **High traffic:** many users sending near-continuous requests
- **Failed requests:** bad routes, server errors, and timeouts

> **Placeholders:** the examples use `stars-app` as the service name and `/`, `/get` as endpoints. Replace these with your application's real values.

## Contents

1. [Prepare the cluster](#1-prepare-the-cluster)
2. [Write the locustfile](#2-write-the-locustfile)
3. [Deploy Locust into the namespace](#3-deploy-locust-into-the-namespace)
4. [Run each scenario](#4-run-each-scenario)
5. [Simulate failures in the app itself](#5-simulate-failures-in-the-app-itself)
6. [Tips](#tips)

## Prerequisites

- [minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

## 1. Prepare the cluster

```bash
minikube start
kubectl create namespace stars #if you haven't already
```

If you don't have an app yet, deploy httpbin as a stand-in. It has endpoints that return errors on demand, which makes it useful for failure testing:

```bash
kubectl -n stars create deployment stars-app --image=kennethreitz/httpbin --port=80
kubectl -n stars expose deployment stars-app --port=80
```

## 2. Download the locustfile

Download the `locustfile.py`. It defines one user class per traffic pattern.


## 3. Deploy Locust into the namespace

Create a ConfigMap from the locustfile:

```bash
kubectl -n stars create configmap locustfile --from-file=locustfile.py #Navigate to where you have your file installed beforehand using cd(if using ubuntu)
```

Download `locust.yaml`, apply it, and open the web UI:

```bash
kubectl apply -f locust.yaml
kubectl -n stars rollout status deployment/locust
kubectl -n stars port-forward svc/locust 8089:8089
```

Open <http://localhost:8089>.

## 4. Run each scenario

In the Locust web UI, use the **User classes** selector to choose which classes run, then set the user count and spawn rate.

| Scenario        | User class        | Users   | Spawn rate |
|-----------------|-------------------|---------|------------|
| Normal          | `NormalUser`      | 10-20   | 2/s        |
| High traffic    | `HighTrafficUser` | 200-500 | 20/s       |
| Failed requests | `FailingUser`     | 10-30   | 5/s        |
| Realistic mix   | all three         | 50      | 5/s        |

If you don't see the user class selector, your Locust version may be older than 2.x. Use a newer image.

## 5. Simulate failures in the app itself

`FailingUser` only generates bad *requests*. To see how the app behaves when the infrastructure fails, run `NormalUser` and break things mid-test:

```bash
# Total outage: connection errors
kubectl -n stars scale deployment/stars-app --replicas=0

# Recovery
kubectl -n stars scale deployment/stars-app --replicas=3

# Pod loss
kubectl -n stars delete pod -l app=stars-app
```

## Tips

- **Headless runs:** replace the container args with `--headless -u 100 -r 10 -t 5m NormalUser` to run without the UI, which is useful for CI or a Kubernetes Job.
- **Scaling the generator:** a single Locust process tops out around a few thousand requests per second, and minikube's own resources will likely limit you first. Start with more headroom using `minikube start --cpus=4 --memory=8g`. For larger loads, Locust supports a master plus worker pods.
- **Editing the locustfile:** after changing it, recreate the ConfigMap and restart Locust:
  ```bash
  kubectl -n stars delete configmap locustfile
  kubectl -n stars create configmap locustfile --from-file=locustfile.py
  kubectl -n stars rollout restart deployment/locust
  ```