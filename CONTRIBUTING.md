# Contributing to stars-sandbox

Read this before you push. If something here is unclear or wrong, open a PR to fix this file. Don't work around it.

## Repo layout

| Folder | Owner | What goes here |
|---|---|---|
| `infrastructure/` | Infrastructure | Cluster setup: Minikube start, namespace |
| `apps/` | Data/Test Engineering | Sample apps and failure scenarios |
| `observability/` | Observability | OpenObserve, collector, dashboards |
| `automation/` | Automation & Self-Healing | Failure injection and recovery steps |
| `ai/` | AI/ML | Anomaly detection, AI settings, and test results |
| `documentation/` | Documentation & Release | Architecture, onboarding, runbooks, release, and handoff documentation |

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

Each team has one branch. Your team commits there, not to `main`.

| Team | Branch |
|---|---|
| Infrastructure | `infrastructure` |
| Data/Test Engineering | `apps` |
| Observability | `observability` |
| AI/ML | `ai` |
| Automation & Self-Healing | `automation` |
| Documentation & Release | `docs` |

- Run `git pull` before you start working and before you push
- Never force-push a team branch
- After each release, update your team branch from `main` before starting new work:

```
git checkout <team-branch>
git pull
git pull origin main
git push
```

## Commits and PRs

- Commits use [Conventional Commits](https://www.conventionalcommits.org/) and link the issue: `feat: add collector values (Refs #12)`
- Never push to `main`. Open a PR
- One PR per team every two weeks, from your team branch to `main`. It can cover several components
- A team member opens the PR, not the sub-lead. GitHub won't let you approve your own PR
- The PR must be ready by Sunday, before the Monday leads meeting
- Your team helps review. Your sub-lead approves, then Jonas or Moises gives final approval and merges
- Before opening the PR, confirm that:
  - [ ] Names follow this file
  - [ ] Every component you changed has its README updated
  - [ ] Your component's diagram is added or updated
  - [ ] It works on a fresh cluster (`minikube delete`, then follow your README)

## Releases

Every two weeks, at the Monday leads meeting:

1. Leads go over blockers and each team's PR
2. Approved PRs merge into `main`
3. `main` is tagged as the release: `v0.1.0`, `v0.2.0`, and so on
4. Until Friday, only fixes go into `main`. That Friday we show the release to Aerospace

Documentation & Release writes the release notes, using `docs/release/release-checklist.md`.
