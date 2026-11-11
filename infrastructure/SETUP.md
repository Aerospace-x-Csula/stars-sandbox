# Infrastructure

## Windows setup

Windows setup uses Docker Desktop with WSL 2. Minikube runs through the Docker driver with **2 CPUs and 4 GB RAM**. Ubuntu is not required.

Use a supported **x64 Windows PC**, with virtualization enabled in BIOS/UEFI and enough RAM for Docker (preferably 16 GB or more). WinGet must be available through Microsoft's App Installer.

1. Clone or download the stars repo.
2. Open **PowerShell as Administrator**. From the repo root, run:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\infrastructure\setup-windows.ps1
   ```

   The script finds the repository from its own location; your terminal can be elsewhere if you use the script's full path.

3. If asked to restart Windows, restart and run the same command again. Complete GitHub's browser sign-in when prompted.
4. The script selects Docker's WSL 2 backend and starts Docker Desktop automatically. Complete any first-run welcome screen if shown; the script waits for the engine to be ready.
5. Enter your OpenObserve root email and password. Include **at least one uppercase letter, one number, and one punctuation character**; avoid double quotes and backslashes because the chart does not escape them. The script saves them in the ignored `observability/values.local.yaml` and reuses that file on later runs. Do not commit it.

The script installs or updates WSL without a Linux distribution, installs missing Git, Docker Desktop, Minikube, kubectl, and Helm through WinGet, starts Minikube, and installs OpenObserve in the `stars` namespace. It waits for Kubernetes and OpenObserve readiness before reporting success.

## macOS setup

Use a Mac supported by [Homebrew](https://docs.brew.sh/Installation) and [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), with internet access and your Mac administrator password available.

1. Open **Terminal**. From the repo root, run:

   ```zsh
   zsh ./infrastructure/macsetup.sh
   ```

2. Follow Homebrew's prompts for your Mac password, Return, and any Xcode Command Line Tools installation. Complete Docker Desktop's first-run terms or permission prompts if shown. If Docker times out, open Docker Desktop and rerun the script.
3. Enter your OpenObserve email and password when prompted. The password prompt asks for **at least 8 characters, one uppercase letter, one number, and one punctuation character**.
4. The script starts port forwarding automatically. Leave Terminal open and visit <http://localhost:5080> to sign in.

The script installs Homebrew and missing Git, Docker Desktop, Minikube, kubectl, and Helm. It starts Docker, clones or reuses `stars-sandbox` in your home folder, runs `minikube start` with its configured defaults, creates the `stars` namespace, and installs OpenObserve. It writes credentials to the ignored `observability/values.local.yaml` in that home-folder clone. Do not commit it.

The Mac script does not configure GitHub sign-in. If repository access requires authentication, set it up beforehand. Use this script for the first installation; use the commands below for later sessions.

## Open OpenObserve

On Windows, run this after setup. On Mac, setup runs it automatically:

```
kubectl --context=minikube --namespace=stars port-forward svc/openobserve-openobserve-standalone 5080:5080
```

Leave that terminal open, visit <http://localhost:5080>, and sign in with your OpenObserve credentials.

Press **Ctrl+C** to stop port forwarding, then run `minikube stop` to stop the cluster.

Next time, open Docker Desktop and start Minikube:

- **Windows:** `minikube start --driver=docker --cpus=2 --memory=4096`
- **Mac:** `minikube start`

Then run the port-forward command above and open <http://localhost:5080>.

On Windows, if a weak password causes `CrashLoopBackOff` during the first installation, edit `observability/values.local.yaml` and rerun the setup script.
