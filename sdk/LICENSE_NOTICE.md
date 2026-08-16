# SDK license notice

| Package | License | Role |
|---|---|---|
| DataLogicEngine application (this repository product) | PolyForm Noncommercial 1.0.0 (+ commercial terms as published) | Desktop product, governed runtime |
| `ukg-sdk` (Python, `sdk/UKG_Python_SDK`) | MIT | Thin client for the installed DLE gateway |
| `@datalogicengine/sdk` (TypeScript) | MIT | Thin client for the installed DLE gateway |

SDKs intentionally do **not** embed provider credentials or a second reasoning stack.
They call the installed service (`dle-gateway.v1`) only.

If you redistribute the desktop product, follow the application license — not the SDK MIT terms alone.
