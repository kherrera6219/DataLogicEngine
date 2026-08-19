# CU-5 source and external-knowledge checkpoint

| Field | Value |
|---|---|
| Checkpoint date | 2026-08-18 |
| Source HEAD | `254be21ffe4b8b0ff9233e975530ee12c7ac7c8d` |
| Source status | Nested refinement detail implemented and focused validation passed |
| External status | Replacement exports published; stale-file archive/de-rank blocked by Google file-scoped write authorization |
| Installed status | Open; must be proven against the later exact signed CP19-M package |
| Release effect | None; production/public release remains **NO-GO** |

## Trace-detail source closure

The existing `TraceStage.outputs.refinement` object is the persisted authority
for a canonical `dle.canonical-refinement-result.v1` receipt. The Trace Explorer
now recognizes only that schema and renders:

- registry version, receipt status, recorded step count, rewrite authorization,
  provider subcall count, and blocking step;
- each named step's number, identifier, status, and reason; and
- selected, executed, and reused KAs plus finding, constraint, and effect counts.

The UI reads the nested object already returned by the aggregate trace bundle.
It does not create a new route, table, copy, or competing trace authority. It
also limits presentation to named governance fields rather than dumping KA
results, findings, effects, or arbitrary nested output content.

Focused validation at this checkpoint:

| Gate | Result |
|---|---|
| Trace persistence and aggregate bundle contracts | 4 passed |
| Trace detail React tests | 3 passed |
| Frontend TypeScript check | passed |
| Focused frontend lint | passed |
| Full frontend unit suite | 483 passed |
| Optimized Next.js production build | passed; 31 static pages generated |

This is source evidence only. Packaged visual, keyboard, scaling, contrast, and
screen-reader acceptance remain part of the exact signed CP19-M candidate.

## External replacement publication

`scripts/generate_spec_exports.py` regenerated the two review exports, and
`tests/unit/test_spec_exports.py` passed 3/3 before upload.

| Published file | Local bytes | Local SHA-256 | Google Drive file ID | Verification |
|---|---:|---|---|---|
| `ka_registry_213.yaml` | 544,964 | `40ef20ec5d4d788bcdfa402ead18faeb5b05dca6a8259ecdb56b933f2b5ae2ab` | `1mlD37Pmj-Xj08VB_pq7ppSARkt-cAXTC` | Drive readback name, MIME type, and byte count match |
| `17_axis_coordinate_schema_axes14-17.yaml` | 799 | `f9d2f1880acd0b7c78cfd498d8a3a1df5728b62304968b17cd6348d3f67c2da7` | `1MP_D9IbYZLFXsbX1Ebq3R2nWAB81SnIG` | Drive readback name, MIME type, and byte count match |

The files were published to the same connected Google Drive root containing the
three exact stale analyses named by F-16. The following folder was also created
for their archive disposition:

- `Archive - Superseded DataLogicEngine Analyses`
- folder ID `17yzwzbkxAH1Pw5fTXr0DxmLj25QxiFbN`

## Remaining external authorization blocker

Move/rename was attempted only for these exact stale Google Docs:

| Current title | Google Drive file ID | Result |
|---|---|---|
| `UKG_DataLogicEngine_Gap_Analysis_2026_05_23` copy 1 | `1ojZX1o5unNnA8KjDUcI5pWVM019p72gNgALwOMbYpvk` | blocked |
| `UKG_DataLogicEngine_Gap_Analysis_2026_05_23` copy 2 | `1XGVRn5GL1iiH_L9t2xDSDtelQUNEaCcaJ_d-OQYOR0w` | blocked |
| `UKG_DataLogicEngine_Validated_Gap_Analysis_v2` | `1EHuuJlwFFiEf7U26es5pS5Xl0OY_lC6OgaNLUxyiukg` | blocked |

Google returned `403 appNotAuthorizedToFile` for each target: the connected app
can discover/read those older Docs but has not been granted write access to
them. They remain unchanged in the Drive root. A user with file authority must
grant this app write access or manually move/rename the three documents into the
created archive folder. Publication of the current replacements is complete;
the stale-document archive/de-rank action remains open.
