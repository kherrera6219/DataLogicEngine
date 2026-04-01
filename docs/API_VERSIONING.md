# API Versioning Strategy

**Last Updated:** 2026-03-31
**Status:** Active

---

## Overview

DataLogicEngine uses **URL path versioning** for primary application APIs and explicit namespace governance for operational and compatibility routes.

---

## Current Version

**v1** - Primary application endpoints are prefixed with `/api/v1/`

Examples:
- `/api/v1/auth/login`
- `/api/v1/simulations`
- `/api/v1/truth/health`

Canonical unversioned namespaces that are still supported in the current contract:

1. `/api/admin/*`
2. `/api/contextual/*`
3. `/api/honeycomb/*`
4. `/api/locations*`
5. `/api/methods*`
6. `/api/search/*`
7. `/api/docs`

Compatibility aliases that remain active with deprecation headers:

1. `/api/compliance/*` -> `/api/v1/compliance/*`
2. `/api/ka/*` -> `/api/v1/ka/*`
3. `/api/mcp/*` -> `/api/v1/mcp/*`
4. `/api/persona/*` -> `/api/v1/persona/*`
5. `/api/pillar/*` -> `/api/v1/pillar/*`
6. `/api/simulations/*` -> `/api/v1/simulations/*`
7. `/api/truth/*` -> `/api/v1/truth/*`
8. `/api/ukg/*` -> `/api/v1/*`

---

## Versioning Rules

### When to Increment Version

**Major version bump (v1 → v2):**
- Breaking changes to request/response schema
- Removal of endpoints
- Changes to authentication mechanism
- Incompatible behavioral changes

**No version bump required:**
- Adding new optional fields
- Adding new endpoints
- Bug fixes
- Performance improvements
- Deprecation notices (without removal)

### Deprecation Policy

1. Announce deprecation at least **3 months** before removal
2. Add `Deprecation` header to affected endpoints
3. Add `Sunset` and `Link: rel="successor-version"` headers
4. Document migration path in changelog
5. Remove in next major version

---

## Version Header

Clients can request specific API behavior using headers:

```http
Accept: application/json
X-API-Version: 2026-01-12
```

The `X-API-Version` header is optional and can be used for minor behavioral variations within a major version.

---

## Client Recommendations

### Best Practices

1. **Prefer versioned application URLs** (`/api/v1/` not legacy `/api/` aliases)
2. **Handle unknown fields gracefully** - APIs may add new fields
3. **Check for deprecation headers** in responses
4. **Treat unversioned `/api/admin`, `/api/search`, `/api/contextual`, `/api/methods`, `/api/honeycomb`, and `/api/locations` as explicit namespace exceptions, not as versionless replacements for `/api/v1/*`**
5. **Subscribe to changelog** for updates

### SDK Versioning

The Python SDK (`sdk/python/`) follows semantic versioning:
- SDK 1.x.x → API v1
- SDK 2.x.x → API v2

---

## Migration Guide Template

When v2 is released, migration guides will follow this format:

```markdown
## Migrating from v1 to v2

### Breaking Changes
- [List of breaking changes]

### Deprecated Endpoints
| v1 Endpoint | v2 Replacement |
|-------------|----------------|
| /api/v1/old | /api/v2/new    |

### Timeline
- v2 Release: [Date]
- v1 Deprecation: [Date]
- v1 Removal: [Date]
```

---

## Contact

For API questions or version negotiation, contact the platform team or open an issue in the repository.
