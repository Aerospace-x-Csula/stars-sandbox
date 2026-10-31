#!/bin/zsh

# This script is for macOS systems only.
# It installs Homebrew, Git, Docker Desktop, kubectl, Minikube and Helm, skipping anything already installed, then clones the stars-sandbox repo into your home directory. After that it starts Minikube, creates the "stars" namespace, adds the OpenObserve Helm repo, asks you for an email and password to put in to values.local.yaml, installs OpenObserve, and port-forwards it so you can open it at localhost:5080 in your browser.

set -e
divider() {
	echo "-------------------------------------------------------------------------------------------------------"
}
longDivider(){
	echo " ====================================================================="
}


# Section 1: Install the tools, skipping any that are already installed
# Installing homebrew 
divider
if command -v brew >/dev/null 2>&1; then
	echo "Homebrew is already installed"
else
	echo "Installing homebrew..."
	echo "The installer will ask for your Mac password and a RETURN keypress."
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# The Homebrew installer does not add brew to the PATH of this running shell, so a fresh install still leaves "brew" as a command not found until we load it.
if ! command -v brew >/dev/null 2>&1; then
	if [ -x /opt/homebrew/bin/brew ]; then
		# For Apple Silicon
		eval "$(/opt/homebrew/bin/brew shellenv)"
	elif [ -x /usr/local/bin/brew ]; then
		# For Intel Macs
		eval "$(/usr/local/bin/brew shellenv)"
	else
		echo "Homebrew still is not available after installing."
		echo "Close this terminal, open a new one, and re-run this script."
		exit 1
	fi
fi

# Adds brew to ~/.zprofile so future terminals can find it, unless the line is already there.
if ! grep -q "brew shellenv" ~/.zprofile 2>/dev/null; then
	echo 'eval "$(brew shellenv)"' >> ~/.zprofile
	echo "Added Homebrew to ~/.zprofile so new terminals can find brew"
fi

# Installation for Git, Kubectl, Minikube, Helm & Docker
divider
if command -v git >/dev/null 2>&1; then
	echo "git is already installed."
else
	echo "git is missing. Installing git via Homebrew..."
	brew install git
fi

if command -v kubectl >/dev/null 2>&1; then
	echo "kubectl is already installed"
else
	echo "kubectl is missing. Installing kubectl via homebrew..."
	brew install kubectl
fi

if command -v minikube >/dev/null 2>&1; then
	echo "minikube is already installed"
else
	echo "Installing Minikube via homebrew..."
	brew install minikube
fi

if command -v helm >/dev/null 2>&1; then
	echo "helm is already installed."
else
	echo "Installing helm via Homebrew..."
	brew install helm
fi

if command -v docker >/dev/null 2>&1; then
	echo "docker is already installed"
else
	echo "Installing Docker Desktop via homebrew..."
	brew install --cask docker-desktop
fi

divider
rehash


# Docker Desktop has to actually be running before "minikube start" works so waits until docker desktop is running
echo "Making sure Docker Desktop is running..."
docker info >/dev/null 2>&1 || open -a "Docker" 2>/dev/null || open -a "Docker Desktop" 2>/dev/null || true

# Checks every 3 seconds, up to 60 times, so it gives up after 3 minutes.
for i in {1..60}; do
	if docker info >/dev/null 2>&1; then
		break
	fi
	echo "Waiting for the Docker engine to start..."
	sleep 3
done

if ! docker info >/dev/null 2>&1; then
	echo "Docker did not start within 3 minutes. Open Docker Desktop manually, then re-run this script."
	exit 1
fi
echo "Docker is running"


# Verification that the programs are installed
longDivider
echo "Verification that the programs are installed:"
	git --version
	docker --version
	minikube version
	kubectl version --client
	helm version
longDivider


# Cloning stars-sandbox repository into the home directory. Skips cloning if star-sandbox is already in the home directory
echo "Cloning STARS Repository into home directory"
if [ -d ~/stars-sandbox/.git ]; then
	echo "stars-sandbox is already cloned. Skipping the clone."
else
	git clone https://github.com/Aerospace-x-Csula/stars-sandbox.git ~/stars-sandbox
fi
	cd ~/stars-sandbox
longDivider


# Installing OpenObserve into the local Minikube cluster

# Starting minikube
divider
echo "Starting Minikube, this can take a few minutes."
	minikube start
