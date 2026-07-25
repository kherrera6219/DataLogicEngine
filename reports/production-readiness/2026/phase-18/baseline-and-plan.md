# Phase 18 Knowledge Algorithm baseline and plan evidence

## Evidence identity

| Field | Value |
|---|---|
| Review date | 2026-07-25 |
| Source commit | `1321f45a733e55581bd2af3b99f281ae5a411cb3` |
| Review mode | Documentation-first, read-only source/history reconciliation |
| Release effect | Signed rebuild paused; production/public release remains NO-GO |
| Owning requirement | `DLE-FR-011` |
| Owning plan checkpoint | Phase 18 CP18-A |

## Authorities reviewed

The review read the active root plan, TODO, handoff, README, documentation
authority manifest, and the canonical product, architecture, interface, data,
security, lifecycle, traceability, V&V, user, developer, AI-system-card, and
KA/TruthCore documents. Retained whitepapers and their rendered PDF pages were
used only as design and provenance context, not as current-state authority.

The retained design consistently requires modular KAs that are selected when
needed, receive shared governed context and dependencies, return typed results,
leave state mutation to the orchestrator, record their execution in the trace,
and have independent tests. It does not require every KA to run on every
request.

## Inventory baseline

| Surface | Observed state |
|---|---|
| Executable backend registry | 125 IDs: `KA-001` through `KA-117`, seven `L10-KA-*`, and `KA-Master` |
| Numeric implementation modules | 117 |
| Layer-9 implementation modules | 7; invoked by TruthCore but absent from the executable registry |
| Layer-10 implementation modules | 7; registered |
| Historical design/SDK registry | 114 IDs |
| Runtime descriptive metadata | 277 rows |
| Production-enabled entries | 11 |
| Algorithms desktop page | Searchable catalog cards only |
| Direct KA API | Numeric IDs only; disabled entries can be bypassed with a generic nonproduction boolean |
| Runtime engines/registries | KA-Master plus incompatible core engine/loader and SDK handler map |

The 277-row file expanded from the original 114-row catalog in commit
`9db1927d` through generated implementation scaffolding. Many appended rows are
duplicates or generic “Advanced ... Module” entries. It is therefore evidence
to classify, not permission to claim 277 distinct production capabilities.

## Confirmed blocking findings

1. **Identity and semantic collision:** KA-Master merges the 277-row metadata
   into live implementations by numeric ID even when name and purpose disagree.
   The divergence affects many IDs beginning around `KA-036`, so UI descriptions
   and dynamic routing can name a different capability than the executed code.
2. **Unreachable Layer 9:** `L9-KA-001` through `L9-KA-007` are called by the
   live meta-reasoning controller but are not in the master registry. Broad
   exception handlers convert the registration defect into logged skips.
3. **Incomplete production admission:** only 11 of 125 registered entries are
   production enabled. The prior classification checkpoint prevents some
   overclaiming but does not meet the product owner's requirement that every KA
   be production-functional and usable when selected.
4. **Multiple incompatible runtimes:** KA-Master executes module-level `run`
   functions, the core engine attempts a missing modern registry and legacy
   signatures, the legacy loader scans a different implementation folder, and
   the SDK has its own handler registry. These are not one authoritative
   execution path.
5. **Partial and defective selection:** KA-Master uses a bounded keyword
   `elif` chain that references only part of the catalog. Its hypothesis branch
   adds a three-item tuple to a two-item flow contract and fails during flow
   normalization.
6. **False operational effects:** effect-oriented implementations include
   service-mesh, integration-bus, and message-broker behaviors that return
   plausible operational state without proving an authoritative app-owned
   service action.
7. **SDK sample behavior:** SDK modules explicitly label handlers as sample,
   stub, naive, or minimal implementations. They cannot remain an alternate
   production KA runtime.
8. **Incomplete product workflow:** the Algorithms page does not implement the
   documented detail, schema/input, execute/cancel, history, limitation,
   effect-receipt, and trace-navigation workflow.
9. **Insufficient individual proof:** current bulk/import/category tests do not
   provide one named production functional test per canonical KA or prove one
   real application call path per KA.

## No-capability-reduction rule

Phase 18 will not solve the collisions by deleting alternate behavior, silently
renaming an existing ID, or treating generic scaffold count as product depth.
CP18-A must produce a lossless crosswalk that distinguishes:

- canonical distinct capabilities;
- compatible historical aliases;
- semantic duplicates;
- generated generic scaffolds with no distinct contract;
- current executable capabilities whose historical numeric metadata describes
  something else;
- Layer-9, Layer-10, and master controllers;
- implementation gaps requiring a new stable canonical ID.

CP18-A must resolve every distinct preserved capability to one stable ID and an
explicit existing-or-required implementation disposition. The implementation,
schema, selector/call path, individual test, documentation, limitation, and
trace requirements become the verified CP18-B through CP18-G work queue and
must all pass before the source exit gate can permit a rebuild.

## Approved implementation sequence

1. CP18-A — capability/identity crosswalk and one-manifest migration.
2. CP18-B — typed contract, one controller, adapters, generated SDK/catalog.
3. CP18-C — production implementation and authoritative side effects.
4. CP18-D — dynamic selector/DAG and complete application wiring.
5. CP18-E — authenticated API/SDK and accessible desktop workflow.
6. CP18-F — individual functional/failure/security/performance proof.
7. CP18-G — clean full source, governance, security, and packaging-smoke
   qualification.
8. Rebuild the signed release candidate.
9. CP18-H and all retained installed/manual/independent release gates.

## Immediate next evidence

Generate the complete machine-readable CP18-A inventory and proposed canonical
crosswalk without changing implementation identities. Its verifier must report
zero unclassified definitions, implementations, callers, tests, SDK/UI
surfaces, aliases, duplicates, and conflicts before the manifest migration is
approved.

## CP18-A completion

CP18-A passed on 2026-07-25. The deterministic generator and independent
repository gate produced and verified:

| Measure | Verified result |
|---|---:|
| Canonical distinct capabilities | 213 |
| Existing implementation surfaces requiring qualification | 132 |
| Implementation gaps to build | 81 |
| Classified identity conflicts | 62 |
| Generic generated scaffolds retained as history | 64 |
| Confirmed semantic duplicates collapsed to aliases | 1 |
| Similar-name pairs reviewed as materially distinct | 11 |
| Exact name/purpose/contract collisions | 0 |
| Unresolved semantic duplicate candidates | 0 |
| Classified implementation surfaces | 132 |
| Classified integration, caller, API, SDK, and UI surfaces | 132 |
| Unclassified definitions or surfaces | 0 |

The authority keeps current executable IDs stable, restores displaced original
design capabilities under collision-free `KA-1xxx` identities, and scopes
ambiguous historical IDs to their source generation. The existing `KA-113`
router is explicitly reviewed as semantically equivalent to the original
“Query Analysis & Complexity Router” instead of being incorrectly duplicated.

Evidence:

- `ka-capability-inventory.json`
- `ka-capability-crosswalk.json`
- `ka-capability-crosswalk.csv`
- `ka-capability-inventory-summary.md`
- `scripts/build_ka_capability_inventory.py`
- `scripts/verify_ka_capability_inventory.py`

The crosswalk is approved for the CP18-B manifest migration. It does not claim
that the 132 existing implementations are production-qualified or that the 81
missing implementations exist. The signed rebuild remains blocked.
