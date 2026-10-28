# Frontend, Backend and Knowledge Retrieval Repair Plan

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-PLAN-REVIEW-2026-10-26 |
| Document version | v1.1.3 |
| Product version | 4.4.6 at review |
| Review baseline | main `f91dd4919c6a5c3265c9fc82bdbb388f15a3b5aa` |
| Date | 2026-10-26 |
| Status | Owner-approved fast-track; source repairs and offline index preparation in progress; installed acceptance open |
| Owner | Production Program Owner |
| Reviewer | Kevin Herrera |
| Release posture | Production/public release remains NO-GO |

## Purpose and authority

Consolidate the frontend review and the backend, database and retrieval review
into an ordered repair and verification plan. The reviews were source-based;
the installed app, its current data, and live provider behavior were not
examined. Two controlled probes showed that a failed vector search may return
no warning and that an empty vector-write result may be reported as success.
The focused backend suite passed 34 tests; the frontend suite passed 506 tests.
These results do not establish search quality or installed acceptance.

## October 27 progress checkpoint

Kevin approved the additional ownership-deletion repair on October 28. Source
`ebf835d2` resolves nested/JSON ownership and database-confirmed legacy IDs,
keeps user scope separate from tenant scope, and blocks shared/conflicting
ownership before mutation. Ingestion IDs now include owner scope and scalar
owner fields reach new materializations. Canonical queued knowledge delivery
rechecks the retained SQL source and deletion receipts under the shared lock.
Sixty-six focused Windows tests pass, including concurrent delivery/deletion.
The original adapter reproduction now reports zero actual remnants. The native
PostgreSQL/Chroma/Neo4j probe deletes 602 synthetic search records and 601 graph
nodes, preserves another owner in the same tenant, and blocks shared ownership.
Its cache lifecycle effect was stubbed, so it is not installed lifecycle proof.
See `reports/ingested-ownership-deletion-fixed-probe-20261028.json` and
`reports/native-owner-deletion-probe-20261028.json`. The isolated test services
and network were removed and the data machine restored to stopped. Full Windows
regression is in progress. No customer cleanup or retained-data migration ran.

October 28 final recovery gate: runtime `ae4c2978` and diagnostic test changes
from `fe870b5c` pass 3,433 Windows tests, 19 skipped, 35 warnings, and zero
failures/setup/collection errors. Forty-one focused checks pass. Preserve the
prior persona-causality failure and its unconfirmed cause: the module, 1,056
governance tests, twenty isolated repetitions and final full run subsequently
pass. Reports are `reports/chat-*20261028.txt`. No assertion, budget or policy
was weakened. Installed restart/outage recovery remains open.

October 28 recovery checkpoint: source `d0847d74` adds atomic, content-free
chat-message outbox records and bounded recovery through the existing worker.
Delivery rechecks retained source ownership/fingerprint and user-deletion
receipts under the shared lock. Retention clears retry envelopes. Forty focused
Windows tests pass, including delayed and interrupted recovery. The full Windows
run reported 3,431 passed, 19 skipped and one documentation-authority failure
for the new candidate note; the missing classification was corrected and the
nine authority tests pass. Final full-suite and installed recovery acceptance
remain open. This only queues newly persisted turns, not a backfill of old chats.
The broader synthetic R-3 candidate is documented in
`docs/evaluation/RETRIEVAL_QUALIFICATION_CANDIDATE_2026-10-28.md`; its acceptance
starting corpus and criteria were approved by Kevin on October 28. The existing locked embedding stack was
inventoried and audited without adding dependencies: about 745 MiB installed,
excluding model files, and no known advisories in the candidate audit. A source
model probe with socket connections blocked loaded 384-dimensional embeddings,
ranked a relevant passage above an unrelated one, and attempted no connections.
Frozen packaging is still being qualified; the active app is unchanged.

