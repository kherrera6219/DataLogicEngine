# Phase 6 Rollback Notes

Date: 2026-07-13

1. Preserve a verified application-data backup before downgrading an installed
   deployment. Source, API/UI contracts, and migration changes must roll back as
   one unit.
2. Migration `c2d3e4f5a6b7` adds trace citation, validator, and quality-decision
   tables and extends evidence/claim/link records. Downgrade deletes those new
   records; export required audit evidence first.
3. Existing Phase 6 traces may remain as historical audit data when the runtime
   is upgraded again. Do not translate null/`not_measured` values into numeric
   defaults for backward compatibility.
4. If evidence or validator persistence fails, fail the governed request and
   restore the last complete runtime/data snapshot. Do not bypass trace or
   evidence writes to regain availability.
5. If a provider/model regresses, quarantine only that matrix row and restore
   the last approved model/configuration. One provider's result cannot approve
   another provider.
6. Do not select SeaweedFS during rollback. MinIO remains the approved
   product-specific object-store architecture until Replacement Control closes.
