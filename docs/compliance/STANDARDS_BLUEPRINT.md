# UKG DataLogicEngine — Standards & Compliance Blueprint

**Prepared for:** Kevin Herrera
**Date:** August 17, 2026 *(rev. 3 — EU market excluded per Kevin, 2026-08-18)*
**Scope:** DataLogicEngine v4.4.0 (`release_blocked`), UKG/USKD platform
**Deployment model:** Installed software on a workstation, server, or VM. Single outbound flow to the LLM provider. Local API surface to client software. Air-gap capable against a local model. No license check-in, no telemetry, no phone-home.
**Target markets:** US federal / public sector (weighted first) and regulated industry (health/finance). **US only — the product is not being placed on the EU market.**

---

## 0. Read this part first

### 0.1 The deployment model changes almost everything

DataLogicEngine is not a cloud service. It is installed software that runs inside the customer's boundary, makes exactly one class of outbound connection (to a model endpoint the customer configures), and exposes a local API to client software. It can run air-gapped against a self-hosted model.

That single set of facts eliminates more compliance obligation than any control you could build:

| | Applies to you |
|---|---|
| **FedRAMP** (any flavor, including 20x) | **No.** FedRAMP authorizes cloud service offerings. You are not one. |
| **SOC 2 Type I / II** | **Essentially no.** SOC 2 reports on a *service organization's* system. You operate no system on the customer's behalf and hold none of their data. |
| Multi-tenant isolation controls | No. There is no tenancy. |
| Continuous monitoring / ConMon reporting | No. |
| Business Associate Agreement under HIPAA | **Probably no** — see §3.2. This is worth a great deal of money. |
| Data residency / cross-border transfer obligations | Only for the one outbound flow, and air-gap mode removes even that |
| Breach notification as a data controller/processor | No customer data in your custody to breach |
| **EU Cyber Resilience Act / EU AI Act / GDPR / NIS2 / DORA** | **No — decision recorded August 18, 2026: the product is not placed on the EU market.** See §6. |
| Product-level secure development, signing, SBOM, CVD, support period | **Yes, and these become the whole game** |

The mental model to hold: **you are a software manufacturer, not a service provider.** Your compliance obligations look like Cisco's or Splunk's, not Salesforce's. Nearly every framework in the previous revision of this document was written for service providers, and I pointed you at the wrong half of the map.

### 0.2 Your actual compliance surface is one arrow

Everything DataLogicEngine does happens inside a boundary the customer already owns, secures, monitors, and has accredited — except one outbound connection to a model endpoint.

That means every security questionnaire, every ATO package, every HIPAA risk analysis, and every AI governance review reduces to four questions:

1. **What leaves the machine?** (prompt content, and nothing else)
2. **Where does it go?** (an endpoint the customer configures — including, optionally, one on their own hardware)
3. **Can the customer see, control, and stop it?** (audit log, allowlist, kill switch)
4. **Can you *prove* items 1–3 rather than assert them?**

Item 4 is the entire job. It is also a testable engineering property, not a paperwork exercise, which is unusually good news. See §2.1.

### 0.3 The document problem that hasn't gone away

Two documents in this project disagree, and it still matters.

The **UKG Enterprise Standards Assessment** (Jan 15, 2026) scores the system at *86% — Enterprise Ready*, with AI Application Standards at *98%*, and marks "Evaluation suites — Confidence calibration (Brier)" as **✓ COVERED**. The **External Code Review** (Aug 16, 2026) searched the tree for `brier`, `ECE`, `calibration_error`, and `expected_calibration_error` and found **zero hits**.

Under a service-provider framework this would be an audit finding. Under a *product* framework it is worse, because product claims are **marketing claims about a good placed on the market**, which puts them squarely under **FTC Act Section 5** (deceptive practices), ordinary misrepresentation and contract law, and — for federal sales — the **False Claims Act**, where a knowingly false capability representation on a government contract is a category of exposure with treble damages attached. A false statement in a design document is an internal problem. The same statement in a datasheet a buyer relies on is a different category of exposure.

**Retitle or supersede that assessment as target-state.** Fifteen minutes, no downside, meaningful upside.

---

## 1. What replaces the frameworks that no longer apply

Here is the substitution table, because buyers will ask for the wrong things and you need a prepared answer.

| They'll ask for | You say | What you actually provide |
|---|---|---|
| "Send us your SOC 2" | "SOC 2 reports on a hosted service. We're installed software in your environment — we operate nothing and hold none of your data. Here's the equivalent product security package." | Product Security Whitepaper + SBOM + signed artifacts + pen test report + SSDF mapping + secure config guide |
| "Are you FedRAMP authorized?" | "FedRAMP authorizes cloud service offerings. We deploy inside your existing accreditation boundary. Here's our control-inheritance matrix for your ATO." | Customer Responsibility Matrix mapped to NIST 800-53 Rev 5 + STIG-aligned hardening guide + FIPS crypto statement |
| "We need a BAA" | "We never receive, create, maintain, or transmit PHI. Your data never reaches us. The only egress is to the model endpoint *you* configure — and you can point that at your own hardware." | Data flow diagram + egress attestation + air-gap deployment guide |
| "What's your uptime SLA?" | "You control availability; it runs on your infrastructure." | Support/maintenance terms + a declared security update support period (no longer a CRA duty, but buyers ask and federal ATOs need it) |
| "Where is our data stored?" | "On your machine. We have no copy." | Data handling statement + retention/deletion procedure for local artifacts |

**Build the "Product Security Package" as one deliverable.** It is roughly 30 pages, it answers 90% of enterprise security questionnaires without a call, and it costs a fraction of a SOC 2. This is the highest-ROI compliance artifact available to you and it does not exist yet.

