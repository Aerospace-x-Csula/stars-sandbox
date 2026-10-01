# Contributing to stars-sandbox

Read this before you push. If something here is unclear or wrong, open a PR to fix this file. Don't work around it.

## Repo layout

| Folder | Owner | What goes here |
|---|---|---|
| `infrastructure/` | Infrastructure | Cluster setup: Minikube start, namespace |
| `apps/` | Data/Test Engineering | Sample apps and failure scenarios |
| `observability/` | Observability | OpenObserve, collector, dashboards |
| `automation/` | Automation & Self-Healing | Failure injection and recovery steps |
| `docs/` | Documentation & Release | Architecture, onboarding, runbooks, release, and handoff documentation |

New top-level folder = a PR that adds a row here.

## Folders and files

- One subfolder per component: `apps/log-generator/`, `observability/openobserve/`, `observability/collector/`
- Every component folder has a `README.md` covering how to install it, how to check it works, and how to remove it
- Names are lowercase with dashes: `log-generator`, not `LogGenerator` or `log_generator`
- Use `.yaml`, not `.yml`
- All commands in READMEs run from the **repo root** with relative paths, for example `-f observability/openobserve/values.local.yaml`. Never use `~/stars-sandbox/...`

### Documentation

- Keep the root `README.md` concise and use it as the repository entry point.
- Put cross-system architecture, onboarding, operations, runbooks, and release documentation under `docs/`.
- Keep component-specific technical documentation close to the component it describes.
- Avoid copying the same procedure into multiple documents; link to the authoritative guide instead.
- Documentation containing commands must be tested before it is marked verified.
- Technical workstream owners review technical facts related to their components.

## Secrets

- Commit `values.example.yaml` with placeholder values
- Put your real values in `values.local.yaml` in the same folder. Git already ignores every `*.local.yaml`
- Never paste passwords or tokens in issues, PRs, or Slack

## Kubernetes names

- Namespace: always `stars`
- Resource name, `app:` label, and Helm release name all match the folder name
  - `apps/log-generator/` → Deployment `log-generator`, label `app: log-generator`

## Branches

```
<type>/<team>-<short-name>
```

- **type:** `feat`, `fix`, `docs`, `chore`
- **team:** the folder name (`infrastructure`, `apps`, `observability`, `automation`, `docs`)
- Examples: `feat/apps-log-generator`, `feat/observability-collector`, `docs/infrastructure-minikube-start`

## Commits and PRs

- Commits use [Conventional Commits](https://www.conventionalcommits.org/) and link the issue: `feat: add collector values (Refs #12)`
- Never push to `main`. Open a PR
- One component per PR
- Your folder's sub-lead reviews and approves
- Before opening the PR, confirm that:
  - [ ] Names follow this file
  - [ ] The README is updated in the same PR
  - [ ] It works on a fresh cluster (`minikube delete`, then follow your README)
