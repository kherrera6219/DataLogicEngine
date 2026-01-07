# Dependency Vulnerability Report

**Generated:** December 7, 2025
**Status:** Partially Resolved

## Summary

- **Python Dependencies:** ✅ All up-to-date, no known vulnerabilities
- **NPM Dependencies:** ⚠️ 9 vulnerabilities remaining (requires breaking changes)

---

## Python Dependencies Status

All Python dependencies are current and secure:

- `werkzeug==3.1.4` (latest)
- `cryptography==46.0.3` (latest)
- `requests==2.32.5` (latest)
- `urllib3==2.5.0` (latest)
- `Jinja2==3.1.6` (latest)
- `flask-jwt-extended==4.6.0` (added in this update)

**Action Required:** ✅ None - all dependencies are current

---

## NPM Dependencies Status

### Fixed Vulnerabilities

1. **node-forge** - High severity ASN.1 vulnerabilities
   - **Status:** ✅ Fixed via `npm audit fix`
   - **CVEs:** GHSA-554w-wpv2-vw27, GHSA-5gfm-wpxj-wjgq, GHSA-65ch-62r8-g69g

### Remaining Vulnerabilities (9 total)

All remaining vulnerabilities are in **development dependencies** and do not affect production builds.

#### 1. nth-check (<2.0.1)
- **Severity:** High
- **Issue:** Inefficient Regular Expression Complexity
- **CVE:** GHSA-rp65-9cf3-cjxr
- **Affected:** Development builds only (svgo dependency chain)
- **Fix Available:** Yes, but requires breaking change to react-scripts
- **Impact:** Low (development only)

#### 2. postcss (<8.4.31)
- **Severity:** Moderate
- **Issue:** PostCSS line return parsing error
- **CVE:** GHSA-7fh5-64p2-3v2j
- **Affected:** Development builds only (resolve-url-loader)
- **Fix Available:** Yes, but requires breaking change to react-scripts
- **Impact:** Low (development only)

#### 3. webpack-dev-server (<=5.2.0)
- **Severity:** Moderate (2 CVEs)
- **Issues:**
  - Source code theft via malicious websites (non-Chromium browsers)
  - Source code theft via malicious websites (all browsers)
- **CVEs:** GHSA-9jgg-88mc-972h, GHSA-4v9v-hfq4-rm2v
- **Affected:** Development server only
- **Fix Available:** Yes, but requires breaking change to react-scripts
- **Impact:** Medium (development only, requires user to visit malicious site)

---

## Dependency Chain

The vulnerabilities are all part of the `react-scripts@5.0.1` dependency chain:

```
react-scripts@5.0.1
├── @svgr/webpack@5.5.0
│   └── @svgr/plugin-svgo@5.5.0
│       └── svgo@1.3.2
│           └── css-select@3.1.0
│               └── nth-check@1.0.2 ⚠️ HIGH
├── resolve-url-loader@4.0.0
│   └── postcss@8.4.5 ⚠️ MODERATE
└── webpack-dev-server@4.15.1 ⚠️ MODERATE
```

---

## Recommended Actions

### Immediate (Current State)

✅ **Safe for development and production:**
- All vulnerabilities are in development dependencies
- Production builds are unaffected
- Risk is minimal and only during development

### Short-term (Next Sprint)

1. **Migrate from react-scripts to Vite or Next.js**
   - `react-scripts` is in maintenance mode
   - Modern alternatives (Vite, Next.js) have better security posture
   - Breaking change but future-proofs the application

2. **Alternative: Use create-react-app@latest**
   - Update to `react-scripts@6.x` if available
   - May require code changes for compatibility

### Long-term

1. **Implement automated dependency scanning**
   - Add Dependabot or Renovate for automatic PRs
   - Set up GitHub Security Scanning
   - Regular dependency update schedule

2. **Security Best Practices**
   - Only access trusted websites during development
   - Use Chromium-based browsers for development (Chrome/Edge)
   - Consider using Docker for isolated dev environments

---

## How to Apply Breaking Changes

⚠️ **WARNING:** This will require significant testing

```bash
cd frontend
npm audit fix --force
```

This will:
- Downgrade react-scripts to 0.0.0 (essentially breaking it)
- Require migration to a different build tool
- May break existing code

**Recommended approach instead:**
1. Migrate to Vite or Next.js in a separate branch
2. Test thoroughly
3. Deploy when ready

---

## Current Mitigation

✅ **Development Environment:**
- Use Chromium-based browsers (Chrome, Edge, Brave)
- Avoid visiting untrusted websites while dev server is running
- Development server only accessible on localhost by default

✅ **Production Environment:**
- Production builds use optimized static files
- No webpack-dev-server in production
- No vulnerable dependencies bundled in final build

---

## References

- [GHSA-rp65-9cf3-cjxr](https://github.com/advisories/GHSA-rp65-9cf3-cjxr) - nth-check
- [GHSA-7fh5-64p2-3v2j](https://github.com/advisories/GHSA-7fh5-64p2-3v2j) - postcss
- [GHSA-9jgg-88mc-972h](https://github.com/advisories/GHSA-9jgg-88mc-972h) - webpack-dev-server
- [GHSA-4v9v-hfq4-rm2v](https://github.com/advisories/GHSA-4v9v-hfq4-rm2v) - webpack-dev-server

---

**Document Status:** Current
**Next Review:** Before Phase 4 (Performance Optimization)
**Owner:** Development Team