### What's still worth certifying

| Certification | Verdict | Why |
|---|---|---|
| **ISO/IEC 27001:2022** | **Yes — narrow scope** | Scope it to your development environment, source control, and build/release pipeline. That's the only thing you actually operate. Buyers accept it as the SOC 2 substitute, it's cheaper at this scope, and it's the international-facing credential. ~$15k–$30k at small scope. |
| **ISO/IEC 42001:2023 (AIMS)** | **Yes — highest value** | Applies cleanly to a product manufacturer. It is the certification that makes UKG legible as what it is, almost nobody in your space has it, and the accredited CB ecosystem matured with ISO/IEC 42006:2025. This is your differentiator. |
| **SOC 2 Type II** | **No, unless you later add a hosted control plane** | Nothing to audit. Revisit only if you introduce licensing/telemetry infrastructure. |
| **FedRAMP** | **No. Not applicable.** | Delete it from the roadmap entirely. |
| **HITRUST** | **Probably not** | Designed for entities handling PHI. If you're not a BA, it's a certification for a risk you don't carry. |
| **Common Criteria / NIAP** | **Later, and only if DoD demands it** | The classic route for on-prem software into DoD. Expensive (6–18 months, six figures) and only worth it against a specific committed opportunity. Know it exists; don't start it. |
| **CMMC Level 2** | **Yes, if you handle CUI** | Applies to *you as a contractor*, not to the product. See §4.3. |

---

## 2. The engineering requirements, reordered for a product company

### 2.1 Egress proof — your single most valuable control

You have made a strong claim: the only outbound connection is to the LLM provider. **Make it a tested, evidenced property rather than a sentence in a datasheet.** Nothing else you build will close deals as efficiently.

Concretely:

- **An egress allowlist enforced in code**, not just by configuration — a single chokepoint through which all outbound HTTP must pass, denying by default, with the model endpoint as the only entry.
- **A CI test that asserts it.** Run the full governed execution path under a network monitor (or a deny-all sandbox with a logging proxy) and fail the build on any connection to a host not in the allowlist. This is a day of work and it produces a *renewable, dated artifact* — the strongest kind of evidence in any framework.
- **A customer-visible egress log.** Every outbound call, with destination, byte count, and timestamp, in the existing hash-chained audit log. This converts "trust us" into "verify us," which is your product's entire thesis applied to itself.
- **A hard offline/air-gap mode** with an explicit setting, verified by the same test with the allowlist empty.
- **A published data flow diagram** showing precisely what fields of a prompt leave the machine.

> **Framework value:** this one bundle satisfies HIPAA §164.308(a)(1)(ii)(A) risk analysis inputs, HIPAA §164.312(e) transmission security, NIST 800-53 **SC-7** (boundary protection) and **AC-4** (information flow enforcement) for the customer's ATO, NIST 800-171 Rev 3 boundary controls if CUI is in play, and the data-flow disclosure every enterprise security questionnaire asks for. Four frameworks and every questionnaire, from one engineering artifact.

### 2.2 The local API is now your primary attack surface

With no cloud service, the "api link out to the client software" is where an attacker meets your product. It is a localhost (or LAN) listener running with the user's privileges on a workstation, server, or VM.

Required:

- **Bind to loopback by default.** `0.0.0.0` must be an explicit, documented, warned-about opt-in. Verify this — it is the single most common finding in on-prem software pen tests.
- **Authenticate every request**, including from localhost. Localhost is not a trust boundary on a multi-user server or a VM with other tenants' workloads.
- **Origin/CSRF enforcement** on any browser-reachable endpoint. You have tests for this.
- **No anonymous mutations.** You have tests for this too — across 18 endpoints including `/api/v1/truth/gate/evaluate` and `/graphql`.
- **Error normalization** so internal state doesn't leak. Also tested.

**And here is the sharp point:** those three test files — `test_session_security.py`, `test_phase1_anonymous_mutations.py`, `test_phase1_public_error_sentinels.py` — are among the **40 tests that error out at setup on Windows** and therefore have never run on the platform you ship to. In the SaaS framing that was an audit-evidence problem. In the product framing it is worse: **it is the security test suite for your only remotely-reachable interface, unexecuted on your only shipping target.**

Root cause is one line — `tests/conftest.py:150` unlinks a shared SQLite file that an undisposed SQLAlchemy engine still holds, and Windows won't allow it. Fix: `engine.dispose()` in fixture teardown, unique temp DB path per test, Windows CI runner that fails the build on errors as well as failures.

**This is the highest-priority item in this document.** One day of work.

### 2.3 Supply chain — for a manufacturer, this *is* the trust relationship

When you ship code into a customer's accredited environment, your build pipeline is the thing they are trusting. This section moved from "largest formal gap" to "the core of your security story."

Required, in build order:

- **Reproducible or at minimum hermetic builds** — pinned toolchain, committed lockfile, no network at build time
- **SBOM per build** — CycloneDX 1.6 via `cdxgen`/`syft`, attached to every release artifact. *Requested at agency discretion under OMB M-26-05's risk-based regime; expected in enterprise diligence.*
- **Dependency/CVE scanning** — `pip-audit`, Trivy, or Grype with a documented severity policy and reachability triage
- **SAST** — Semgrep or CodeQL as a required PR check
- **Secret scanning** — `gitleaks` pre-commit and CI (your hygiene is already clean; this keeps it evidenced)
- **Authenticode EV code signing on the Windows installer.** Not optional. SmartScreen reputation is a hard distribution blocker before it is ever a compliance one.
- **Sigstore/cosign + in-toto/SLSA provenance attestations.** Target **SLSA Build Level 3.**
- **Secure update mechanism** — signed updates, rollback protection, and ideally TUF-style metadata. You have no auto-update phone-home, which is a privacy win; it means update *distribution* integrity matters more, not less.
- **License compliance scan** — matters more than expected in federal prime diligence