October 28 retention checkpoint: Kevin approved fail-closed cross-store session
cleanup. Source verifies chat-index deletion before transcript deletion and
coordinates the active gateway writer, profile deletion and session cleanup
through a shared runtime lock. Partial batches are reported, and policies that
require unavailable session or trace archival stop rather than report a false
archive. Forty-four focused Windows tests pass, including concurrent synthetic
writes. The full Windows suite using locked dependencies passed 3,423 tests,
19 skipped, 35 warnings, and no failures or setup/collection errors at runtime
source `b6f2632d`. A disposable cached Chroma container verified deletion of a
synthetic session, preservation of another session, and repeat deletion. The
container was removed and the data-service machine was restored to stopped.
This does not establish installed behavior, durable chat-index retries, or
coordination with non-cooperating processes.

Later source work corrects unacknowledged document and knowledge-node vector
writes: documents report an explicit internal retrieval error for incomplete
writes, and failed knowledge-node materializations remain retryable. Index
failure logs no longer include exception text. A focused recovery test and 66
related backend tests pass. The chat client also restores current chat and
trace rooms after a connection returns; 70 focused frontend tests pass. The
sequential Windows backend suite at `e25170a9` passed 3,410 tests with 19
skipped, 35 warnings, and no test/setup/collection errors. The frontend suite
passed 521 tests, and the Electron-mode frontend build passed at the same
source checkpoint. Installed verification remains open.

A reproducible offline screen of 12 public documentation sections and 12
manually written questions found hash ranking top-1 1/12 and top-4 4/12,
lexical top-1 4/12 and top-4 8/12, and MiniLM top-1 10/12 and top-4 12/12.
Using simulated squared-L2 ranking with the existing 0.15 threshold retained
the target for 0/12 hash and 1/12 MiniLM questions. Model truncation applies.
This small screen uses public documents, not retained customer data; it does
not qualify a threshold, approve an index cutover, or measure production accuracy.
The reproducible tool is `scripts/evaluate_project_docs_retrieval.py`.
The same screen includes eight manually chosen unrelated questions. On this
small set, MiniLM thresholds 0.15, 0.00, -0.25, and -0.50 retained 1/12,
7/12, 11/12, and 11/12 known targets respectively, while none of the eight
unrelated questions crossed those thresholds. These queries and sections are
too few and too easy to establish false-positive rates or select a threshold.
The optional production-style chunker produced 12 pieces for these short
sections; MiniLM retained the same 10/12 top-1 and 1/12 at 0.15. The hash
top-4 result changed from 4/12 to 1/12 after chunk normalization, illustrating
that this projection is sensitive to exact text representation.

Kevin authorized this repair as a separate fast-track while Phase A and release
gates remain open, and approved an offline MiniLM model with a separate,
recoverable index. Source changes now cover session-scoped chat and trace,
session-title search, Truth Engine measurement display, explicit retrieval
failure warnings, chat-index acknowledgments, filtering the active session
before the recall limit, and per-run graph-status narratives. Focused frontend
and backend tests passed. A Windows full backend run passed 3,395 tests, 19
skipped, zero failures or setup errors, and 35 warnings before the later graph
status changes. A subsequent full run passed 3,400 tests but reported one
setup or teardown error in `test_durable_runner_fails_interrupted_work_without_replay`;
the captured summary did not retain the error detail. The test and its full
six-test module pass when rerun independently. The cause is not established.
A subsequent sequential Windows backend run at `04885301` passed 3,401 tests,
with 19 skipped, 35 warnings and zero failures, setup or collection errors. The
backend and backend tests have since changed. At `1767a887` the full
frontend suite passed 520 tests across 93 files, and frontend lint and type
checking passed. The unrestricted Python lint and format
gates have existing failures on both main and the repair branch, and `mypy` is
not installed in either checked environment.
The October 27 PR #98 dependency security scan subsequently reported seven
advisories for Authlib 1.7.2. The reviewed pin and lock were updated to 1.9.1
and the local locked-dependency audit and GitHub scan at `453bd415` passed.
The full Windows backend suite with Authlib 1.9.1 subsequently passed 3,401
tests, with 19 skipped, 35 warnings, and no failures, setup or collection errors.

