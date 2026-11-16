# Instructor Answer Key: vuln-notes-express

> Hide this file from students before the exercise.

| # | Location | Issue | CWE | Severity | Remediation |
|---|----------|-------|-----|----------|-------------|
| E1 | `ADMIN_API_KEY` | Hard-coded secret (and it looks like a live payment key, so secret scanning push protection may block the push. That's a good demo!) | CWE-798 | High | Environment variable or secrets manager; rotate; enable secret scanning. |
| E2 | `GET /hello` | Reflected XSS: `req.query.name` is written into HTML unescaped | CWE-79 | Medium | Use a templating engine with autoescape, or escape (e.g., `escape-html`); set a CSP. |
| E3 | `merge()` + `PUT /users/:id/settings` | **Prototype pollution.** A body of `{"__proto__": {"isAdmin": true}}` pollutes `Object.prototype` | CWE-1321 | Critical | Skip `__proto__`, `constructor`, and `prototype` keys; use `Object.create(null)` or `Map`; validate the body with a schema (zod/ajv) and allow-list keys. |
| E4 | `GET /admin/stats` (`user.isAdmin`) | Authorization based on a property that E3 can inject, which turns pollution into privilege escalation. Also a non-constant-time key comparison. | CWE-863 / CWE-208 | High | Real authn/authz middleware; `crypto.timingSafeEqual` for key comparison; `Object.hasOwn` checks. |
| E5 | `GET /files` | Path traversal: `path.join` normalizes `../` but doesn't confine | CWE-22 | High | `res.sendFile(name, { root: FILES_DIR })`, plus reject names containing separators. |
| E6 | `GET /dns` | OS command injection through `exec` with a shell | CWE-78 | Critical | `execFile('nslookup', [host])` plus hostname allow-list validation, or `dns.promises.lookup`. |
| E7 | `POST /validate-email` | ReDoS: nested quantifier `([a-zA-Z0-9]+)*` causes catastrophic backtracking | CWE-1333 | Medium–High (blocks the event loop) | `/^[a-zA-Z0-9]+@example\.com$/`; input length limits; consider `re2`. |
| E8 | `POST /password-reset` | Insecure randomness for a security token | CWE-338 | High | `crypto.randomBytes(32).toString('hex')`; expiry; single use; store a hash. |
| E9 | `GET /logout` | Open redirect via `next` | CWE-601 | Medium | Allow-list relative paths (`next.startsWith('/') && !next.startsWith('//')`). |
| E10 | App-wide | No `helmet`, no rate limiting, `x-powered-by` exposed | CWE-693 | Low | `helmet()`, `express-rate-limit`, `app.disable('x-powered-by')`. |

## Teaching notes

- **E3 → E4 is the "aha" chain.** Neither line looks dangerous on its own. Ask the AI: *"Trace whether any request can influence the result of `user.isAdmin` on line X."* This is a good showcase for reasoning-based analysis.
- Connect E3 to the **minimist CVE-2021-44906** demo: the same bug class shows up in a real, popular library, and the first fix was incomplete (it blocked `__proto__` but not paths through a function's `constructor`).
- **Actual run (CodeQL 2.27.4, `javascript-security-extended`, 15 alerts):** E2 `js/reflected-xss` (L35) · E3 `js/prototype-polluting-assignment` (L25, L28), `js/prototype-pollution-utility` (L28), `js/remote-property-injection` (L25, L28, L40, L70) · E5 `js/path-injection` (L53) · E6 `js/command-line-injection` (L57) · E7 `js/redos` (L64), `js/polynomial-redos` (L65) · E9 `js/server-side-unvalidated-url-redirection` (L75) · E10 `js/missing-rate-limiting` (L52, L56).
- **CodeQL did NOT report:** E1 (hard-coded key; that's secret scanning's job), **E4** (the `isAdmin` authorization chain requires reasoning), E8 (`Math.random` token; `js/insecure-randomness` didn't fire here). These are the gaps AI review should fill. Check whether it does.
- **Actual Copilot code review** (PR #1 in the demo repo): flagged E1, E2, E3 → E4 (*"Recursive merge allows prototype pollution and admin bypass"*), E5, E6, E7, E9, plus unauthenticated settings access. It **missed E8**, so neither tool alone is complete.