### 2.4 Secure configuration and hardening — a product deliverable, not internal ops

Because the customer runs it, the hardening guide is something you *ship*:

- **CIS Benchmarks and DISA STIG–aligned configuration guide** for Windows Server / Windows 11 targets
- **Least-privilege installation** — document the exact service account rights required, and do not require local admin at runtime
- **Windows ACL and DPAPI scoping** for credentials at rest, with the scope (user vs. machine) documented and justified
- **Firewall rules** the customer should apply, including the outbound allowlist
- **Uninstall/decommission procedure** including artifact and log disposition

### 2.5 Code quality gates that should be mandatory PR checks

- `ruff` (lint + format) — zero-warning policy
- `mypy --strict` on `backend/` and `sdk/`, with a documented shrinking allowlist for legacy paths
- Coverage floor enforced in CI (you're at a healthy ~1:2.8 test-to-source ratio — set the floor at current and ratchet)
- Mutation testing (`mutmut`) on the governed execution path and truth engine — for a product whose *value proposition is verification*, mutation score is what proves the tests mean something
- Branch protection: no direct pushes to `main`, required status checks, signed commits
- **Resolve the 91 uncommitted working-tree changes** — evidence artifacts referencing commit state are worthless if the tree doesn't match
- **Archive `core/simulation/`.** 1,444 lines whose three constructor imports reference `backend.knowledge_algorithm` (singular — a package that does not exist), so `axis_mapper`, `truth_engine`, and `workflow_loader` are permanently `None`, and three active test files still import it. Audit all 19 `# inversion:ok` suppressions while you're in there — an inline annotation asserting "intentional and safe" reads to any assessor as a compensating-control claim, and at least three of them currently document a permanently broken import as design intent.

---

## 3. Regulated industry — health and finance

### 3.1 The general shape

Because you hold no customer data, you are not the regulated entity. Your customer is. Your job is to be **deployable inside their compliance program without breaking it**, and to hand them the artifacts that let them prove it.

That reframes everything: you are not seeking HIPAA compliance. You are building a **HIPAA-deployable product**.

### 3.2 HIPAA — you are probably not a Business Associate, and that is worth real money

Under 45 CFR §160.103, a Business Associate is one who **creates, receives, maintains, or transmits PHI on behalf of a covered entity**. If DataLogicEngine runs entirely on the customer's machine and you never receive PHI, you are not a BA. The relevant analogue is the "software vendor" position — a company selling installed software that a covered entity uses to process PHI is generally not a BA, whereas one that hosts or supports with PHI access is.

**Three things can destroy this position. Guard all three:**

1. **The LLM egress.** If PHI goes into a prompt to a third-party model API, that transmission is a disclosure. It is the *customer's* disclosure, not yours — but it only works if (a) the customer has a BAA with the model provider (Azure OpenAI, AWS Bedrock, and Anthropic all offer them), or (b) the model runs on the customer's own hardware. **Your obligation is to make both configurations first-class, documented, and tested.** Air-gap mode is not a feature here, it is the compliance argument.
2. **Support access.** The moment a support engineer screen-shares into a session showing PHI, or receives a diagnostic bundle containing it, you are handling PHI. Build **PHI-safe diagnostics**: log bundles that scrub content by default, with the existing Presidio redaction on the export path. Write the support policy before the first support incident, not after.
3. **Any future telemetry.** You have none today. If you ever add it, the design constraint is metadata-only, and it should be written down now while it's easy.

**Deliverable:** a two-page *HIPAA Deployment Guide* covering the BA analysis, the model-endpoint decision tree, the PHI-safe diagnostics policy, and a mapping of which §164.312 technical safeguards the product supports (access control, audit controls, integrity, transmission security) versus which the customer must supply. Customers' privacy officers will use this document directly, which makes it a sales asset.

The **HIPAA Security Rule overhaul is delayed to July 2027** (OMB extended it a year from May 2026). Proposed requirements include mandatory MFA, mandatory encryption at rest and in transit, network segmentation, asset inventory and network mapping, annual penetration tests, vulnerability scans every 6 months, and annual compliance audits — and it removes the "addressable vs. required" flexibility most HIPAA programs lean on. **Design to the proposed rule now**, because your customers will need the product to support these controls, and "supports the 2027 Security Rule" will be a differentiator in 2027.

### 3.3 Finance

- **SR 11-7 / OCC 2011-12 model risk management** is the framework that will interrogate your confidence score hardest. It requires independent validation, ongoing monitoring, and outcomes analysis. A bank's model risk team will ask what `0.995` means and will not accept "most sub-checks returned pass." See §5.
- **SEC 17a-4 / FINRA 4511** record retention: your SHA-512 hash-chained, append-only audit log is genuinely well positioned for WORM-equivalence. Verify the chain is **verified on read by production code**, not merely written — an unverified chain is a data structure, not a control.
- **NYDFS 23 NYCRR 500** applies to the customer; support their MFA and 72-hour incident reporting obligations. (DORA is out of scope with the EU market decision.)
- **PCI DSS**: stay out of scope entirely. Never touch cardholder data.

---

## 4. Federal / public sector — the path that actually exists

### 4.1 Delete FedRAMP from the plan

FedRAMP authorizes cloud service offerings. Installed software running inside an agency's existing accreditation boundary is not one. The FedRAMP 20x consolidated rules that launched in 2026 are real and significant — and irrelevant to you.

**What replaces it:** the agency does the ATO under FISMA/NIST 800-53 Rev 5, and your product is a component inside their boundary. Your job is to make their ATO cheap. That is a documentation exercise, not a certification, and it is enormously less expensive.

### 4.2 The federal artifact set

| Artifact | Why |
|---|---|
| **Customer Responsibility Matrix** mapped to NIST 800-53 Rev 5 | The single most valuable federal document you can write. For each relevant control: what the product provides, what the agency must supply, what is shared. Assessors love it because it saves them weeks. |
| **NIST SSDF (SP 800-218 v1.1) mapping** | Practice-by-practice, what you do and where the evidence lives. **Status note:** OMB **M-26-05** (January 23, 2026) rescinded M-22-18 and M-23-16, ending the government-wide mandatory CISA "Common Form" self-attestation and replacing it with agency-level, risk-based validation. Agencies retain discretion to require attestations and SBOMs. Practically: the uniform gate is gone, agency-specific demands replaced it, and SSDF + SBOM remain the currency. **Have the artifacts ready on request rather than a form on file.** |
| **NIST SP 800-218A mapping** | The SSDF Community Profile for generative AI and dual-use foundation models. Directly applicable and few competitors will have it. |
| **FIPS 140-3 crypto statement** | **Specific finding:** your `EncryptionManager` uses `AESGCM` from Python's `cryptography`. AES-256-GCM is a FIPS-*approved algorithm*, but the default build is **not a FIPS-validated module**. For federal deployment you need a validated module — FIPS-mode OpenSSL, Windows CNG in FIPS mode, or a validated HSM. Same question applies to **Windows DPAPI** for your specific usage. Resolve before claiming FIPS anywhere. |
| **DISA STIG / SRG–aligned hardening guide** | Required in practice for DoD deployment |
| **SBOM (CycloneDX 1.6)** | Requested at agency discretion under M-26-05; assume it will be requested |
| **Section 508 / WCAG 2.2 AA conformance (ACR/VPAT)** | Mandatory for federal procurement of anything with a UI. Routinely forgotten until it blocks a deal at the last minute. |
| **Supply chain risk statement** | FASCSA / Section 889 / prohibited-vendor declarations |
| **Air-gap deployment guide** | For classified and high-side environments this is the difference between deployable and not. Your strongest federal feature. |

### 4.3 CMMC — applies to you, not to the product

If you handle CUI as a DoD contractor or subcontractor, **CMMC applies to your company**. The 48 CFR rule took effect **November 10, 2025**; the program is in **Phase 1**. On **July 13, 2026 the Department of War paused the Phase 2 transition** for a 60-day review — during the pause only **Level 1 (Self)** and **Level 2 (Self)** can be designated in new solicitations, and Level 2 C3PAO assessment requirements are temporarily removed. Further guidance was expected around mid-September 2026.

**Level 2 = all 110 NIST SP 800-171 requirements**, self-assessed every three years with annual senior-official affirmation.

Given your background and the current pause, **the Level 2 self-assessment window is genuinely favorable right now.** It is the most natural federal entry point available to you and it does not require a third-party assessor at this moment. Watch for the mid-September guidance.

### 4.4 Common Criteria / NIAP

The traditional route for on-prem software into DoD at higher assurance. Six to eighteen months, six figures, against a specific Protection Profile. **Do not start this speculatively.** Know it exists, mention it as a roadmap item if a DoD opportunity demands it, and price it into that specific deal.

---

## 5. AI-specific standards — where you can lead

### 5.1 The frameworks

| Standard | Applicability to a product manufacturer |
|---|---|
| **ISO/IEC 42001:2023 (AIMS)** | Applies cleanly. An AI management system: AI policy, roles, risk assessment, impact assessment, lifecycle controls, performance evaluation, continual improvement. **Your best-value certification.** |
| **ISO/IEC 42005** | AI system impact assessment — the artifact ISO 42001 cl. 6.1.4 points at |
| **ISO/IEC 23894** | AI risk management guidance (ISO 31000 adapted for AI) |
| **NIST AI RMF 1.0** + **NIST AI 600-1** (Generative AI Profile) | Govern / Map / Measure / Manage. The GenAI Profile adds 12 risk categories including confabulation and information integrity. Voluntary, but it is the common language of US enterprise AI procurement — and federal agencies use it in their own risk assessments of AI you deploy into their boundary. |
| **OWASP GenAI LLM Top 10 (2026)** | LLM01 Prompt Injection · LLM02 Sensitive Info Disclosure · LLM03 Excessive Agency · LLM04 Data & Model Poisoning · LLM05 Improper Supply Chain · LLM06 Insecure Output Handling · LLM07 Vector & Memory Flaws · LLM08 Misinformation · LLM09 Hidden Context Exposure · LLM10 Unbounded Consumption |
| **OWASP Top 10 for Agentic Applications (2026)** | Goal manipulation, tool misuse, identity/privilege abuse, cascading multi-agent failures, memory poisoning. Directly applicable to the Quad Persona system and MCP integration. |
| **MITRE ATLAS** | The ATT&CK equivalent for AI. Use as the threat-modeling frame. |
| **Model card / system card** | Documented intended use, limitations, evaluation results. **Under a product regime this is not optional documentation — it is the datasheet, and it is what your accuracy claims are legally measured against.** |

### 5.2 Your genuine assets

**The KA `limitations` pattern.** KAs returning explicit statements of what they did *not* establish — `"Token-distribution entropy does not measure truth, knowledge decay, or overall system health and cannot trigger reconciliation."` — is a code-level implementation of what **ISO 42001 Annex A.8.2** (system documentation and information for users), **NIST AI RMF GOVERN 4.2 / MAP 3.4**, and — newly relevant — the **Colorado ADMTA** developer-documentation duty (known risks and limitations, instructions for meaningful human oversight) ask for in prose. Most vendors write this in a PDF nobody reads; you compute it per invocation. Formalize it into the API response contract and the system card. This is a differentiator, not a detail.

**The hash-chained audit log.** SHA-512 chaining over `(previous_hash + entry)` with 7-year retention gives you HIPAA §164.312(b) (audit controls), SEC 17a-4 / FINRA 4511 WORM-equivalence, NIST 800-53 **AU-9** (protection of audit information) for the customer's ATO, and the Colorado ADMTA three-year record-retention duty, essentially for free. Add egress events to it (§2.1) and it becomes the customer's proof of your egress claim as well.

**Typed governed execution** with fail-closed re-entrancy guards, deadline clamping to [5,300]s, a cancellation registry, and an explicit failure taxonomy. This is precisely what the Agentic Top 10 asks for against goal manipulation and unbounded consumption. Document it as a security control, not just as architecture.

### 5.3 Your genuine exposure

**LLM08 Misinformation is your product's core risk and you have no measurement for it.** `hallucination_rate` exists as a key in a `METRIC_DEFINITIONS` dict in `truth_memory/metrics.py`; no code computes it. OWASP moved Misinformation up the 2026 list specifically because confidently-wrong AI output now triggers automated business workflows — which is exactly the pattern DataLogicEngine enables.

**The confidence score.** `C = 0.35·evidence_quality + 0.30·ka_consensus + 0.20·persona_agreement + 0.15·gate_factor`, with `0.5` returned on every failure path, the whole body wrapped in `except Exception: return 0.5`, and `0.995` hard-wired as the healthcare/finance/legal/safety threshold across `trust_validation_gateway.py`, `opa_policy.py`, and a dozen other sites.

> Under the SaaS framing this was a certification problem. **Under the product framing it is a product-claims problem**, and that is a harder category. ISO 42001 **cl. 9.1** requires performance evaluation against defined criteria. NIST AI RMF **MEASURE 2.x** requires trustworthiness characteristics to be measured, not asserted. **SR 11-7** requires independent validation and outcomes analysis before a bank may rely on a model. The **Colorado ADMTA** requires developers to document known risks and limitations. And — with no EU regime in play, this becomes the sharpest one — a numeric accuracy figure in product documentation is a representation to the buyer, reachable under **FTC Act Section 5** and ordinary contract and misrepresentation law.
>
> **Do this week (free):** rename it — `governance_score`, `check_pass_ratio`, anything non-probabilistic — and stop swallowing exceptions so failures propagate as failures instead of as 0.5.
> **Do this quarter:** build a labeled held-out evaluation set, measure ECE, publish a reliability diagram.
> **Do after that, if ever:** implement the spec'd formula (sigmoid, conflict penalty, entropy term) — only once you can prove it is better than what it replaces.

**LLM07 Vector and Memory Flaws.** TruthMemory and the nested memory architecture are persistent state influencing future outputs. On a shared server or VM this is also a *multi-user* concern — one user's poisoned memory affecting another's results. No listed control.

**LLM09 Hidden Context Exposure.** Ten layers, quad personas, and MCP tool calls mean context assembled at one layer can surface at another. Needs an explicit context-flow threat model.

**MCP as an unmanaged supply chain.** Each MCP server is an untrusted tool surface with its own identity, permissions, and dependencies — and in the installed model, **each one is a potential second egress path that breaks your "one outbound flow" claim.** Schema allowlists are necessary and insufficient. Add per-server capability scoping, tool-call rate limits, human-in-the-loop gates for state-changing tools, MCP servers in the SBOM and third-party register, and **MCP endpoints in the egress allowlist test.**

**The 20-KA concentration.** 203 KA modules, 213 canonical capabilities, ~211 marked "production-enabled" in the manifest — and the live L1–L10 default path touches roughly 20. As a product claim, "211 production-enabled" needs a different word.

---

## 6. The US regulatory surface — what replaces the EU chapter

**Decision recorded August 18, 2026: DataLogicEngine is not being placed on the EU market.** The EU Cyber Resilience Act, EU AI Act, GDPR, NIS2, and DORA are all out of scope. That decision should be written into the product documentation and the sales playbook, because it is the answer to a question EU-headquartered prospects will eventually ask, and because "we deliberately scoped to US only" is a defensible position while "we hadn't thought about it" is not.

**The first-order consequence is that you now have no hard external compliance deadline at all.** The September 11 CRA reporting date is gone. The December 2, 2027 EU AI Act date is gone. Nothing left on this list points a gun at you.

That is worth sitting with, because it changes *why* the work in this document gets done. It is no longer "a regulator requires it by date X." It is now entirely **commercial**: a buyer will ask, a deal will stall, an ATO will take four months instead of six weeks. That is a weaker forcing function and a better reason — the work should be sequenced by which deal you are chasing, not by a calendar.

### 6.1 What genuinely still has dates

| | Status |
|---|---|
| **HIPAA Security Rule overhaul** | Final rule now expected **July 2027** (OMB extended it a year from May 2026). Mandatory MFA, mandatory encryption at rest and in transit, network segmentation, asset inventory and network map, annual penetration tests, vulnerability scans every 6 months, annual compliance audits — and it removes the "addressable vs. required" flexibility. **This lands on your customers, not you** — but they will need the product to support these controls, and "supports the 2027 Security Rule" is a differentiator you can start claiming truthfully in 2027. |
| **CMMC** | 48 CFR effective **November 10, 2025**; program in **Phase 1**. DoW paused the Phase 2 transition on **July 13, 2026** for a 60-day review — during the pause only Level 1 (Self) and Level 2 (Self) may be designated in new solicitations, and Level 2 C3PAO requirements are temporarily lifted. Guidance expected around **mid-September 2026**. Applies to *you as a contractor* if you handle CUI. **The self-assessment window is genuinely favorable right now.** |
| **Colorado ADMTA** | Effective **January 1, 2027**, contingent on AG rulemaking. See §6.2 — this is the one new obligation that actually reaches you. |
| **CIRCIA** | CISA's final rule slipped from October 2025 to an expected **May 2026**, and as of mid-2026 reporting suggests it is still pending finalization. When effective: **72 hours** to report a covered cyber incident, **24 hours** to report a ransom payment, for covered entities across the 16 critical infrastructure sectors. This mostly lands on your *customers*; watch it in case a hosted component or a CI-sector customer relationship pulls you in. |

### 6.2 Colorado ADMTA — the EU AI Act's obligations, returning in US form

This is the item to actually pay attention to, because it does something interesting: it imposes on you, as a *developer*, roughly the documentation duties EU AI Act Article 13 would have — and your architecture is unusually well positioned for it.

Colorado **repealed and replaced** the Colorado AI Act on **May 14, 2026**, substituting the **Automated Decision-Making Technology Act (ADMTA)** after industry opposition and federal pressure. The replacement drops the algorithmic-discrimination framing and emphasizes transparency instead.

**Scope:** automated decision-making technology that *materially influences* consequential decisions in seven domains — education, employment, housing, lending, insurance, **healthcare**, and government benefits. Two of your three target verticals sit inside that list.

**Developer obligations** — provide deployers with:

- documentation of intended use, known risks, and **limitations**
- categories of personal data used in training
- instructions for meaningful human oversight
- notice of material system updates
- record retention for a minimum of three years

**Read that list against what you already have.** The KA `limitations` pattern computes per-invocation statements of what a capability did *not* establish. The hash-chained audit log with 7-year retention covers the retention duty three times over. The system card generated in CR-F5 is the intended-use-and-limitations document. The governed execution path with its explicit failure taxonomy is the human-oversight substrate.

You are closer to compliant with the ADMTA than almost any vendor in your space will be, and you got there by engineering instinct rather than by reading the statute. **That is a marketing position, not just a compliance one** — and it is the single strongest argument for finishing CR-F5 (system card generated from code) rather than treating it as documentation cleanup.

### 6.3 The rest of the state patchwork, and why not to chase it

- **Texas RAIGA** (effective January 1, 2026) covers developers and deployers doing business in Texas. It prohibits *intentional* creation or use of AI for restricted purposes — encouraging harm, violating constitutional rights, unlawful discrimination. The intent standard makes it hard to trip accidentally. The Texas AG can issue civil investigative demands requiring detailed system information, so be able to produce your documentation on request.
- **California** (January 1, 2026): the Transparency in Frontier AI Act applies to frontier developers above 10^26 training FLOPs and $500M revenue — **not you**. But the same tranche includes training-data transparency disclosures, AI content detection, **healthcare provider disclaimers**, and companion-chatbot warnings. The healthcare disclaimer provision is the one to check against any clinical-adjacent deployment.
- **Federal preemption is in play and unresolved.** The **December 11, 2025 executive order, "Ensuring a National Policy Framework for Artificial Intelligence,"** does not preempt state law directly. It directs the Attorney General to stand up an AI Litigation Task Force to challenge state laws as inconsistent with federal policy, required Commerce to identify burdensome state laws by March 11, 2026, tasked the FTC with clarifying when state requirements "alter truthful outputs," and conditions certain federal broadband funding on states avoiding "onerous" AI regulation. Child safety, infrastructure, and procurement rules are carved out. **Enforceability depends on litigation not yet resolved.**

**The practical instruction: do not build to any individual state statute.** They are being written, repealed, replaced, and challenged faster than an engineering roadmap can track — Colorado repealed its own flagship law fourteen months after passing it. Build to the **common denominator** all of them share, which is also what ISO 42001 and NIST AI RMF already require:

1. documented intended use and out-of-scope use
2. documented known limitations, measured rather than asserted
3. training and data provenance disclosure
4. meaningful human oversight, implemented and instructed
5. change notification
6. records retained

Every one of those is an output of Phases D, F, and G. Build them once; satisfy the patchwork by construction.

### 6.4 Incident reporting — the US replacement for the CRA runbook

The CRA's 24h/72h ENISA obligation is gone, but a US-market product still needs an incident reporting posture:

- **DFARS 252.204-7012** — 72-hour reporting to DoD if you handle covered defense information as a contractor. Applies to *you*, and given your background this is the likeliest one to bite first.
- **CIRCIA** — 72h incident / 24h ransom payment when the final rule lands, for covered entities in the 16 CI sectors.
- **Customer contractual notification** — enterprise and government contracts routinely impose their own windows, often tighter than statute. This is the one that will actually govern you.
- **State breach notification law** — 50 states, but largely moot: you hold no customer data.

**A coordinated vulnerability disclosure policy is still worth writing**, just no longer on a September deadline. ISO/IEC 29147 and 30111 remain the template, federal procurement increasingly expects a published CVD process, and it costs two pages plus a `security.txt`. Reclassify it from urgent to routine — do not delete it.

---

## 7. Subsystem → control map

| Subsystem | Provides (with evidence) | Missing | Maps to |
|---|---|---|---|
| Egress path to LLM provider | Single configurable endpoint | **Enforced allowlist, CI egress test, customer-visible egress log, verified air-gap mode** (§2.1) | NIST 800-53 SC-7/AC-4; NIST 800-171 r3; HIPAA §164.312(e) |
| Local API to client software | CSRF, origin checks, desktop-auth precedence, anonymous-mutation denial — **all tested** | **Those tests don't execute on Windows** (§2.2); loopback-default verification | OWASP ASVS 5.0 L2; NIST 800-53 AC-3/SC-8 |
| `governed_execution/orchestrator.py` | Typed contracts, fail-closed re-entrancy, deadline clamp, cancellation registry, failure taxonomy | Documented as a security control; formal threat model | OWASP Agentic T-01/T-05; ISO 27001 A.8.28 |
| Hash-chained audit log | SHA-512 chain, 7yr retention, tamper-evident | Chain *verification on read*; egress events; auditor export tooling | NIST 800-53 AU-9; HIPAA §164.312(b); SEC 17a-4; CO ADMTA retention |
| `EncryptionManager` | Real AES-256-GCM, 12-byte nonce, envelope design | **FIPS 140-3 validated module** (§4.2); key rotation evidence | FIPS 140-3; HIPAA §164.312(a)(2)(iv); ISO 27001 A.8.24 |
| DPAPI secret storage | Secrets at rest, tests exist | Tests don't execute; FIPS validation status for this usage unverified | NIST 800-53 IA-5; ISO 27001 A.8.24 |
| `confidence_calculator.py` | Deterministic, documented weights | **Calibration, honest failure modes, conflict and entropy terms** | ISO 42001 cl. 9.1; NIST AI RMF MEASURE; SR 11-7; FTC Act §5 |
| KA registry + `limitations` | Explicit non-claims per capability | Aggregate into a system card; reconcile "211 production-enabled" with ~20 live | ISO 42001 A.8.2; CO ADMTA developer duties; NIST AI RMF MAP 3.4 |
| KA-61 + Llama Guard 3 + Rebuff | Prompt injection defense, multi-layer | Red-team evidence; no coverage of LLM07/08/09 | OWASP GenAI 2026 LLM01/02 |
| Presidio PII redaction | Pre/post-model filtering, log masking | Effectiveness measurement; **apply to support diagnostic bundles** (§3.2) | HIPAA §164.514 de-identification; CCPA/CPRA; state privacy law |
| MCP integration | Schema allowlists, authz checks | Per-server scoping, HITL gates, SBOM inclusion, **egress-allowlist coverage** | OWASP Agentic; SSDF PW.4 |
| `core/simulation/` | — | Archive it (§2.5) | ISO 27001 A.8.9; SSDF PW.4 |
| Build pipeline | Docker, pinned deps | **SBOM, EV signing, SLSA provenance, SAST/SCA, Windows CI** (§2.3) | SLSA L3; SSDF PS.1–3; agency SBOM requests |
| Installer / update path | — | Signed installer, signed updates, rollback protection, hardening guide | NIST 800-53 SI-2/CM-14; SLSA L3 |

---

## 8. Revised roadmap

### Phase 0 — Make the claims true (now → October 2026)

Roughly two weeks of engineering. Everything else depends on it.

1. **Fix the Windows conftest leak**; Windows CI runner failing on errors — *1 day, highest value in this document*
2. **Build the egress allowlist + CI egress test + air-gap mode verification** — *2–3 days, your single most valuable control*
3. **Rename the confidence score; stop swallowing exceptions** — *1 day*
4. **Verify loopback-default binding** on the local API — *hours*
5. Retitle/supersede the January assessment as target-state — *15 minutes*
6. Archive `core/simulation/`; audit all 19 `# inversion:ok` suppressions — *2–3 days*
7. Commit the working tree
8. **Record the US-only market decision** in the product documentation and sales playbook. Then write the CVD policy (ISO 29147/30111) + `security.txt` + named security contact at routine priority — no longer on a CRA clock, but federal procurement expects a published disclosure process
9. SBOM + SAST + SCA + secret scanning in CI; **Authenticode EV signing on the installer**

### Phase 1 — The Product Security Package (Q4 2026)

10. Write it as one deliverable (§1): product security whitepaper, data flow diagram, egress attestation, SSDF + 800-218A mapping, SBOM, secure configuration/hardening guide, CVD policy, support & PHI-safe diagnostics policy, declared security update support period
11. **Customer Responsibility Matrix** against NIST 800-53 Rev 5
12. **HIPAA Deployment Guide** with the BA analysis and model-endpoint decision tree (§3.2)
13. First third-party penetration test against the local API surface — the report is a sales asset
14. Section 508 / WCAG 2.2 AA conformance report (ACR/VPAT) if federal is on the horizon
15. Incident response plan with AI-specific playbooks: prompt injection, model provider outage, confabulated-output-caused-harm, context leak

### Phase 2 — The quality benchmark (Q4 2026 → Q1 2027)

16. **Build one external quality benchmark and publish the results.** Labeled held-out eval set, ECE, reliability diagram, and a measured hallucination rate. This single piece of work is simultaneously the calibration fix, the NIST AI RMF MEASURE evidence, the SR 11-7 validation input, the Colorado ADMTA limitations disclosure, the system card content, and the only item on this entire roadmap a *buyer* would notice.

### Phase 3 — Certifications, exactly two (2027)

17. **ISO/IEC 27001:2022**, scoped narrowly to your dev environment, source control, and build pipeline
18. **ISO/IEC 42001:2023 (AIMS)** — with ISO 42005 impact assessment and a published system card. This is the differentiator.
19. SLSA Build Level 3

### Phase 4 — Market-specific, on demand (2027 → 2028)

20. **Federal:** CMMC Level 2 self-assessment (watch the mid-September 2026 guidance), FIPS 140-3 validated crypto, STIG hardening guide, air-gap deployment guide, DFARS 252.204-7012 incident reporting posture. Common Criteria/NIAP **only against a committed opportunity.**
21. **Health/finance:** HIPAA Security Rule 2027-aligned control support, SR 11-7 model validation package
22. **State AI law:** Colorado ADMTA developer documentation package by **January 1, 2027** — which, if CR-F5 lands, you get essentially for free (§6.2)

---

## 9. What I'd actually say to you

Two corrections in two days removed most of this document's original content. The installed-software model took out FedRAMP, SOC 2, HITRUST, multi-tenancy, ConMon, data residency, and breach notification. The US-only decision took out the Cyber Resilience Act, the EU AI Act, GDPR, NIS2, and DORA. Between them, that is on the order of two years and several hundred thousand dollars of compliance work you are not doing.

**And with the EU gone, you have no hard external deadline left.** Nothing on the remaining list has a date that binds you. The HIPAA Security Rule lands on your customers. CMMC applies only if you take CUI work. Colorado's ADMTA arrives January 1, 2027 and you are already most of the way there by accident.

That is worth naming plainly, because it removes the excuse and the forcing function at the same time. Every item left in this document is now justified by exactly one thing: **a buyer will ask, and the answer had better be true.**

But the trade is real, and it's this: **as a service provider you get audited periodically; as a product manufacturer your claims are load-bearing continuously.** Nobody audits your datasheet. They rely on it, and then something goes wrong, and the datasheet is evidence. That is why the through-line of this entire document is the same three items:

- The egress claim is your best asset — **so prove it in CI rather than asserting it in prose.**
- The security tests for your only remotely-reachable interface **have never run on the platform you ship.**
- The accuracy claim has no measurement behind it, and under a product regime an accuracy claim is a representation to the buyer.

Two weeks of engineering closes all three. That is the whole Phase 0 list, and it is worth more than every certification on this roadmap combined — because the certifications all just ask, in their various dialects, whether the things you say about your system are true.

One genuine upside from the EU exit that I did not expect to find: **Colorado's ADMTA hands you back the one EU obligation you were actually well positioned for.** Documented intended use, documented known limitations, human-oversight instructions, three-year retention — you have or nearly have all four, and you built them because they were good engineering rather than because a statute demanded them. Finish CR-F5 and you are compliant with a 2027 law before most of your competitors have read it. That is the rare case where the compliance artifact and the sales asset are the same document.

Which is, as the external review noted, the same question DataLogicEngine exists to answer for everyone else. Right now the system's answer about itself is weaker than the answer it promises about anything else. That's not a compliance chore. It's the product.

---

## Sources

Regulatory status verified August 17, 2026:

- [OMB Rescinds the "Common Form" Secure Software Attestation Requirement — M-26-05 (Inside Government Contracts / Covington)](https://www.insidegovernmentcontracts.com/2026/02/omb-rescinds-the-common-form-secure-software-attestation-requirement/)
- [Colorado Repeals and Replaces Its AI Act — the Automated Decision-Making Technology Act (Skadden)](https://www.skadden.com/insights/publications/2026/06/colorado-repeals-and-replaces-its-ai-act)
- [New State AI Laws Effective January 1, 2026, and the Executive Order Signaling Disruption (King & Spalding)](https://www.kslaw.com/news-and-insights/new-state-ai-laws-are-effective-on-january-1-2026-but-a-new-executive-order-signals-disruption)
- [CISA Delays Cyber Incident Reporting Rule for Critical Infrastructure — CIRCIA (Covington, Inside Privacy)](https://www.insideprivacy.com/critical-infrastructure/cisa-delays-cyber-incident-reporting-rule-for-critical-infrastructure/)
- [HIPAA Security Rule Update Postponed (HIPAA Journal)](https://www.hipaajournal.com/hipaa-security-rule-update-postponed/)
- [CMMC 2.0 Timeline: Key Dates, Deadlines & the Current Phase (Secureframe)](https://secureframe.com/hub/cmmc/proposed-final-rule)
- [OWASP GenAI LLM Top 10 2026 (OWASP Gen AI Security Project)](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [ISO/IEC 42001:2023 — AI management systems (ISO)](https://www.iso.org/standard/42001)
- [ISO/IEC 42006:2025 — Requirements for AIMS audit and certification bodies (ISO)](https://www.iso.org/standard/42006)
- [NIST SP 800-218A — Secure Software Development Practices for Generative AI (NIST CSRC)](https://csrc.nist.gov/pubs/sp/800/218/a/final)
- [NIST Secure Software Development Framework (NIST CSRC)](https://csrc.nist.gov/projects/ssdf)
- [FedRAMP Consolidated Rules for 2026 (fedramp.gov)](https://www.fedramp.gov/2026-06-25-propelling-change-fedramp-launches-consolidated-rules-for-2026/) — noted as *not applicable* under the installed-software model

Internal sources: `claude/DataLogicEngine_External_Review_2026-08-16.md`, `UKG_Enterprise_Standards_Assessment.docx`, `The 17-Axis System — Comprehensive Technical Architecture.pdf`, `Universal Simulated Knowledge Database USKD / UKG — System Documentation.pdf` (UKG project).

**EU sources retained for the record only** — the market decision of August 18, 2026 places these out of scope: [EU AI Act Digital Omnibus (Gibson Dunn)](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/), [Cyber Resilience Act reporting obligations (European Commission)](https://digital-strategy.ec.europa.eu/en/policies/cra-reporting).

> **Legal note:** this is technical and standards analysis, not legal advice. The HIPAA Business Associate determination in §3.2 in particular is a legal conclusion that depends on your actual contracts and support practices — have counsel confirm it before putting it in writing to a customer.