A browser smoke check using simulated local API responses verified session
filtering, New Chat trace clearing and unmeasured confidence display. It also
exposed repeated socket connections while the backend was unavailable; the
client now reuses its pending connection, with focused test coverage and a
repeat browser check. This was not a test of an installed application or a live
provider. The Electron-mode frontend build passed before that socket change;
an exact-source installer and installed acceptance remain open.

The isolated retrieval screening used eight synthetic documents, eight initial
questions, and twelve later synthetic questions. With cosine ranking, hash
projection had top-1 0/8 and 2/12; token overlap 7/8 and 9/12; offline MiniLM
8/8 and 12/12. These small synthetic results do not establish production
accuracy, threshold suitability, installed behavior or customer-data quality.
With a simulated squared-L2 score of `1 - distance` and the current `0.15`
threshold, the intended source passed within the top four for 0/8 and 0/12
hash queries, and 5/8 and 6/12 MiniLM queries. This is a simulation, not a live
Chroma threshold qualification; it shows that good ranking alone is not enough.
A subsequent isolated Chroma 1.5.9 query using the same synthetic corpus and
threshold reproduced those counts, including MiniLM ranking 8/8 and 12/12 first.
The disposable container was removed. Neither experiment qualifies a threshold
on representative customer data or authorizes a cutover.
Cached model revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, weights
SHA-256 `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`,
and complete local file inventory SHA-256
`8c4ccf957588dbe5df32048c58a29a8e81fd46e3fa8d940e8d7777b348b0c979` were
used offline; cached model card reports Apache-2.0. The source-only preparation
tool requires source and target to be marked disposable test collections; it
creates no collection, does not activate a target and never deletes the old
index. Mocked tests cover partial resume, changed source, unexpected target
records, owner metadata and vector verification. An isolated Chroma 1.5.9
container, using an already-cached image and three synthetic records, passed
preparation, source/target count, owner-filter and session-exclusion checks.
The temporary container was removed; the preexisting data-plane VM was returned
to its prior stopped state. This is not installed or retained-data qualification.

**Still open:** qualification and packaging of the complete local ML stack
(the existing installer spec excludes it), a broader approved relevance and
threshold evaluation, coordinated write/deletion/retention and race-safe
cutover, installed recovery/rollback and index synchronization retry, installed
graph-use visibility, final quality gates,
and exact rebuilt/installed/provider acceptance. The active app continues to
use the existing hash projection and index. No user data has been migrated and
no new installer has been built for this repair. Do not treat the shadow-index
tool or this source checkpoint as enabling semantic retrieval in the app.

A separate source review found that session cleanup could leave `chat_history`
vectors and report an archive that was never created. Kevin approved the
repair described in the October 28 checkpoint above. No user-data cleanup was
performed during review or synthetic testing.

During the index-lifecycle review, a newly discovered deletion defect was
reproduced: a failed Chroma lookup could be treated as zero remnants. Kevin
approved a separate repair. The adapter now raises a safe explicit error, and
the deletion coordinator records a partial failure. A focused test covers the
failure and redaction; an isolated Chroma 1.5.9 test removed one synthetic
owner record, preserved another owner's record and verified no remnants. The
isolated container was removed. Installed and concurrent deletion qualification
remain open.

### Review finding inventory

