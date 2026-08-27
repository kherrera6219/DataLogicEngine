# Compliance & Remediation Corpus

Everything governing the DataLogicEngine compliance remediation program. Authored August 17–18, 2026.

**Agents:** the entry point is `/AGENTS.md` at repo root, not this file. This directory is read on demand.

---

## Reading order

| # | File | Read it when |
|---|---|---|
| 1 | `REMEDIATION_PLAN.md` | **Start here.** 44 work orders (`CR-A0` … `CR-G12`) in 7 phases, each with a deterministic shell-command exit gate, allowed paths, and stop conditions. |
| 2 | `remediation_tasks.json` | You need to pick the next unblocked task, or you want dependencies / `allowed_paths` / gates as data rather than prose. |
| 3 | `STANDARDS_BLUEPRINT.md` | You need to know *why* a task exists — which standard, regulation, or buyer requirement it serves. |
| 4 | `EXTERNAL_REVIEW_2026-08-16.md` | You need the original evidence for a finding, or want to verify a premise before acting on it. |

Generated evidence goes in `/reports/remediation/`, never here. This directory is authored; that one is produced.

---

## The program in one paragraph

An independent code review on August 16, 2026 reported three things that matter: 40 security tests erroring at setup on its Windows baseline; a confidence score gated at 0.995 that is a weighted average of pass-rate fractions with a `0.5` fallback on exception and no calibration behind it; and 1,444 lines of "live pipeline engine" whose core imports failed. The setup-error count is historical: the 2026-08-27 4.4.3 qualification completed 3,317 Windows tests with 19 skipped and zero failures or setup errors, so CR-A0 must capture a fresh commit-bound baseline before CR-A1 is treated as open work. The current documentation/evidence commit `43fd86df...` also has passing Deploy, Security, and CI/CD workflows, but neither result dispositions the human gate. A compliance blueprint written the next day established that DataLogicEngine is installed software rather than SaaS — which removes FedRAMP, SOC 2, HITRUST, and multi-tenancy obligations entirely, and makes product-manufacturer duties (supply chain, signing, egress proof, honest documentation) the whole game. A market decision on August 18 excluded the EU, removing the Cyber Resilience Act, EU AI Act, GDPR, NIS2, and DORA. What remains is a verification-first 44-task program whose common purpose is making the system's claims about itself as strong as the claims it makes about everything else.

---

## Standing facts that constrain every task

- **Deployment:** installed software on a workstation, server, or VM. The approved boundary permits provider egress only to customer-configured model endpoints and exposes a local API to client software. CR-B must prove that enforcement and air-gap operation; neither is represented here as completed evidence. No approved telemetry, license check-in, or phone-home.
- **Market:** United States only. EU frameworks out of scope as of 2026-08-18.
- **Not applicable:** FedRAMP (authorizes cloud services), SOC 2 (audits a service organization), HITRUST, multi-tenancy controls, ConMon.
- **Applicable:** NIST SSDF 800-218 + 800-218A, NIST 800-53 Rev 5 (for customer ATOs), NIST 800-171 r3 / CMMC if CUI, FIPS 140-3, Section 508, ISO 27001 (narrow scope), ISO 42001, OWASP GenAI LLM Top 10 2026, OWASP Agentic Top 10 2026, HIPAA (as a deployable product, likely not as a Business Associate), SR 11-7, Colorado ADMTA from 2027-01-01.
- **No external deadline remains.** Every task is justified commercially — a buyer asks, and the answer must be true.

---

## Program exit criteria

Twelve conditions, listed in full at the end of `REMEDIATION_PLAN.md`. When they hold, `release_blocked` comes off.

---

## Maintenance

- These documents are **authored**, not generated. Update them deliberately.
- `remediation_tasks.json` and `REMEDIATION_PLAN.md` describe the same 44 tasks. **Changing one without the other is a defect.**
- Superseded documents get a header marking them as such — they are not silently deleted or quietly edited to look correct in hindsight. That practice is what the program exists to correct.
