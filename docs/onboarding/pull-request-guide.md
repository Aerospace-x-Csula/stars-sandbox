# Pull Request Guide

How a team's work gets from its team branch into `dev`, through the wargame, and into a release on `main`. The full rules are in [CONTRIBUTING.md](https://github.com/Aerospace-x-Csula/stars-sandbox/blob/dev/CONTRIBUTING.md).

| Who | What they do |
|---|---|
| A team member | Opens the team PR into `dev` |
| POC (release owner) | Submits the release request and runs its tests at the wargame |
| Teammates | Review and comment |
| Sub-lead (code owner) | Approves |
| Jonas or Moises | Final approval, merge, and wargame |

The PR and the release request must be ready by the Sunday before the biweekly Monday leads meeting. That meeting is the wargame.

## 1. Open the team PR (team member)

A team member opens the PR, not the sub-lead. GitHub doesn't let the person who opened a PR approve it, and the sub-lead's approval is required.

1. Make sure your team branch is up to date with `dev` (see step 6).
2. On the repo's main page, choose your team branch in the **Branch** menu.

   ![Branch menu on the repo's main page](images/branch-dropdown.png)

3. Click **Compare & pull request** in the yellow banner. If there's no banner, go to **Pull requests** and click **New pull request**.

   ![Compare & pull request banner](images/pull-request-compare-pull-request.png)

4. Check that **base** is `dev` and **compare** is your team branch. `dev` is the default, so base is usually already set. Never use `main`.
5. Fill in the PR template.
6. Click **Create pull request**.

GitHub adds your sub-lead as a reviewer automatically. If the PR changes another team's folder, that team's sub-lead is added too and must also approve.

## 2. Submit the release request (POC)

One release request per component folder your PR changes.

1. Go to **Issues**, click **New issue**, and choose **Release Request**.
2. Fill in every field. Paste your PR link so the leads can see exactly what's changing.
3. Click **Create**.

Two fields matter most at the wargame:

- **Acceptance tests:** the steps you'll rerun. Test them on your own fresh cluster first (`minikube delete`, then follow your README).
- **Rollback:** commands someone else can copy and paste to undo your release. Write them for a lead who doesn't know your code.

## 3. Review and approve (teammates and sub-lead)

1. Open the PR and click **Files changed**.

   ![Files changed tab](images/pull-request-tabs-changed-files.png)

2. To comment on a line, hover over it and click the blue **+**.

   ![Blue + next to a line number](images/hover-comment-icon.png)

3. When you're done, click **Review changes**.

   ![Review changes button](images/review-changes-button.png)

4. Write a short summary, then choose one:
   - **Comment**: feedback only. Teammates use this.
   - **Approve**: the sub-lead uses this when the PR is ready to merge.
   - **Request changes**: blocks the merge until it's fixed.
5. Click **Submit review**.

An approval only counts if you click the button. A new commit clears all approvals, so approve again after changes.

## 4. Final approval and merge into `dev` (Jonas or Moises)

This happens at the Monday leads meeting. The merge button unlocks after 2 approvals, including the sub-lead's. If one lead wrote code in the PR or approved it as sub-lead, the other one merges.

1. Read the team's release request.
2. Approve the PR (step 3) so the final approval is on record.
3. At the bottom of the PR, open the merge menu and choose **Create a merge commit**. Don't squash: team branches keep being used after each release.

   ![Merge options menu](images/merge-pull-request-options.png)

4. Click **Merge pull request**, then **Confirm merge**.
5. Don't click **Delete branch**. The team branch stays.

## 5. Wargame (leads and POCs)

1. A lead deploys `dev` on a fresh cluster.
2. Each POC runs the acceptance tests from their release request.
3. **Pass:** the leads open a PR from `dev` into `main`, merge it, and tag the release (see Versions in CONTRIBUTING.md).
4. **Fail:** the leads revert that team's merge on `dev` and tell the sub-lead. The team fixes it and brings it to the next wargame.

## 6. After each wargame: update your team branch

Run from the repo root:

```
git checkout <team-branch>
git pull
git pull origin dev
git push
```

## Credits

Screenshots and some steps are from GitHub Docs, © GitHub, Inc., licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The steps were shortened and adapted to our process. The screenshots are unchanged.

- [Creating a pull request](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request)
- [Reviewing proposed changes in a pull request](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request)
- [Merging a pull request](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request)
