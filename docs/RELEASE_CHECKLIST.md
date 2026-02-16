# Release Checklist

## Purpose

Provide a release governance checklist for tagged builds and production deployment approvals.

## Pre-Release Gate

1. [ ] `CHANGELOG.md` updated with release entry.
2. [ ] `docs/DOCS_VERSION.json` version and `updated_at` updated if docs changed.
3. [ ] CI jobs pass:
   - lint
   - backend tests
   - frontend build/lint/typecheck/tests
   - governance (parity + lockfiles)
   - windows packaging smoke
4. [ ] Security scans reviewed (dependency audit, CodeQL, Bandit delta, secret scan).
5. [ ] Installer integrity/signing checks completed for release artifacts.

## Release Approval

1. [ ] At least one code-owner review approved.
2. [ ] Branch protection requirements satisfied (required checks + review count).
3. [ ] Production rollback plan confirmed.

## Post-Release

1. [ ] Deployment health checks validated.
2. [ ] Metrics/alerts reviewed for first 30 minutes after rollout.
3. [ ] Release notes published.

## Document Control

1. Owner: Release Engineering
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every release cycle
