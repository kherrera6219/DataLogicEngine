# CP19-K Grouped Qualification Roadmap

**Status:** Active

**Plan version:** `2026.08.05-cp19k-grouped.11`

**Baseline:** 27/213 qualified; 186 open

**Planned work:** 36 cohesive batches, numbered 08 through 43

**Current checkpoint:** Batches 08-29 passed; 143/213 qualified, 70 open; Batch 30 next
**Release effect:** None; CP19-L, rebuilding, CP19-M, and every retained
installed/manual/external gate remain unauthorized

## Decision

The earlier arithmetic estimate of 49 batches extrapolated the first seven
small discovery/remediation batches. It is replaced by this reviewed roadmap.
The 186 open rows are grouped by shared production owner, real caller or
transaction, effect port, dependency order, and failure model. The result is 36
planned batches averaging 5.17 KAs each, with a bounded range of two to eight.

The 28 security/operations rows are specifically **not** one batch. They cross
five different product boundaries:

1. content-free observability and diagnostic decisions;
2. durable notification and message delivery;
3. environment/service topology and approved evolution;
4. health, backup, performance, and disaster recovery; and
5. cryptography, key lifecycle, vulnerability, and purple-team evidence.

Combining those boundaries would make it impossible to review notification,
infrastructure, recovery, and cryptographic effects independently or to bind
each effect to the correct owning-service receipt.

## Group totals

| Primary owner | Open KAs | Planned batches |
|---|---:|---:|
| Security/operations lifecycle | 28 | 5 |
| TruthMemory/TruthLink/FROST | 24 | 5 |
| TruthCore L1-L5 | 23 | 4 |
| TruthCore L6-L8 | 17 | 3 |
| Retrieval/graph/memory | 15 | 3 |
| TruthGate | 15 | 3 |
| TruthCore L9 | 12 | 2 |
| TruthCore L10 | 12 | 2 |
| DSQP/Quad Persona | 11 | 2 |
| Provider/gateway | 11 | 3 |
| Governed request/DMRF | 8 | 2 |
| Ingestion | 8 | 1 |
| Simulation | 2 | 1 |
| **Total** | **186** | **36** |

## Ordered batches

The order below is dependency-safe against the canonical manifest. A batch may
move later if its real owner is absent, but it must not move earlier than an
open prerequisite.