| Review finding | Source checkpoint | Remaining qualification |
|---|---|---|
| A reply can appear in another conversation | Session and request guards added; delayed-reply and revisit tests and full frontend suite pass | Installed switch/background-run checks |
| Late history can overwrite the selected conversation; history failure looks empty | Stale loads ignored; error and retry shown; targeted tests pass | Installed history failure and recovery |
| New Chat can retain another run's trace | Chat panel scoped to the selected run; fresh-draft and saved-run tests pass | Installed live streaming, saved history and trace isolation |
| Truth Engine shows unavailable confidence as zero and labels recent runs active | Unmeasured/error/zero are distinguished and metric labeled **Average Run Confidence**, approved by Kevin; targeted tests pass | Installed display and accessibility |
| Recent-session search does not filter | Title filter and no-match state added; targeted tests pass | Installed keyboard and session-selection checks |
| Default hash projection does not provide semantic search | Offline MiniLM screened and test-only separate-index preparation implemented; active app is unchanged | Packaged model, broader evaluation, live-data migration, lifecycle and safe cutover |
| Vector query failure looks like an empty search | Typed failure, existing warning path and trace narrative added; backend suite passes | Installed outage/recovery and final exact-source suite |
| Failed chat index writes can appear successful | Write acknowledgment, backend status and current-answer warning added; targeted tests pass | Durable bounded retry/reconciliation, deletion safety, and installed verification |
| Active-session results crowd out earlier chat recall | Owner/session filter applied before limit; focused tests and isolated Chroma synthetic check pass | Installed retained-data and authorization coverage |
| Graph use and limitations are unclear | Conditions explained in chat; per-run status narrative added with Kevin's approval and focused tests | Installed graph-enabled, disabled, missing-source and outage checks |
| Additional deletion finding: failed Chroma lookup could look like zero remnants | Kevin approved the repair; failure and isolated successful-deletion tests pass | Installed cross-store failure, retry and concurrent deletion qualification |

Status is source-level unless explicitly identified as an isolated Chroma test;
no item above is claimed complete in the installed application.

This is a supporting work proposal, not a replacement for
`PRODUCTION_COMPLETION_PLAN_2026.md`, `TODO.md`, `HANDOFF.md`, or the compliance
work orders in `docs/compliance/REMEDIATION_PLAN.md` and
`docs/compliance/remediation_tasks.json`. Phase A remains open and blocks the
remediation phases. Before implementation, reconcile each item with those
work orders and obtain any required task disposition or owner approval; this
plan alone does not authorize work outside task `allowed_paths`, override
human gates, or change an external response contract. Keep the owner-approved
Standard-mode behavior that permits an answer without qualifying local evidence.
Make a retrieval failure visible without silently representing it as no match;
any change to API schema or answer-release policy needs the required decision.

Do not add outbound destinations, telemetry or automatic provider calls.
Preserve local ownership, authorization, source eligibility, content defense,
retention and trace provenance. No test may be removed, skipped or weakened to
make a gate pass. Reverify each premise at the actual implementation revision.
One implementation task should have one appropriately scoped commit; honor the
active work order's branch, path and human-gate rules. Do not change product
version for this plan. Apply the owner's patch-version rule when a future major
update is packaged, subject to the existing version authority and gates.

## Priorities and dependencies

| Order | Work | Depends on | Main outcome |
|---|---|---|---|
| 0 | Reproduce and capture baseline | None | Confirm actual source and installed behavior and identify applicable work orders |
| 1 | Conversation isolation and trace scoping | 0 | Correct session, answer and trace associations |
| 2 | Truthful retrieval and indexing status | 0 | Distinguish empty results, service failures and failed index writes |
| 3 | Search quality and index migration | 2; design and required approvals | Relevant local material can be found and existing indexes remain recoverable |
| 4 | History, graph and user-facing search | 1-3 as applicable | Accurate recall, explicit graph usage and usable session search |
| 5 | Truth Engine metrics | 0 | Missing measurements and record scope are represented honestly |
| 6 | End-to-end qualification and documentation | 1-5 | Source, installed and provider evidence tied to the final artifact |

## R-0 — Reproduce and establish baseline

- Record the exact source commit, installed artifact version/hash, storage
  profile, service availability and whether a test uses real stores or fakes.
  Avoid copying credentials, customer prompts or database contents into reports.
