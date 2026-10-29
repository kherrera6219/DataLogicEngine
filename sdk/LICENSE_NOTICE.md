# SDK and application license notice

| Package | License | Role |
|---|---|---|
| DataLogicEngine project-owned application source | MIT | Desktop product, governed runtime |
| `ukg-sdk` (Python, `sdk/UKG_Python_SDK`) | MIT | Thin client for the installed DLE gateway |
| `@datalogicengine/sdk` (TypeScript) | MIT | Thin client for the installed DLE gateway |

SDKs intentionally do **not** embed provider credentials or a second reasoning stack.
They call the installed service (`dle-gateway.v1`) only.

Third-party packages, model weights, media, provider services, and bundled infrastructure retain their respective licensing/terms. The project's MIT license does not authorize distribution of a release-blocked Windows installer or waive its qualification requirements.
