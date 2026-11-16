# Demo 4: Finding & Remedying Vulnerabilities

**Time on stage:** 8 minutes · **Targets:** `labs\vuln-notes-flask`, `labs\vuln-notes-express`, `targets\minimist-1.2.5` vs `targets\minimist-1.2.6`, `targets\requests-2.30.0` vs `targets\requests-2.31.0`
**Tools:** Copilot CLI, CodeQL CLI, Copilot code review & Copilot Autofix on GitHub.com

> ⚖️ **Scope:** defensive analysis of **our own lab code** and of **publicly disclosed, already-fixed** CVEs in open-source code. We find, explain, fix, and regression-test. We do **not** build exploits or attack running systems.

## Goal

Show that **AI review and static analysis are complementary**:

| | CodeQL (deterministic) | AI review (probabilistic) |
|---|---|---|
| Strength | Precise taint tracking source → sink, repeatable, CI-friendly | Logic/authorization flaws, chained issues, explaining context, writing fixes |
| Weakness | Misses missing logic (authz, CSRF) and business-logic bugs | Can miss issues, invent issues, and vary from run to run |
| Use it for | The gate in CI | Triage, explanation, remediation, design-level review |

---

## Part A: AI security review of the lab apps (2 min)

```powershell
cd labs\vuln-notes-express
copilot --plan
```

```text
@server.js
Situation: I'm reviewing this Express service before it ships.
Constraints: Read-only. Defensive review only; do not write exploit payloads.
Objective: Identify security weaknesses.
Product: A table sorted by severity: ID | line | weakness | CWE | why it's exploitable (one sentence) | fix.
Then: identify any CHAINS where two individually-minor issues combine into a serious one.
Evidence: cite line numbers. Mark low-confidence findings as "needs verification".
```

**Compare against** [`labs/vuln-notes-express/ANSWER_KEY.md`](../../labs/vuln-notes-express/ANSWER_KEY.md). Highlight the **prototype pollution → `user.isAdmin` authorization bypass chain** (E3 → E4), which a pure pattern scanner won't connect.

Run the same prompt on `labs\vuln-notes-flask\app.py` and compare with [its answer key](../../labs/vuln-notes-flask/ANSWER_KEY.md). Watch for **false positives** (e.g., claiming the parameterized `/register` query is injectable).

## Part B: CodeQL, the deterministic baseline (2 min) <a id="codeql"></a>

Build databases **before** class (it takes a minute or two each):

```powershell
# From the repo root
codeql database create codeql-db-flask   --language=python                --source-root=labs\vuln-notes-flask
codeql database create codeql-db-express --language=javascript-typescript --source-root=labs\vuln-notes-express

codeql database analyze codeql-db-flask   codeql/python-queries:codeql-suites/python-security-extended.qls `
  --download --format=sarif-latest --output=flask.sarif
codeql database analyze codeql-db-express codeql/javascript-queries:codeql-suites/javascript-security-extended.qls `
  --download --format=sarif-latest --output=express.sarif
```

Live: open the SARIF in VS Code (*SARIF Viewer* extension) and compare against Part A.

**AI-assisted triage of the scanner output:**

```text
@flask.sarif @labs/vuln-notes-flask/app.py
For each CodeQL result: (1) explain the source → sink path in plain English, (2) classify it as
true positive / false positive with justification, (3) propose the minimal fix.
Then list vulnerabilities in app.py that CodeQL did NOT report, and explain why a data-flow
analyzer would miss them.
```

> 🎤 **Talking point:** the "what did CodeQL miss?" question usually surfaces the IDOR / missing-auth / CSRF issues. That's the complementarity in one slide.

## Part C: Remediation in the PR workflow (1.5 min)

Pre-stage before class:
1. Push both labs to a **throwaway** GitHub repo (keep `ANSWER_KEY.md` out of it).
2. Enable **Settings → Code security → Code scanning → CodeQL default setup**. Copilot Autofix is on by default for eligible repos.
3. Enable **Secret scanning + push protection**. The fake `sk_live_…` key in the Express lab may be blocked on push, which is a nice live moment. Bypass it only for this throwaway repo.
4. Open a PR that touches the vulnerable routes and **request Copilot as a reviewer**.

