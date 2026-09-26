# OpenObserve Local Installation (STARS)

This guide installs **OpenObserve Standalone** into a local **Minikube Kubernetes cluster** using **Helm**.

The same Kubernetes and Helm commands can be used on Windows, macOS, and Linux as long as the prerequisites below are already installed.

## Prerequisites

Make sure you already have:

- Docker / Docker Desktop
- Minikube
- kubectl
- Helm
- A local copy of the STARS repository

Optional checks:

```bash
docker --version
minikube version
kubectl version --client
helm version
```

---

## 1. Start Minikube

Start the local Kubernetes cluster:

```bash
minikube start
```

Verify that Kubernetes can see the Minikube node:

```bash
kubectl get nodes
```

You should see the `minikube` node with a status of `Ready`.

---

## 2. Create the `stars` Namespace

Create the namespace that will contain the STARS OpenObserve resources:

```bash
kubectl create namespace stars
```

If Kubernetes says the namespace already exists, that is okay.

Verify it:

```bash
kubectl get namespaces
```

---

## 3. Add the OpenObserve Helm Repository

Add the official OpenObserve Helm repository:

```bash
helm repo add openobserve https://charts.openobserve.ai
```

Refresh Helm's local chart list:

```bash
helm repo update
```

Verify that Helm can find the OpenObserve charts:

```bash
helm search repo openobserve
```

You should see a chart named:

```text
openobserve/openobserve-standalone
```

---

## 4. Create Your Private OpenObserve Credentials

Do **not** put a real password in a file that will be committed to GitHub.

From the root of the STARS repository, create this file locally:

```text
observability/values.local.yaml
```

Put your own OpenObserve root email and password inside it:

```yaml
auth:
  ZO_ROOT_USER_EMAIL: "your-email@example.com"
  ZO_ROOT_USER_PASSWORD: "your-private-password"
```

### Choose a strong password.

At least one uppercase letter, one number, one punctuation.

If the password isn't strong enough, the pod can go into a CrashLoopBackOff.

If that is the case, change your password in your values.local.yaml and save the file.

After that, run this command to correct the CrashLoopBackOff.

```bash
helm upgrade openobserve openobserve/openobserve-standalone `
  --namespace stars `
  -f values.local.yaml
```

### Important: keep this file out of Git

Make sure the repository's `.gitignore` contains:

```gitignore
observability/values.local.yaml
```

Before committing, you can check that Git is ignoring the file with:

```bash
git status
```

`values.local.yaml` should **not** appear as a file waiting to be committed.

---

## 5. Install OpenObserve

From the root of the STARS repository, run:

```bash
helm --namespace stars -f observability/values.local.yaml install openobserve openobserve/openobserve-standalone
```

What the command means:

- `--namespace stars` installs the Kubernetes resources into the `stars` namespace.
- `-f observability/values.local.yaml` loads your private OpenObserve configuration.
- `install` creates a new Helm installation.
- `openobserve` is the Helm **release name**.
- `openobserve/openobserve-standalone` is the Helm chart being installed.

A successful install should show information similar to:

```text
NAME: openobserve
NAMESPACE: stars
STATUS: deployed
```

---

## 6. Verify That OpenObserve Is Running

Check the pods:

```bash
kubectl get pods -n stars
```

Wait until the OpenObserve pod shows:

```text
READY   STATUS
1/1     Running
```

If you encountered a CrashLoopBackOff on status, go back to the instructions when picking a Strong Password. Check your pods again until STATUS is Running and READY is 1/1.

Check the services:

```bash
kubectl get services -n stars
```

With the release name used in this guide, the OpenObserve service should be named:

```text
openobserve-openobserve-standalone
```

You can also verify the Helm release:

```bash
helm list -n stars
```

---

## 7. Open the OpenObserve Web UI

Forward local port `5080` to the OpenObserve service:

```bash
kubectl --namespace stars port-forward svc/openobserve-openobserve-standalone 5080:5080
```

Keep this terminal running while you use OpenObserve.

Open a browser and go to:

```text
http://localhost:5080
```

Log in using the email and password from your private `observability/values.local.yaml` file.

### If the service name is not found

Run:

```bash
kubectl get services -n stars
```

Use the actual non-headless OpenObserve service shown there in the `port-forward` command.

For example:

```bash
kubectl --namespace stars port-forward svc/<service-name> 5080:5080
```

Do not use the service ending in `-headless` for browser access.

---

## 8. Stopping Work for the Day

Stop Minikube without deleting the cluster:

```bash
minikube stop
```

This keeps the Kubernetes cluster and OpenObserve installation saved locally.

The next time you work on the project, start it again with:

```bash
minikube start
```

Then verify the pod is running:

```bash
kubectl get pods -n stars
```

Start the port forward again when you need the OpenObserve UI:

```bash
kubectl --namespace stars port-forward svc/openobserve-openobserve-standalone 5080:5080
```

---

## Useful Commands

Show everything in the `stars` namespace:

```bash
kubectl get all -n stars
```

Show OpenObserve pods:

```bash
kubectl get pods -n stars
```

Show OpenObserve services:

```bash
kubectl get services -n stars
```

Show Helm releases in `stars`:

```bash
helm list -n stars
```

View the OpenObserve Kubernetes Secret metadata and Base64-encoded values:

```bash
kubectl get secret openobserve-openobserve-standalone -n stars -o yaml
```

Do not paste decoded passwords into GitHub, documentation, issues, or chat messages.

---

## Uninstalling OpenObserve

Only use this if you intentionally want to remove the Helm release:

```bash
helm uninstall openobserve -n stars
```

To completely delete the local Minikube cluster:

```bash
minikube delete
```

Normally use `minikube stop`, not `minikube delete`, when you are simply finished working for the day.

---

## Installation Flow

```text
Docker
  ↓
Minikube
  ↓
Kubernetes cluster
  ↓
stars namespace
  ↓
Helm release: openobserve
  ↓
OpenObserve standalone pod/service
  ↓
kubectl port-forward
  ↓
http://localhost:5080
```