| Batch | Cohesive boundary | Owner | KAs | Count |
|---:|---|---|---|---:|
| 08 | Operations observability — **passed 2026-08-02** | security/operations | 091, 092, 094, 095, 098, 099, 100 | 7 |
| 09 | Secure ingestion pipeline — **passed 2026-08-02** | ingestion | 071-078 | 8 |
| 10 | Provider model preparation — **passed 2026-08-02** | provider/gateway | 081, 082, 085, 086 | 4 |
| 11 | Provider model release preparation — **passed 2026-08-04** | provider/gateway | 083, 087-090 | 5 |
| 12 | Knowledge temporal health — **passed 2026-08-04** | TruthMemory/TruthLink/FROST | 023, 052, 064, 1082, 1083, 1093, 1105 | 7 |
| 13 | L1 context and dependencies — **passed 2026-08-04** | TruthCore L1-L5 | 003, 011, 015, 017, 025, 040 | 6 |
| 14 | Retrieval provenance and scoring — **passed 2026-08-04** | retrieval/graph/memory | 018, 079, 1049, 1077, 1092 | 5 |
| 15 | DMRF core routing — **passed 2026-08-04** | governed request/DMRF | 031, 036, 1073, 1107, KA-Master | 5 |
| 16 | Adversarial/privacy gate — **passed 2026-08-04** | TruthGate | 034, 1074, 172, 173 | 4 |
| 17 | Knowledge trust and containment — **passed 2026-08-04** | TruthMemory/TruthLink/FROST | 062, 065, 1071, 1094, 1109, 117 | 6 |
| 18 | Knowledge expansion/promotion — **passed 2026-08-04** | retrieval/graph/memory | 029, 1079 | 2 |
| 19 | Persona foundation DAG — **passed 2026-08-04** | DSQP/Quad Persona | 012, 013, 028, 030, 038 | 5 |
| 20 | L6 evidence/confidence/entropy — **passed 2026-08-04** | TruthCore L6-L8 | 002, 009, 014, 026, 035, 1041, 1042, 1102 | 8 |
| 21 | DMRF adaptive routing — **passed 2026-08-04** | governed request/DMRF | 033, 058, 059 | 3 |
| 22 | Retrieval store maintenance — **passed 2026-08-04** | retrieval/graph/memory | 080, 1039, 1040, 1043, 1046, 1048, 1076, 1078 | 8 |
| 23 | Knowledge content evolution — **passed 2026-08-04** | TruthMemory/TruthLink/FROST | 051, 053, 054, 055, 063 | 5 |
| 24 | Knowledge lifecycle analytics — **passed 2026-08-05** | TruthMemory/TruthLink/FROST | 1086, 1088, 1089, 1095 | 4 |
| 25 | L10 oversight and release — **passed 2026-08-05** | TruthCore L10 | 020, 021, 1106, 1112, 116 | 5 |
| 26 | System-integrity gate — **passed 2026-08-05** | TruthGate | 1045, 1099, 1104, 1108, 1110 | 5 |
| 27 | Knowledge release/long-horizon | TruthMemory/TruthLink/FROST | 1096, 1111 | 2 |
| 28 | Regulatory/compliance gate | TruthGate | 016, 027, 1090, 169, 174, 176 | 6 |
| 29 | Persona adaptation | DSQP/Quad Persona | 057, 068, 069, 1037, 1075, 1084 | 6 |
| 30 | L6 planning control | TruthCore L6-L8 | 006, 007, 060 | 3 |
| 31 | L6 advanced reasoning | TruthCore L6-L8 | 066, 067, 1036, 1044, 1047, 1085 | 6 |
| 32 | L9 synthesis/explainability | TruthCore L9 | 008, 019, 056, 1038, 1087 | 5 |
| 33 | Exact L9 loop suite | TruthCore L9 | L9-KA-001 through L9-KA-007 | 7 |
| 34 | Exact L10 release suite | TruthCore L10 | L10-KA-001 through L10-KA-007 | 7 |
| 35 | L1 inference/mapping | TruthCore L1-L5 | 041, 043, 044, 049 | 4 |
| 36 | L1 signal analysis | TruthCore L1-L5 | 039, 045, 046, 047, 165, 167 | 6 |
| 37 | L1 language/identity/explanation | TruthCore L1-L5 | 048, 050, 161, 162, 163, 168, 178 | 7 |
| 38 | Provider API/external research | provider/gateway | 111, 1114 | 2 |
| 39 | Operations delivery/messaging | security/operations | 093, 110, 112, 114, 115 | 5 |
| 40 | Operations health/recovery | security/operations | 107, 108, 109, 1097, 1098, 138 | 6 |
| 41 | Operations crypto/vulnerability | security/operations | 139, 180, 181, 183 | 4 |
| 42 | Simulation chaos/rollback | simulation | 1101, 1103 | 2 |
| 43 | Operations topology/evolution | security/operations | 101-105, 1100 | 6 |

## Qualification contract for every batch

Every row still requires its own named semantic test, positive and negative
selector proof, real owning-path test, complete trace, limitation review,
security review, effect review, and performance evidence. Grouping shares the
owner fixture and transaction tests; it does not weaken individual evidence.

Effect-oriented batches must additionally prove that:

- the KA returns a decision or proposal and never claims the effect itself;
- the production service applies the exact admitted operation;
- idempotency, authorization, failure, and rollback behavior are explicit;
- the receipt is bound to the pre-effect KA plan and proposal identities; and
- no installed, external-provider, notification, infrastructure, or recovery
  acceptance is inferred from source-only evidence.

The machine-readable authority is
`config/phase19-ka-grouped-batches.json`. Its integrity test proves exact
186-row baseline coverage, one owner per batch, bounded batch size, unique
membership, dependency-safe order, and exact reconciliation of completed
batches with the current 70-row open matrix.