Live: show an alert → **Generate fix** (Autofix) → review the suggested diff → commit to the PR branch → alert closes on re-scan. Show Copilot's PR review comments next to it.

**Locally**, after applying a fix in your working tree, the CLI can review the change:

```text
/security-review Focus on whether the fix fully closes the bug class, not just this instance.
```

## Part D: Real CVE, variant analysis & incomplete fixes (2.5 min)

### minimist CVE-2021-44906 (prototype pollution), JS

`targets\minimist-1.2.5\index.js` is ~250 lines. Version 1.2.5 **already** had a `__proto__` guard in `setKey`. The CVE exists because that guard was **incomplete**.

```text
@targets/minimist-1.2.5/index.js
Situation: This argument parser receives untrusted input (argv can come from users or config).
Constraints: Defensive analysis only. No exploit chains.
Objective: Review setKey() for prototype pollution.
  1. What does the existing '__proto__' check protect against?
  2. Is it sufficient? Which other property paths can reach a prototype object? Explain conceptually.
  3. Propose a minimal fix and a regression test (tape, matching test/ style) asserting that
     Object.prototype and Function.prototype are unchanged after parsing.
Evidence: cite line numbers.
```

Then show the **real fix** and ask the AI to grade it:

```powershell
git diff --no-index targets\minimist-1.2.5\index.js targets\minimist-1.2.6\index.js
```

```text
Here is the upstream fix (diff above). Compare it with your proposal. Is the upstream fix complete?
Which inputs does it rely on `typeof obj[key] === 'function'` to handle, and is there any remaining
bug-class risk? Then: search the rest of this repository (labs/) for OTHER functions that recursively
assign user-controlled keys, i.e., variants of the same bug class.
```

**A good answer:** the 1.2.6 fix adds `isConstructorOrProto()`, blocking `constructor` (when it's a function) as well as `__proto__`, at both the intermediate and final key. **Variant analysis** should find `merge()` in `labs/vuln-notes-express/server.js`, the same bug class in *our* code.

> 🎤 **Talking point:** *"Fix the class, not the instance."* A patch that blocks one spelling of the attack is how CVE follow-ups happen. AI is very good at "find me everything shaped like this."

### requests CVE-2023-32681 (Proxy-Authorization leak), Python (alternate / take-home)

A **logic** bug with no dangerous function call in sight. Run two prompts and compare:

**Unguided (often misses it):**
```text
@targets/requests-2.30.0/requests/sessions.py  Find security vulnerabilities in this file.
```

**Threat-model-guided:**
```text
@targets/requests-2.30.0/requests/sessions.py
Threat model: a client uses an HTTPS proxy with credentials and follows a redirect to an HTTPS URL.
Trace rebuild_proxies() and determine whether the Proxy-Authorization header could ever be sent to
anyone other than the proxy (consider CONNECT tunneling, where urllib3 already authenticates to the proxy).
Cite line numbers and propose a minimal fix.
```

Then compare with upstream: `git diff --no-index targets\requests-2.30.0\requests\sessions.py targets\requests-2.31.0\requests\sessions.py`. The fix only adds the header when the scheme is **not** HTTPS (one-line condition).

> 🎤 **Talking point:** AI finds what you point it at. **Threat modeling first, then prompt** beats "find bugs."

---

## Pitfalls to call out

- **False confidence in "no issues found."** Absence of findings is not evidence of security.
- **Fixes that compile but don't close the class** (e.g., blocking only `__proto__`). Always ask "is this complete?" and add regression tests.
- **Autofix is a suggestion.** Review it like any PR: tests, behavior, side effects.
- **Never paste real secrets or proprietary vulnerable code into unapproved tools.** Use org-approved tools or a local model (Demo 5).
