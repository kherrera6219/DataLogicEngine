# DataLogicEngine Microsoft distribution and submission dossier

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-EXT-002 |
| Title | Microsoft distribution and submission dossier |
| Document version | v1.0.0 |
| Product version | 4.3.0 |
| Status | not_evaluated |
| Audience | Distribution owner, product/release authority, legal/privacy/security, accessibility, operations, and Microsoft submission reviewers |
| Owner | Distribution Owner |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Current official Microsoft Store/Partner Center guidance, exact signed artifact, canonical product records, and submission results |
| Confidentiality | Public |
| Last reviewed | 2026-07-24 |
| Next-review trigger | Microsoft policy/guidance, route/package, Partner Center field, artifact/signature, privacy/legal, certification, or submission-result change |
| Requirements and evidence | Official Microsoft policy snapshot, Partner Center submission, signed installer, WACK/applicable tests, metadata/assets, and certification correspondence |

## No Microsoft approval claim

DataLogicEngine has not been submitted to, certified by, endorsed by, or approved
by Microsoft. No Partner Center product, Store listing, certification result,
Windows App Certification Kit (WACK) result, or Microsoft correspondence is
recorded. This dossier is `not_evaluated` and production/public distribution is
**NO-GO**.

## Selected qualification route

The recommended route selected for qualification is the Microsoft Store
traditional desktop **MSI/EXE submission** path using the existing standalone
NSIS `.exe` architecture. It avoids an unproved MSIX/Desktop Bridge conversion
and matches the current installer investment. This is a route selection for
engineering and policy qualification, not authorization to submit or publish.

The direct-download signed installer may remain a separate owner-controlled
channel only after the same signing, legal, privacy, accessibility, lifecycle,
security, support, and release gates pass. Store and direct artifacts must remain
hash/version/support aligned.

## Official policy snapshot

Reviewed official sources on 2026-07-14:

- [Microsoft Store Policies](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies), document version 7.19, published 2025-09-10 and effective 2025-10-14 on the reviewed page.
- [Create an app submission for an MSI/EXE app](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/create-app-submission), including Partner Center availability/listing/package/property/age-rating/submission fields.
- [MSI/EXE app package requirements](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/app-package-requirements), including HTTPS/versioned installer URL, `.msi`/`.exe`, signature, immutability, silent install, and standalone-installer requirements.
- [Windows App Certification Kit](https://learn.microsoft.com/en-us/windows/uwp/debug-test-perf/windows-app-certification-kit) and [test catalog](https://learn.microsoft.com/en-us/windows/uwp/debug-test-perf/windows-app-certification-kit-tests), which direct publishers to current Store policy and the current applicable kit/workflow.

Policies can change after review. Refresh every linked page immediately before
submission, record page version/date/hash or preserved review evidence as
permitted, and resolve differences. This dossier does not replace the Microsoft
App Developer Agreement, Partner Center terms, legal advice, or certification.

## MSI/EXE package requirements matrix

| Requirement from reviewed official guidance | DataLogicEngine state | Required evidence |
|---|---|---|
| Installer is `.msi` or `.exe` | NSIS `.exe` architecture exists | Final canonical filename and exact signed binary |
| HTTPS direct download URL | Not established | Owner-controlled TLS URL, availability monitoring, access without auth/redirect ambiguity |
| Versioned URL and immutable submitted binary | Not established | URL/version policy; hash before/after submission; no in-place replacement |
| Installer and all PE files signed with trusted CA chain | Current candidate unsigned | Approved publisher, timestamp/revocation, complete PE signature inventory |
| Silent install; UAC prompt allowed | Candidate `/S` syntax documented only | Signed clean install logs/exit code and Store-compatible unattended behavior |
| Standalone installer, not downloader stub | Current payload is intended standalone | Network capture/offline install and complete component/payload proof |
| Updated binary uses updated versioned URL | Not established | Release/update publishing procedure and rollback/support record |
| Version managed by installer for Win32 route | Product authority is 4.3.0/4.3.0.0 | Installer/file/UI/API version parity and upgrade ordering |

The app-owned PostgreSQL, Redis, Neo4j, ChromaDB, and object-store delivery must
not turn the installer into an undocumented downloader or install prohibited/
unlicensed services. Exact offline/runtime delivery and redistribution approval
remain open.

## Microsoft Store policy review matrix

| Area | Current engineering state | Submission gate |
|---|---|---|
| Distinct value and accurate metadata | Product requirements and governed trace/evidence differentiators documented | Final listing must match exact installed behavior and avoid certification/AI claims |
| Testability | Single-owner/local provider/service prerequisites exist | Certification notes, safe test credentials/data, deterministic reviewer path, functional required services |
| Usability/compatibility | Automated UI checks and Windows scope exist | Signed supported-device/requirements detection, responsiveness, lifecycle, error/recovery evidence |
| Privacy policy for Win32/personal information | Canonical privacy notice and PIA exist | Public stable privacy URL, deployment legal review, accurate access/use/store/security/disclosure/control statements |
| Consent for external personal-information sharing | Provider/connector preflight/control foundations exist | Installed opt-in/withdrawal behavior and legal applicability review |
| Content/metadata rights | Third-party index and legal actions exist | Final icons/screenshots/text/data/model/provider/trademark/license permissions |
| Security/safety | Threat/release controls exist; alert 389 is fixed | Signed artifact, final scans, no-egress/penetration, and independent review |
| Support | Troubleshooting/operations docs exist | Public support contact/process, response/maintenance policy, data recovery/uninstall guidance |
| Accessibility | Automated evidence exists | Manual packaged NVDA/scaling/contrast and truthful accessibility disclosure |
| Updates | Auto-update disabled/fail-closed | Store/direct-channel update ownership, signed metadata, replay/downgrade/rollback evidence |

## Partner Center submission inventory

The final submission record captures:

- Partner Center account/publisher identity, agreements, tax/payout data where
  applicable, reserved product name, and user access/least privilege;
- markets, discoverability, pricing/availability, category, age ratings, license
  terms, copyright/trademark, privacy URL, support/contact, and applicable notices;
- short/full descriptions, keywords, features, system requirements, accessibility,
  AI/provider/data-egress disclosures, known limitations, and release notes;
- required 1:1 Store logo, recommended poster art, icons, screenshots, captions,
  alt text/accessibility considerations, and proof of rights;
- package URL, architecture, languages, install/uninstall switches, version,
  SHA-256, signature/publisher/timestamp, and availability monitoring;
- certification notes, test path, provider/service setup, safe demo data/account
  if required, offline/failure behavior, and reviewer contact;
- submission ID/date, policy version, automated/manual certification results,
  failures/correspondence, corrections, resubmission, and final decision.

Do not place production credentials, private keys, customer data, or unrestricted
internal service access in certification notes or test accounts.

## WACK and certification evidence

Install the current Windows SDK/Certification Kit on a clean supported machine
and run the current workflow applicable to the selected traditional desktop
submission and any package conversion actually used. Record kit/SDK/Windows
versions, app type, selected tests, machine profile, exact installer/package hash,
HTML/XML reports, failures, applicability decisions, remediation, and rerun.

The reviewed WACK guidance notes that an active user session is required and
that environment/performance can affect results. Applicability and Store-side
testing can differ by app/package type; do not mark a test `pass` merely because
it was unavailable or grayed out. Use `not_applicable` only with policy/reviewer
basis. No WACK run has been performed for the signed 4.3.0 release candidate.

## Submission blockers

- No final signed/timestamped installer or trusted publisher.
- Reproducibility hashes differ; exact final artifact is not frozen.
- Signed install/repair/upgrade/rollback/uninstall and silent/offline behavior are
  not accepted.
- Required service delivery, licensing/redistribution, legal actions,
  independent object-store license/security acceptance, and privacy/legal
  review remain open. The engineering object-store selection is recorded in
  ADR-0010 and Dependabot alert 389 is fixed.
- Packaged accessibility/NVDA, provider/service, security/no-egress, failure/
  recovery, performance/soak, pilot, and independent reviews are incomplete.
- Partner Center identity/listing/assets/privacy/support/package URL and WACK/
  certification evidence do not exist.

## Final disposition

CP16-D content is present but the dossier remains `not_evaluated`. Only recorded
Partner Center certification/publication evidence for the exact signed artifact,
after all product release gates pass, may change the status. A Microsoft Store
listing must never be described as broader Microsoft endorsement or certification
beyond the exact result Microsoft provides.
