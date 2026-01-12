# API Versioning Strategy

**Last Updated:** 2026-01-12  
**Status:** Active

---

## Overview

DataLogicEngine uses **URL path versioning** for its REST API to ensure backward compatibility and clear version management.

---

## Current Version

**v1** - All endpoints are prefixed with `/api/v1/`

Examples:
- `/api/v1/auth/login`
- `/api/v1/simulations`
- `/api/ukg/pillars` (core UKG endpoints)

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
3. Document migration path in changelog
4. Remove in next major version

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

1. **Always use versioned URLs** (`/api/v1/` not `/api/`)
2. **Handle unknown fields gracefully** - APIs may add new fields
3. **Check for deprecation headers** in responses
4. **Subscribe to changelog** for updates

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
