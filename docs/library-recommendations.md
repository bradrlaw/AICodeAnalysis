# Recommended Open-Source Analysis Targets

Selection criteria: **well known**, **small enough to reason about in a lecture**, **permissively licensed**, **readable code**, and (for security demos) a **public, already-fixed CVE** with a small diff we can compare against. All versions are pinned in [`scripts/setup-targets.ps1`](../scripts/setup-targets.ps1).

## Primary targets (used in the lecture)

| Target | Lang | Pinned | Size (core) | License | Used for | Why it works |
|--------|------|--------|-------------|---------|----------|--------------|
| [TinyDB](https://github.com/msiemens/tinydb) | Python | `v4.8.0` | ~2.3k LOC, 9 modules | MIT | **Understanding** | Clean layering (TinyDB → Table → Storage/Middleware), a query DSL built with operator overloading, an LRU query cache. Small enough that students can verify every AI claim. |
| [Express](https://github.com/expressjs/express) | JS | `4.21.2` | ~4.3k LOC in `lib/` | MIT | **Architecture** | Classic middleware-pipeline / chain-of-responsibility; Router → Layer → Route is perfect for a sequence diagram. Most students have used it. |
| [Flask](https://github.com/pallets/flask) | Python | `3.0.3` | ~7k LOC | BSD-3 | **Architecture** (alt) | Context-local globals (`request`, `g`), app vs request context, the `sansio` split, blueprints, signals. Great for "explain the design decision" prompts. |
| [Bottle](https://github.com/bottlepy/bottle) | Python | `0.13.2` | **one 4,680-line file** | MIT | **Refactoring at scale** | A real "god file." Ideal for *planning* a modular decomposition and discussing why the authors chose a single file (an intentional trade-off, not a mistake). |
| `labs/legacy-invoice` | Python | (in repo) | ~100 LOC | — | **Refactoring hands-on** | Purpose-built smells (long function, magic numbers, duplication, global state) plus characterization tests. Safe to refactor live in minutes. |

## Security targets (defensive study only)

| Target | Lang | Vulnerable → Fixed | CVE | What students learn |
|--------|------|-------------------|-----|---------------------|
| [minimist](https://github.com/minimistjs/minimist) | JS | `v1.2.5` → `v1.2.6` | [CVE-2021-44906](https://nvd.nist.gov/vuln/detail/CVE-2021-44906) — prototype pollution | ~250 LOC. 1.2.5 *already* blocked `__proto__` but missed `constructor.prototype` — a textbook **incomplete fix**. Teaches *variant analysis*: "given this bug, where else does the pattern occur?" Fix diff is 8 lines. |
| [requests](https://github.com/psf/requests) | Python | `v2.30.0` → `v2.31.0` | [CVE-2023-32681](https://nvd.nist.gov/vuln/detail/CVE-2023-32681) — Proxy-Authorization header leak | Subtle, logic-level bug (not a "dangerous function"). Shows where pattern-matching scanners struggle and where reasoning helps — and where AI also misses things without hints. Fix is a 1-line condition in `sessions.py`. |
| `labs/vuln-notes-flask` | Python | (in repo) | — | Intentionally vulnerable mini app: SQLi, path traversal, command injection, insecure deserialization, XSS, IDOR, weak hashing, debug mode, hard-coded secret. Has an instructor answer key. |
| `labs/vuln-notes-express` | JS | (in repo) | — | Same idea for Node: prototype pollution, command injection, ReDoS, XSS, open redirect, path traversal, insecure randomness, hard-coded secret. |

## Optional / stretch targets (take-home)

| Target | Lang | Why |
|--------|------|-----|
| [OWASP Juice Shop](https://github.com/juice-shop/juice-shop) | TS/Angular | Large, intentionally insecure, realistic. Excellent for CodeQL + AI triage practice. |
| [OWASP PyGoat](https://github.com/adeyosemanputra/pygoat) | Python/Django | Intentionally insecure Django app mapped to OWASP Top 10. |
| [ms](https://github.com/vercel/ms) | JS | Tiny (one function). Historical ReDoS ([CVE-2017-20162](https://nvd.nist.gov/vuln/detail/CVE-2017-20162)) — good for regex-complexity discussions. |
| [httpx](https://github.com/encode/httpx) vs requests | Python | "Compare two architectures that solve the same problem" prompts. |
| [Zod](https://github.com/colinhacks/zod) | TS | Strongly typed TS codebase; good for type-level understanding prompts. |
| [click](https://github.com/pallets/click) | Python | Decorator-heavy design; good for "explain the magic" prompts. |

## Why pinned, older versions?

- **Reproducibility:** prompts, file names, and expected answers stay valid for every class section.
- **Ground truth:** for CVE targets, the upstream fix *is* the answer key — students can diff their AI-proposed fix against what the maintainers shipped.
- **Ethics:** we only analyze **publicly disclosed, already-patched** vulnerabilities in open-source code we're licensed to read. We do not hunt for new 0-days in other people's projects during class. (If students find something new later, see responsible disclosure in [ethics-and-defense.md](ethics-and-defense.md).)
