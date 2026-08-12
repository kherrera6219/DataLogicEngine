# DataLogicEngine accessibility conformance report

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ASR-006 |
| Title | Accessibility conformance report |
| Document version | v1.1.1 |
| Product version | 4.4.0 |
| Status | not_evaluated |
| Audience | Users, accessibility specialists, product/quality engineering, procurement, and release authority |
| Owner | Accessibility Review |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | UI implementation, automated accessibility/keyboard evidence, manual checklist, and retained packaged validation plan |
| Confidentiality | Public |
| Last reviewed | 2026-08-11 |
| Next-review trigger | UI route/control/content/theme, framework, accessibility test, assistive technology, finding, or release change |
| Requirements and evidence | Product requirement DLE-QR-001, app-readiness reports, Phase 12/13 evidence, manual NVDA record, and independent review |

## Report status

This is not a VPAT, ACR certification, WCAG conformance claim, or procurement
attestation. Product 4.4.0 remains `not_evaluated` for final accessibility
conformance because the exact signed installed candidate has not completed
packaged visual/scaling/high-contrast checks, manual keyboard and NVDA testing,
unfamiliar-user documentation walkthrough, or independent accessibility review.
The rebuilt Electron application launches and the automated source/browser
accessibility baseline remains green; this does not replace packaged scaling,
high-contrast, manual keyboard/NVDA, or independent acceptance.
The August 11 local artifact has not completed installed visual, scaling,
high-contrast, keyboard, or NVDA acceptance.

## Product and evaluation scope

The scope is the Windows 11 x64 Electron desktop application, including public/
disclosure routes, Dashboard, Chat, Session Library, Runs/Trace Explorer,
Graph/Knowledge, Simulations, Truth Engine, MCP, Settings/Privacy, Diagnostics,
and single-owner Admin surfaces. It includes normal, empty, loading, unavailable,
blocked, failed, validation, confirmation, progress, success, and recovery states.

The backend/API and generated/exported documents are assessed where their output
is presented to a user or accessibility professional. Unsupported public web,
mobile, macOS, and Linux surfaces are outside the 4.4.0 product scope.

## Current automated evidence

| Evidence | Current result | Limit |
|---|---|---|
| Axe route sweep | Phase 13 records 28 production routes with zero detected axe violations | Automated rules do not prove conformance or assistive-technology usability |
| Browser readiness/keyboard workflows | 10/10 workflows passed | Covers named paths, not every control/state or native Electron behavior |
| Production control inventory | Source inventory reports zero enabled controls without an obvious action | Does not prove accessible name, focus order, effect, or durable outcome |
| Type/lint/unit/build | Passing at recorded checkpoints | Does not replace visual/manual/AT review |

The evidence is source/browser checkpoint evidence. It must be regenerated and
bound to the final signed installer, Windows build, display settings, browser/
Electron runtime, and test tooling before release.

## Evaluation criteria

Final review shall cover at least:

- keyboard-only operation, logical focus order, visible focus, no traps, skip/
  landmark/navigation behavior, dialogs, menus, tabs, grids, trees, and complex
  graph/trace controls;
- accessible names, roles, states, descriptions, relationships, headings,
  labels/instructions, required/invalid/error/status announcements, and dynamic
  updates;
- color contrast, non-color meaning, icons, charts/graphs, evidence/confidence/
  status semantics, light/dark/high-contrast themes, and Windows forced colors;
- 100%, 125%, 150%, 200%, and supported high-DPI/multi-monitor behavior without
  lost content, overlap, clipping, or two-dimensional scrolling where avoidable;
- text resizing, zoom, responsive desktop window bounds, reflow, spacing, and
  long/error/localized-like content;
- NVDA reading order, forms, tables, live regions, dialogs, route changes,
  progress, validation, error recovery, trace/evidence review, and data controls;
- motion/animation, timing, cancellation, repeated entry, authentication,
  clipboard/download/export, and privacy/security interactions;
- installer, first-run/readiness blocker, provider configuration, backup/restore,
  update/rollback, support bundle, and uninstall data-choice accessibility;
- canonical user, installation, operations, troubleshooting, privacy, and AI
  documentation structure and readability.

## Manual NVDA protocol

Run on the exact signed candidate with a recorded Windows and NVDA version.
Start NVDA before launch, navigate every primary route without a mouse, operate
representative create/read/update/delete/recovery workflows, inspect dialogs and
async announcements, and compare spoken role/name/state/value/error/progress with
the visible and actual backend outcome. Repeat critical paths at high contrast
and 200% scaling.

Record tester, assistive technology, input devices, display/scaling, app/installer
hash, route/state, steps, expected/actual, severity, evidence, correction, retest,
and reviewer disposition. The existing NVDA checklist says it was not executed
in that environment; it is not a pass.

## Current design/control observations

The UI uses semantic routes/components, labeled controls, explicit unavailable
and error states, confirmation for destructive actions, truthful `not measured`
data, keyboard-tested navigation, and corrected contrast findings. Unsupported
or actionless controls were removed/disabled rather than presented as functional.

Remaining risk is material: automated tools can miss focus loss, inaccessible
canvas/graph semantics, noisy or absent announcements, incorrect control
relationships, scaling/forced-color defects, Electron/native-dialog behavior,
and workflow outcomes that are visually clear but not perceivable through NVDA.

## Findings and conformance disposition

Accessibility findings use severity, affected requirement/route/control/state,
reproduction environment, user impact, evidence, remediation, regression test,
and exact-artifact retest. P0/P1 and unaccepted P2 findings block release.
Exceptions require an owner, alternative access, scope, rationale, expiration,
and independent review; they do not become general conformance.

No WCAG level, Section 508, EN 301 549, Microsoft accessibility, or other formal
conformance is asserted. Final status remains `not_evaluated`, and production/
public release is **NO-GO**, until the manual packaged and independent evidence is
complete and the release authority records a truthful criterion-by-criterion
disposition.
