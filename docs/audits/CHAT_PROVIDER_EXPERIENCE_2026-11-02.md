# Chat provider and answer presentation checkpoint

Status: source merged and engineering build installed; live-provider, full installed acceptance and release remain open.

The installed question reviewed in this work used Google `gemini-3.8-flash`.
Its only cited source was earlier conversation history containing the same
question, and its trace recorded unsupported claims. A citation label is not
proof that a source supports a claim. The recorded provider completion was
`complete`; it did not establish that the prose was comprehensive.

The candidate source change adds a primary-provider preference using the
existing AI settings, and an opt-in desktop-chat fallback setting stored on
this computer. When enabled for a desktop request, the governed provider path
permits at most two attempts within the same request-wide, session, time,
token, and spending controls. It tries the other configured provider only
after a network failure, provider outage, timeout, or rate limit. It does not
retry a policy block or grant an external client a new routing privilege.
Both providers may receive the question and selected context, and each
attempt may incur a charge. A deadline or budget can prevent fallback.

The candidate chat display restores recorded model identity for historical
answers, identifies a successful fallback, exposes recorded unsupported-claim
counts, and shows cited prior chat as conversation history. Source details use
the existing authorized trace bundle and can be unavailable. The answer
renderer handles a limited safe text subset: headings, lists, emphasis and
code; block equations are displayed as LaTeX text, not typeset mathematics.
The trace explorer requests recorded stages for the selected run.

On November 4, the isolated Windows backend suite passed 3,546 tests with 19
skipped, 35 warnings, and zero failures or setup/collection errors. The final
frontend suite passed 533 tests, and frontend lint and type checking passed.
An unsigned engineering installer from clean commit `245658b6` passes checksum,
frozen-payload and NSIS checks; its packaged UI contains the new feature markers.
A November 6 replacement install succeeded; the installed UI and backend match
the build hashes, and local health/readiness report healthy/ready. No live
provider, fallback, saved-chat or full lifecycle acceptance was run. Coordinated
backup and installed acceptance remain open. Repository-wide Ruff
lint currently reports pre-existing errors outside the changed files, Ruff
format reports pre-existing formatting differences, and the active Python
environment does not contain mypy. These are not passing quality gates.
No semantic migration or retrieval-scoring repair is included. Do not infer
production readiness from these checks.

PR #109 merged at `8934d6929912881957187a6a8b98d3c7ce8c7534`. Its
post-merge Cosign job passed, while the dependency scan reported
`CVE-2026-49272` in `oauthlib` 4.0.0 (fixed in 4.0.1). The owner approved
remediation; the runtime and test locks now pin 4.0.1. The local and hosted
security scans pass, as do the full local Windows suite and hosted Windows test.
An unsigned replacement from clean source `11af8185` was installed on November 6;
its UI and backend hashes match the build, and local health and readiness pass
with no blockers. The installer SHA-256 is
`66f3ebb00bbd79ea0525e304b1385f8fdd862dc972a4fb4b0007d9323a385d39`.
The prior build predates this dependency update; live-provider and full installed
acceptance remain open.

On November 4, the stopped Podman disk, desktop data, and prior installer were
copied to a private recovery directory and hash-verified. The copy is not a
tested restore or an encrypted coordinated backup. An initial full test run
appended test records to the existing DMRF tracking log; the log was preserved
and subsequent runs set `MLFLOW_TRACKING_URI` to a temporary directory.