- Reproduce session switching, New Chat, failed retrieval, failed vector write,
  old-session recall, unmeasured confidence and search-field behavior. Capture
  observable outcomes and minimal safe logs. Do not alter the user's data.
- Map work to existing TODO entries, CP9/CHAT-QC acceptance, and compliance
  work orders. In particular, the New Chat trace and Truth Engine findings are
  already open in `TODO.md`; avoid duplicate closure claims. Identify any
  additional security finding and honor the repository's stop-and-ask rule.
- Baseline source and installed environments separately. Collect failing
  regression cases first; do not characterize a passing mock test as installed
  or live-provider proof.

Exit: each item has a current reproducible result or an explicit unverified
status, named owner/work order, scope and dependencies. Phase A and all
human-gate decisions remain independently open.

## R-1 — Isolate conversations, requests and trace state

**Findings:** an in-flight response can append to a newly selected session;
late history loads can overwrite the current conversation; failed history loads
clear the display without an actionable explanation; New Chat can show an old
run in Live Trace. These are related but require distinct checks.

- Bind send, upload, completion, errors, loading state and request IDs to the
  originating session/draft and request. Define cancellation or background-run
  behavior when switching; do not discard a persisted answer or present it in
  the wrong conversation. Prevent an earlier request from clearing a later
  request's loading or trace state. Review session creation races as well.
- Ignore or cancel stale history requests on session change, including failures;
  show a recoverable load-error state without presenting failure as an empty
  transcript. Preserve durable server records and existing access controls.
- Scope Live Trace and its progress/feed data to the selected session and its
  current or retained run. A fresh draft has an empty state; returning to a
  saved session selects only its own trace. Do not delete persisted traces.
- Add deterministic delayed-promise tests for A-to-B switching, New Chat while
  a send or history load is pending, stale errors, concurrent request cleanup,
  session creation and restoration. Cover trace updates and same-session flows.

Exit: regressions pass; no answer, error, history or trace from session A is
shown as belonging to B or a fresh draft. Existing session persistence and
cancellation behavior remain tested. UI review includes keyboard and narrow
window behavior on the supported desktop platform.

## R-2 — Make retrieval and index failures explicit

**Findings:** vector backend and RAG wrappers can collapse failures into empty
results; chat-vector writes can return no IDs but still be marked successful.

- Define a typed internal outcome for successful results, empty results,
  partial results and service/embedding failures. Propagate it through every
  vector and RAG layer to the governed trace and an appropriate user-visible
  state without exposing secrets or mislabeling unavailable as no evidence.
  Preserve the approved Standard-mode answer policy and existing provider-call
  budget. If the remedy needs an external contract change, obtain the required
  owner decision before implementing it.
- Check the actual stored IDs/acknowledgment and propagate false returns as well
  as exceptions. Relational transcript persistence and vector synchronization
  must report distinct outcomes. Provide a retry/reconciliation mechanism with
  bounded, idempotent processing and clear failure status; preserve the user's
  retention and deletion settings.
- Inject vector connection errors, query errors, embedding errors, empty
  results, partial-source failures, empty/partial write acknowledgments and
  recovery. Verify trace and UI status, logging redaction, and no silent default.

Exit: a failed vector read/write is never reported as a successful empty
search or successful synchronization; valid empty results remain distinguishable.
The existing no-evidence release rule remains unchanged unless separately approved.

## R-3 — Improve retrieval quality and migrate indexes safely

**Finding:** the default SHA-256 projection is deterministic but is not a
semantic text embedding; relevant text may be missed. The review's small
similarity probe is illustrative, not a quality benchmark.

- First build a representative, owner-approved local evaluation set covering
  paraphrases, exact matches, unrelated distractors, long documents, source
  permissions, retention and known-answer queries. Measure recall/ranking and
  latency against the current baseline; record the evaluation corpus and method.
- Compare a qualified local semantic index and a local lexical/hybrid approach.
  Record model/library provenance, license, size, supported Windows packaging,
  resource costs, accuracy and data-handling implications. No provider egress
  is implicit. Adding a dependency, outbound destination or altering data
  handling requires the repository's specified owner decision before execution.
