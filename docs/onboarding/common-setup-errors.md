# Common setup errors guide

### Windows asks to restart during setup

**Symptom:** While the Windows setup script `infrastructure/setup-windows.ps1` is running, it asks you to restart Windows.

**Check:** Read the message in PowerShell to confirm it's asking you to restart Windows.

**Fix:** Restart Windows, open **PowerShell as an Administrator** and run the same command again in the repo root:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\infrastructure\setup-windows.ps1
```

**Related Documentation:**

- [README.MD](../../infrastructure/README.md)
- [SETUP-MD](../../infrastructure/SETUP.md)

### OpenObserve pod enters `CrashLoopBackOff` when running `infrastructure/setup-windows.ps1`

**Symptom:** During the first installation on Windows when running `infrastructure/setup-windows.ps1`, OpenObserve enters a `CrashLoopBackOff` because the password created in `observability/values.local.yaml` is too weak.

**Check:** Open `observability/values.local.yaml` and check the password. It must include **at least one uppercase letter, one number, and one punctuation character, and must not contain double quotes or backslashes.**

**Fix:**
Edit the password in `observability/values.local.yaml` and save the file. Then rerun the setup script in **PowerShell as an Administrator** in the repo root:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\infrastructure\setup-windows.ps1
```

**Related Documentation:**

- [README.MD](../../infrastructure/README.md)
- [SETUP-MD](../../infrastructure/SETUP.md)

### `values.local.yaml` appears in `git status`

**Symptom:**

When writing OpenObserve credentials into `values.local.yaml` and then running `git status`, `values.local.yaml` appears under `Untracked files:` waiting to be added and committed.

**Check:**

Run

```
git status
```

`values.local.yaml` appears as a file waiting to be committed.

**Fix:**

Edit `.gitignore` to include `values.local.yaml` in order to ignore this file and save.

Run:

```
git status
```

to confirm that `values.local.yaml` is not appearing as a file waiting to be committed.

**Related Documentation:**

- [README.md](../../observability/README.md)
- [install.md](../../observability/install.md)

### OpenObserve pod enters `CrashLoopBackOff`

**Symptom:** When running `kubectl get pods -n stars -w` it shows the OpenObserve pod has entered a status of `CrashLoopBackOff`.

**Check:**
Run

```
kubectl get pods -n stars
```

If the status is `CrashLoopBackOff`, look at the password in `values.local.yaml`. It needs to be changed to have at least one uppercase letter, one number and one punctuation mark.

**Fix:**

Change your password in `values.local.yaml` to a stronger one and save the file.

Then run:

```
helm upgrade openobserve openobserve/openobserve-standalone --namespace stars -f values.local.yaml
```

Check the pods:

```
kubectl get pods -n stars -w
```

Wait until the OpenObserve pod shows:

```
READY   STATUS
1/1     Running
```

**Related Documentation:**

- [README.md](../../observability/README.md)
- [install.md](../../observability/install.md)

### OpenObserve service cannot be found

**Symptom:**

Running

```
kubectl --namespace stars port-forward svc/openobserve-openobserve-standalone 5080:5080
```

results in being unable to forward local port `5080` to the OpenObserve service.

**Check:**

Run

```
kubectl get services -n stars
```

to see services that currently exist in the `stars` namespace.

**Fix:**
Use the actual non-headless OpenObserve service shown there in the `port-forward` command.

For example:

```
kubectl --namespace stars port-forward svc/<service-name> 5080:5080
```

Do not use the service ending in `-headless` for browser access.

Then open `http://localhost:5080` in your browser.

**Related Documentation:**

- [README.md](../../observability/README.md)
- [install.md](../../observability/install.md)