echo "Verifying that Kubernetes can see the Minikube node..."
	kubectl get nodes

# Creating the stars namespace.
divider
echo "Creating stars namespace"
	kubectl create namespace stars
	kubectl get namespaces

# Adding the OpenObserve Helm Repository
divider
echo "Adding the OpenObserve Helm Repository...."
	helm repo add openobserve https://charts.openobserve.ai
	helm repo update
	helm search repo openobserve


# Creating the private OpenObserve credentials
divider

# Asks for the user to input an email until it looks like an email address.
while true; do
	print -n "Enter your OpenObserve email: "
	read -r EMAIL
	if [[ "$EMAIL" == *@*.* ]]; then
		break
	fi
	echo "That does not look like an email. Try again."
done

# Asks for a password until it meets all four requirments of being more than 8 characters long, contain one uppercase letter, one number and one punctuation. A weak password makes the OpenObserve pod go into CrashLoopBackOff, so this checks before installing.
while true; do
	echo "Password needs to be at least 8 characters long, have one uppercase letter, one number and one punctuation"
	print -n "Enter a strong OpenObserve root password: "
	read -r PASSWORD

	if [[ ${#PASSWORD} -ge 8 ]]; then
		echo "Password must be greater than 8 characters. Try again."
		continue
	fi
	if [[ "$PASSWORD" != *[A-Z]* ]]; then
		echo "Password needs at least one uppercase letter. Try again."
		continue
	fi
	if [[ "$PASSWORD" != *[0-9]* ]]; then
		echo "Password needs at least one number. Try again."
		continue
	fi
	if ! [[ "$PASSWORD" =~ [[:punct:]] ]]; then
		echo "Password needs at least one punctuation character. Try again."
		continue
	fi
	break
done


SAFE_EMAIL=${EMAIL//\'/\'\'}
SAFE_PASSWORD=${PASSWORD//\'/\'\'}

# Writes the lines below into values.local.yaml and inserts the inputed email and password into the file 
cat > ~/stars-sandbox/observability/values.local.yaml <<EOF
auth:
  ZO_ROOT_USER_EMAIL: '$SAFE_EMAIL'
  ZO_ROOT_USER_PASSWORD: '$SAFE_PASSWORD'
EOF

# Checking if values.local.yaml is not listed when running git status and will add the file to the .gitignore to be ignored from being commited and pushed 
divider
if git -C ~/stars-sandbox check-ignore -q observability/values.local.yaml; then
	echo "Git is ignoring values.local.yaml"
else
	echo "WARNING: git is NOT ignoring observability/values.local.yaml."
	echo "Do not commit anything until that is fixed."
	echo "Make sure add observability/values.local.yaml to the .gitignore file"
fi


# Installing OpenObserve
divider
echo "Installing OpenObserve..."
helm --namespace stars -f ~/stars-sandbox/observability/values.local.yaml install openobserve openobserve/openobserve-standalone


# Verifying that OpenObserve is running
divider
echo "Waiting for the OpenObserve pod to be ready, this can take a few minutes..."
sleep 5
if ! kubectl wait --for=condition=ready pod --all -n stars --timeout=300s; then
	echo ""
	echo "The OpenObserve pod did not become ready."
	echo "This usually means the password was not strong enough."
	echo "Edit observability/values.local.yaml, pick a stronger password, then run:"
	echo "  helm upgrade openobserve openobserve/openobserve-standalone --namespace stars -f ~/stars-sandbox/observability/values.local.yaml"
	exit 1
fi

echo "Checking the pods, services and Helm release:"
	kubectl get pods -n stars
	kubectl get services -n stars
	helm list -n stars


# Opening the OpenObserve in Browser
longDivider
echo "OpenObserve is installed and running."
echo ""
echo "Open http://localhost:5080 in your browser and log in with the email and password you just created."
echo ""
echo "When you are finished, stop Minikube without deleting the cluster by running in a new terminal window:"
echo "  minikube stop"
echo ""
echo "Next time you work on the project run the following commands then open localhost:5080 in the browser:"
echo "  minikube start"
echo "  kubectl get pods -n stars"
echo "  kubectl --namespace stars port-forward svc/openobserve-openobserve-standalone 5080:5080"
longDivider


echo "Starting the port forward. Press Ctrl-C when you are finished."
kubectl --namespace stars port-forward svc/openobserve-openobserve-standalone 5080:5080