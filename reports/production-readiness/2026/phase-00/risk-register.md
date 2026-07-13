# Phase 0 Risk Register

| ID | Risk | Severity | Owner phase | Disposition |
|---|---|---|---:|---|
| P0-R001 | Governed lifecycle is not causal on normal chat | Critical | 5, 6 | Open; release blocking |
| P0-R002 | Active mutations bypass intended authorization | Critical | 1 | Open; release blocking |
| P0-R003 | Public errors can expose exception text | Critical | 1 | Open; release blocking |
| P0-R004 | Installer does not deliver required data plane | High | 2, 3, 4, 14, 15 | Open |
| P0-R005 | Compose omits required ChromaDB | High | 0, 3 | Open |
| P0-R006 | Broad and `latest` image tags prevent reproducibility | High | 0, 3, 14 | Open |
| P0-R007 | Podman Machine requires WSL2/virtualization and still needs redistribution/support qualification | High | 0, 3, 14 | Architecture accepted; qualification open |
| P0-R008 | Native delivery lacks official Redis OSS Windows server | High | 0, 3, 14 | Avoided by accepted container decision |
| P0-R009 | Product/frontend/SDK/document versions disagree | Medium | 0, 7, 14 | Open |
| P0-R010 | Tests do not prove installed cross-system causality | High | 0, 5, 15 | Open |
| P0-R011 | Legal/redistribution/signing authority is not recorded | High | 0, 14 | Open |
| P0-R012 | Phase 0 changes are not committed | Medium | 0 | Closed by the Phase 0 checkpoint commit |
| P0-R013 | Independent architecture, security, data integrity, service, AI, API, accessibility, and documentation reviewers are unnamed | High | 0, 15, 16 | Open; release blocking |
| P0-R014 | Minimum/recommended hardware and enterprise Windows policy compatibility are not approved | High | 0, 3, 14, 15 | Open |
| P0-R015 | Verified-secret history scan could expose committed credentials | Critical | 0 | Closed 2026-07-13; TruffleHog 3.93.1 found zero verified secrets |
| P0-R016 | Active shell Python 3.13 differs from approved CI Python 3.11 | Medium | 0 | Closed 2026-07-13; strict gate passed with isolated Python 3.11.14 |
