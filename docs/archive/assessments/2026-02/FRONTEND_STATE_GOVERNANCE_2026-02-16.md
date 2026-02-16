# Frontend State Governance (2026-02-16)

## Purpose
- Establish explicit ownership and mutation boundaries for frontend state.
- Enforce predictable data flow through lint rules and approved persistence adapters.

## State Domains
- `auth`: owned by `frontend/contexts/AuthContext.tsx`
- `theme`: owned by `frontend/contexts/ThemeContext.tsx`
- `feature_flags`: owned by `frontend/contexts/FeatureFlagContext.tsx`

## Persistence Policy
- Approved browser-persistence adapter:
  - `frontend/lib/state/storage.ts`
- Direct usage of:
  - `localStorage`
  - `sessionStorage`
  - `window.localStorage`
  - `window.sessionStorage`
  is disallowed by lint in application code (tests excluded).

## Layering Policy
- `frontend/lib/**` must not import from:
  - `frontend/app/**`
  - `frontend/components/**`
  - `frontend/contexts/**`
- `frontend/contexts/**` must not import from:
  - `frontend/app/**`

## Enforcement
- Lint enforcement is codified in:
  - `frontend/eslint.config.mjs`
- Machine-readable policy contract:
  - `frontend/state-governance.config.json`
