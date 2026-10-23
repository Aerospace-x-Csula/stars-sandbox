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

| Branch | What it is |
|---|---|
| Team branch | Where your team works day to day |
| `dev` | Team PRs merge here and get tested together at the wargame. This is the default branch |
| `main` | Production. Only changes when a wargame passes, by a PR from `dev` |

Each team has one branch. Your team commits there, never to `dev` or `main`.

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
- After each wargame, update your team branch from `dev` before starting new work:

```
git checkout <team-branch>
git pull
git pull origin dev
git push
```

## Commits and PRs

- Commits use [Conventional Commits](https://www.conventionalcommits.org/) and link the issue: `feat: add collector values (Refs #12)`
- Never push to `dev` or `main`. Open a PR
- One PR per team every two weeks, from your team branch to `dev`. It can cover several components
- A team member opens the PR, not the sub-lead. GitHub won't let you approve your own PR
- The PR and your release request must be ready by Sunday, before the Monday leads meeting
- Your team helps review. Your sub-lead approves, then Jonas or Moises gives final approval and merges. `dev` needs 2 approvals, including the code owner
- Before opening the PR, confirm that:
  - [ ] Names follow this file
  - [ ] Every component you changed has its README updated
  - [ ] Your component's diagram is added or updated
  - [ ] It works on a fresh cluster (`minikube delete`, then follow your README)

## Releases

We follow the STARS release process: changes are tested together on `dev` at a wargame before they reach `main`.

### Release request

Every team PR comes with a release request: **Issues → New issue → Release Request**. One per component folder that changed. It covers:

- POC: who owns the release and runs its tests at the wargame
- Version, PR link, and issues
- Risk (Low / Medium / High) and the worst case if it goes wrong
- Breaking changes and anything it depends on
- Acceptance tests: proof it worked on your own fresh cluster, and the steps to rerun it
- Rollback: copy-and-paste commands to go back to the last version

### Wargame

Every two weeks, at the Monday leads meeting:

1. Leads go over blockers, each team's PR, and its release request
2. Approved PRs merge into `dev`
3. A lead deploys `dev` on a fresh cluster. Each POC runs their acceptance tests
4. **Pass:** `dev` merges into `main` and is tagged. **Fail:** that team's merge is reverted on `dev`, and the team brings the fix to the next wargame
5. That Friday we show the release to Aerospace

Documentation & Release writes the release notes, using `docs/release/release-checklist.md`.

### Versions

Versions are `MAJOR.MINOR.PATCH`. We stay at `0.x` until the handoff release, `1.0.0`.

| Change | Bump | Example |
|---|---|---|
| Bug fix | Patch | `0.1.0` → `0.1.1` |
| New feature or breaking change | Minor | `0.1.0` → `0.2.0` |

Two kinds of tags, both made by the leads after a wargame passes:

- **Component:** `<folder>/v<version>`, for example `observability/v0.2.0`. One for each component that released
- **Platform:** `v<version>` on `main`, for example `v0.2.0`. One per wargame

### Rollback

To put one component back to its last version, run from the repo root, then reinstall it with its README:

```
git checkout observability/v0.1.0 -- observability/
```

To put everything back, deploy the last platform tag, for example `v0.1.0`.
