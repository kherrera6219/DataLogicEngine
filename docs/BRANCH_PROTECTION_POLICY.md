# Branch Protection and Review Policy

## Purpose

Define minimum branch governance requirements for protected branches (`main`, `dev`, `develop`).

## Required Settings

1. Require pull request before merge.
2. Require at least 1 approving review from code owners.
3. Dismiss stale approvals when new commits are pushed.
4. Require all configured status checks to pass before merge.
5. Require conversation resolution before merge.
6. Restrict direct pushes to repository administrators/bots only.

## Required Status Checks

1. `lint`
2. `backend-test`
3. `frontend-build`
4. `governance`
5. `windows-packaging-smoke`
6. `security` workflow checks for protected release paths

## Code Owner Governance

1. `CODEOWNERS` is the source of review ownership.
2. PRs touching security/auth, release, or governance files must include code-owner approval.

## Document Control

1. Owner: Platform Engineering
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days
