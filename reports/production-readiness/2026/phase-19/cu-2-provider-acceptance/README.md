# CU-2 provider-refresh live acceptance

## Verdict

**Partial pass; CP19-M remains open and production/public release remains
NO-GO.** The bounded source-level Google call passed. The bounded OpenAI call
used the required `high` reasoning contract but was rejected because the owner
account has no available quota. The later exact-source unsigned engineering
rebuild and strict portable checks pass; signing and installed acceptance do
not.

## Source binding

| Field | Result |
|---|---|
| Live-call source HEAD | `254be21ffe4b8b0ff9233e975530ee12c7ac7c8d` with the reviewed worktree then dirty |
| Exact rebuild source | Clean commit `ab7b1b181d65d0fc10c1a88706258710b2b34807` |
| Exact artifact binding | `DataLogicEngine Setup 4.4.1.exe`, 358,849,159 bytes, SHA-256 `a92b836145bb23eccc2f89c33a005a6ec66683fae28e13824cd988ec18b05156` |
| Signed artifact | Not established |

## Focused contract validation

`python -m pytest tests/unit/test_validate_provider_refresh_acceptance.py tests/unit/test_provider_manifest_phase7.py tests/unit/test_provider_execution_phase7.py -q`
passed **26 tests**. This includes the canonical provider/model IDs, OpenAI
Responses API request shape, explicit `high` reasoning, Google request shape,
and evidence redaction behavior.

## Bounded live calls

| Provider | Model | Contract | Result | Latency | Usage |
|---|---|---|---|---:|---:|
| Google | `gemini-3.7-flash` | Current manifest model | **Pass** | 2,552.15 ms | 10 prompt / 1 completion / 108 total |
| OpenAI | `gpt-5.6-sol` | Responses API, reasoning `high` | **Blocked** — `quota_exhausted` | 3,109.56 ms | No completed response |

A separate owner-requested Google retest also passed in 1,021.73 ms using 10
prompt, one completion, and 84 total tokens. Its sanitized receipt is
`google-live-retest.json`.

The runner made exactly two calls. It used credentials already present in the
local environment, required no re-entry, and did not print or persist any
credential or response body. The machine-readable record is
`provider-refresh-live-acceptance.json`.

## Diagnostic note

The older Phase 1 gateway-staging runner was attempted first for Google. It
reached `gemini-3.7-flash` and created an audit row, but its compliance-release
prompt was classified as `high_stakes` and the candidate was correctly blocked
by the current governed convergence policy. That runner's Tier 2/footer
assertions therefore cannot serve as a simple availability check. Its transient
JSON/SQLite files were moved out of the repository to the system temporary
folder; they are not acceptance evidence.

## Rebuild and signing prerequisite assessment

- The Podman machine is present but stopped. No new data-plane or installed
  acceptance was attempted out of order.
- The repository has local `signtool.exe` copies through the Electron build
  dependencies, but no `CSC_LINK`/`WIN_CSC_LINK` signing material is configured.
- Two current-user self-signed development certificates exist. They are not
  production publisher authority.
- `config/release-trust-policy.json` still sets `production_authorized` to
  `false`, has no approved publisher subjects, and leaves the production
  credential boundary pending a hardware or managed signing-service decision.

Because the first CU-2 provider gate is incomplete and production signing is
not authorized, no artifact is signed. At the owner's direction, independently
safe source correction and unsigned exact-source portable acceptance proceeded
through 4.4.1. See
`exact-source-4.4.1-rebuild-engineering-acceptance.md`; this is portable
engineering evidence, not a production candidate. The older
`exact-source-rebuild-engineering-acceptance.md` remains superseded 4.4.0
history.

## Full-history secret-scan closure

The recorded scheduled Security failure is now formally closed:

- run `31561547302` used TruffleHog 3.96.0 and reported 135 verified Lob
  detector results;
- later scheduled runs `31859901999`, `31922838142`, and `31989275082` passed;
- scheduled run `32093054806`, job `95578937904`, scanned 1,298 commits,
  262,141 chunks, and 2,632,118,047 bytes with TruffleHog 3.97.0 and finished
  with zero verified and zero unverified secrets; and
- push Security run `32102824942` passed at current HEAD `254be21f`.

The historical Lob results are dispositioned as no longer current verified
credentials. This closes the specific recorded finding without waiving future
secret-scan failures. The machine-readable receipt is
`full-history-secret-scan-closure.json`.

## Exact next action

Install the exact 4.4.1 artifact hash recorded above and prove a normal Google
chat passes Layer 4, calls the configured provider once, and produces validation
telemetry. Restore or replenish the OpenAI account quota, then rerun:

```powershell
python scripts/validate_provider_refresh_acceptance.py --provider openai
```

After OpenAI passes, rerun both providers for one complete receipt and obtain
owner-authorized production signing material. Rebuild/sign/timestamp from the
then-current exact commit before treating any artifact as the final CP19-M
candidate; rebuild again if packaged source or packaged documentation changed
after `ab7b1b181d65d0fc10c1a88706258710b2b34807`.
