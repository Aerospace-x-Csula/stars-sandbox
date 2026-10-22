# Applications

Managed by the Data/Test Engineering Team: **Eric Castellon (sub-lead)**, Jasmine Pineda, Jayden Darling & Mario Nunez

## Purpose of the apps folder

This folder contains sample applications that run in the Minikube cluster and generate logs/metrics used by the `stars` sandbox.

## Current Applications and Generators

- `log-generator`
- `error-generator`

## Components Overview

### log-generator:

- Kubernetes application that writes log lines to stdout (terminal) in the `stars` namespace. Is used for manual **WARN/ERROR/Connectivity/Crash** testing.

### error-generator:

- Kubernetes application that automatically creates spikes of **22 ERROR logs** then waits for 20 seconds then repeats, simulating through 5 different simulated error types. These spikes can be viewed in the **Stars Error Monitoring Dashboard** inside of OpenObserve.

## Running and Deployment

### log-generator:

**Deploying log-generator:**

Before starting make sure to have Minikube and OpenObserve running then run:

```
minikube status
kubectl get namespace stars
```

to verify that Minikube is running and the `stars` namespace exists

From the root of the repository run:

```
kubectl apply -f apps/log-generator/deployment.yaml
kubectl -n stars rollout status deployment/log-generator --timeout=120s
```

Then wait for the rollout to succeed.

### error-generator:

Make sure that Minikube, OpenObserve and the collector are runnning.
If you forgot the setup for the collector or `log-generator` follow:

- **collector:** [collector.md](../observability/collector.md)
- **log-generator:** [README.md](log-generator/README.md)

Start/Update both generators:

```
kubectl apply -f apps/log-generator/deployment.yaml
kubectl apply -f apps/error-generator/deployment.yaml
```

Check the pods

```
kubectl get pods -n stars
```

Watch the automatic error spikes in the terminal:

```
kubectl logs -n stars -l app=error-generator -f
```

## Component Verification

### log-generator:

To verify, list the pod and run:

```
kubectl get pods -n stars
```

The pod should have a name that starts with `log-generator` and should show Running under status and 1/1 under READY

### error-generator:

In a browser open:

```
http://localhost:5050
```

In the Open Observe homepage go to

```
Logs > default
```

To show logs from both `log-generator` & `error-generator` run the query:

```
(k8s_container_name = 'log-generator' OR k8s_container_name = 'error-generator')
```

To show **Error** logs from both run the query:

```
(k8s_container_name = 'log-generator' OR k8s_container_name = 'error-generator')
AND body LIKE '%level=ERROR%'
```

## Component Telemetry

### log-generator:

- Writes continous log lines to stdout in the `stars` namespace
- INFO heartbeat logs with an increasing count every 5 seconds
- One **WARN** line, One **ERROR** line, one **Error spike** that writes 20 error lines numbered from 1-20
- Connectivity Failure: One Error with `run_id=network=01`, `target=127.0.0.1:1`, and a nonzero `wget_exit`.
- Crash ERROR with `exiting with code 42` and no completion marker. Kubernetes restarts the container and the RESTARTS count increases by one.

### error-generator:

- A spike of 20 **ERROR** logs, pausing for 20 seconds then repeat again.
- Each spike rotates through 5 simulated error types:
  - `authentication, database, connectivity, dependency & service`. Each 20-error spike contains about 4 of each type.
- `error-generator` only creates **ERROR** logs, so **WARN** logs will come from `log-generator`

## Existing Failure Scenarios

### log-generator:

- WARN: One WARN line
- ERROR: one ERROR line
- ERROR-SPIKE: 20 Error lines, numbered from 1-20
- Connectivity: one ERROR with `run_id=network01`, `target=127.0.0.1:1`, and a nonzero `wget_exit`
- Crash: exits with `code 42`, container restart

### error-generator:

5 simulated error types:

```
Authentication
database
connectivity
dependency
service
```

## Stopping or Removing Components

### log-generator:

In the terminal typing **CTRL C** stops following the logs without stopping the application.

To delete the `log-generator` application, run:

```
kubectl delete -f apps/log-generator/deployment.yaml
```

### error-generator:

To stop automatic spikes:

```
kubectl scale deployment error-generator -n stars --replicas=0
```

To remove `error-generator` run:

```
kubectl delete -f apps/error-generator/deployment.yaml
```

## Detailed Component installation:

- `error-generator`: [README.md](error-generator/README.md)
- `log-generator`: [README.md](log-generator/README.md)

## Current Limitations/Work in progress

### Current Limitations:

### Work in Progress:

- Application Traffic Generator
- Failure Scenario Documentation
- Automated Telemetry Validation
- Synthetic Metrics Generator

## Planned Functionality

