# Infrastructure
Cluster setup: Minikube config, namespaces, and anything needed to rebuild the environment.

Managed by the Infrastructure team: Saw Dee (sub-lead) Cristian Hernandez Juan, Angel Hurtado

## Purpose of the Infrastructure folder
This Infrastructure/ directory is intended to document and support the setup of the local STARS AI-Powered Observability Platform sandbox. It includes: Minikube cluster configuration, Kubernetes namespaces, and the resources/instructions needed to recreate the local development environment. 

## Current Contents
Currently, this directory only contains this README.md file. There are no infrastructure scripts, Kubernetes manifests, Helm charts, or other configuration files in this directory at the time of writing. 

## Required prerequisite tools
The current [Onboarding Local Setup](../docs/onboarding/local-setup.md) guide lists the following required tools:
 - Git
 - Docker or Docker Desktop
 - Minikube
 - Kubectl
 - Helm
   
  To check that the command-line tools are installed run:

    git --version

    docker --version
    
    minikube version
    
    kubectl version --client
    
    helm version

  These commands verify tool availability and versions, not the health of the Kubernetes enviornment.

## Setup and usage
Follow the [Onboarding Local Setup](../docs/onboarding/local-setup.md) guide for the documented workstation requirements and base Minikube setup. The directory currently does not contain scripts or configuration files that can be applied directly to create the environnmet.

## Verification
After following the [Onboarding Local Setup](../docs/onboarding/local-setup.md) instructions, the following commands can help inspect the local Kuberbetes environment:

    minikube status

    kubectl cluster-info

    kubectl get nodes

    kubectl get namespace stars
  
  These commands provide basic checks of cluster status, Kubernetes connectivity, node availability, and the expected namespace.
The Infrastructure Sub-Lead should confirm the expected healthy state and whether additional checks are required for the current environment. A running cluster does not necessarily mean that all STARTS Sandbox applications and services are functioning correctly. 

## Stopping and Removing the Environment 
To stop the local cluster while generally preserving its configuration and resources:

     minikube stop
   
To delete the selected Minikube cluster and its cluster-managed resources:

    minikube delete
  
  # Warning: Deleting a cluster may permanently remove data stored only inside that cluster.
Before using the delete command, confirm that any required local data has been preserved and that the procedure is appropriate for the current STARS Sandbox environment.
The Infrastructure Sub-Lead must confirm whether additional cleanup steps are required. 

## Naming and Namespace Concentions
Follow the conventions defined in [Contributing Guidelines](../CONTRIBUTING.md)

  - The Kubernetes namespace is stars
  - Resource names, application labels, and Helm release names must match their component folder names.
  - Use lowercase names with hyphens.
  - Use .yaml, not .yml, for YAML files.
  - Run documented commands from the repository root and use relative paths when referencing repository files.
  - Never commit credentials, tokens, or other secrets.

## Current limitations

## Planned functionality 
