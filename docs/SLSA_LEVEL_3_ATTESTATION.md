# Supply Chain Layers for Software Artifacts (SLSA) - Level 3 Strategy
## DataLogicEngine (UKG) Build Integrity

This document outlines the strategy to achieve **SLSA Level 3** complaince for the UKG build and release process.

### 1. Build Definition (Verified Source)
*   **Requirement:** The build must be defined in a version-controlled script (e.g., `.github/workflows/build.yml`).
*   **Implementation:** All build steps are defined as code. No manual steps (e.g., "Developer runs build on laptop") are permitted for production releases.

### 2. Build Service (Hosted)
*   **Requirement:** The build must run on a hosted build service, not on a developer's machine.
*   **Implementation:** 
    *   **Primary:** GitHub Actions (Hosted Runners)
    *   **Isolation:** Each build runs in an ephemeral VM/Container that is destroyed after use.

### 3. Provenance Generation (Authenticated)
*   **Requirement:** The build service must generate an authenticated stream of data describing how the artifact was produced.
*   **Implementation:**
    *   **Tooling:** `github-slsa-provenance-generator`
    *   **Signing:** All provenance attestations are signed using **Sigstore/Cosign** (Keyless signing via OIDC).
    *   **Output:** `provenance.intoto.jsonl` attached to every container image and Python wheel.

### 4. Non-Falsifiable (Tamper Proof)
*   **Requirement:** Users cannot modify the provenance data after it is generated.
*   **Implementation:**
    *   Provenance is uploaded to **Rekor** (Public transparency log) immediately upon generation.
    *   The hash of the build logs is included in the provenance.

### 5. Verification Policy
*   **Enforcement:** The Deployment Controller (Admission Controller in K8s) validates the provenance before allowing any pod to start.
*   **Policy:** "Image must have a valid Sigstore signature and provenance tracing back to the `main` branch of `kherrera6219/DataLogicEngine`."

---
**Status:** Planning / Partial Implementation
**Target Date:** Q2 2026