- Select a versioned embedding/index and metric only after evaluation. Define
  dimension, distance-to-score conversion, relevance threshold and source
  diversity with measured justification. Never mix incompatible vectors in a
  collection or present a hash score as semantic confidence.
- Design a resumable, idempotent, versioned reindex from authorized source
  records and retained chats; verify checksums, permissions, deletion, counts,
  interrupted recovery, rollback and storage requirements. Preserve the old
  index until the replacement is verified; never reindex or delete user data
  without the appropriate authorization and backup/recovery plan.

Exit: the chosen local method meets explicitly approved, recorded relevance and
latency criteria on held-out cases, security and source-authority controls still
pass, and migration/rollback is demonstrated against representative retained
data. No blanket accuracy or production claim follows from a small sample.

## R-4 — Complete recall, graph and session search

- Fetch enough authorized cross-session candidates before excluding the active
  session, within a documented bound. Test many current-session matches,
  older relevant chats, multiple owners, disabled history, deleted sessions and
  unavailable index. Never broaden permissions to increase recall.
- Clarify when graph relationships are used, why a run has none, and whether
  graph retrieval is unavailable or disabled. Verify session/owner/tenant
  permissions, bounds, source authority and citations when graph context is
  requested. Do not claim every chat automatically creates verified graph facts.
  Any default or data-handling change needs the applicable owner decision.
- Connect the existing recent-session search field to a bounded, accessible
  filter, with no-match, clear and keyboard states. Verify titles and restored
  session selection; do not expose another owner's sessions.

Exit: old-session recall and session search work on representative tests; graph
usage and limitations are visible and traceable, with authorization preserved.

## R-5 — Correct Truth Engine summaries

- Show unavailable/not measured when no qualifying confidence exists or when
  loading fails; preserve an actual measured zero. Reject non-finite values.
- Name the count according to what is measured: the bounded recent trace
  inventory, or explicitly compute genuinely active runs. Explain the sample
  limit and denominator for averages and failure rates; do not present an
  empty or unavailable denominator as a measured zero.
- Test empty, failed, partially measured, zero, non-finite and mixed-status
  runs. Preserve existing documented confidence meaning and do not imply that
  a confidence average proves factual accuracy.

Exit: the displayed labels, values and error states match their actual data.

## R-6 — Integrated validation, documentation and artifact

- Run targeted tests for each repair, then required Windows backend tests
  `python -m pytest tests/ --no-cov -q --tb=short -rE`, with zero collection and
  setup errors, plus frontend tests, lint, typecheck, build and applicable
  accessibility/browser checks. Run the repository's required security,
  governance and documentation checks. Record results and any failures.
- With a safely prepared local dataset, test ingestion, source authority, index
  synchronization, relevant retrieval and prompt evidence; test same-session
  continuation, cross-session recall, trace linkage, graph use and service
  outage/recovery. Include deletion/retention and retained-data upgrade tests.
- Rebuild the Windows app after implementation and source checks are complete. Follow the product patch-version rule for a major
  update, update version authorities consistently, and record source commit,
  artifact hash, signature and packaged resources. Do not silently replace the
  user's existing installer or data.
- Separately verify the exact rebuilt artifact through fresh install, upgrade,
  repair, uninstall and retained-data scenarios, plus an owner-authorized live
  provider question. Record what evidence and trace were actually used; never
  equate completion of the ten layers or refinement with factual verification.
- Update the handoff, TODO, user and operator guides, README and release records
  with measured results and limitations. Preserve failed/historical evidence.
  Commit and publish only when authorized; verify branch, merge and workflows.

Exit: completed items have linked evidence and no unresolved regression.
Installed/provider tests, signing, external review and CP19-M remain separate
release gates; no source test or unsigned engineering rebuild by itself changes
NO-GO. If a gate cannot run, record it as open with the exact reason.
