> **Recorded fallback** · GitHub Copilot CLI, read-only (`--deny-tool write --deny-tool shell`) · model gpt-6.1-sol · prompt: see docs/demo-script.md

 ● Security-review (model: gpt-6.1-sol) Defensive app security review                            49s
   │ 2 earlier approval checks are hidden
   │ Reviewed **`C:\projects\AICodeAnalysisLecture\labs\vuln-notes-flask\app.py`...
   │ Read requirements.txt 1 line read
   └ Search "^" (app.py) 133 lines found

Reviewed **`C:\projects\AICodeAnalysisLecture\labs\vuln-notes-flask\app.py`**, with exact line numbers. Findings assume an attacker can reach the application; its default listener is loopback-only. No payloads were generated or code changed. Git inspection and ancestor repository instructions were inaccessible, so diff scope and those instructions could not be verified.

## Security findings

All line ranges below refer to the absolute path above.

| line | weakness | CWE | why it matters (one sentence) | fix |
|---|---|---|---|---|
| 117–120 | OS command injection — **Severity: CRITICAL \| Confidence: 10/10** | CWE-78 | Unauthenticated form input `format` is interpolated into `subprocess.check_output(..., shell=True)`, allowing command execution with the application’s privileges. | Use `shell=False` with an argument list, strictly allowlist supported formats, and require authorization. |
| 124–127 | Unsafe deserialization — **Severity: CRITICAL \| Confidence: 10/10** | CWE-502 | An unauthenticated client controls the `prefs` cookie passed through Base64 decoding into `pickle.loads`, which can execute arbitrary code during deserialization. | Replace pickle with schema-validated JSON; use authenticated storage if preferences must be tamper-resistant. |
| 83–88 | Server-side template injection, also enabling XSS — **Severity: CRITICAL \| Confidence: 10/10** | CWE-1336; CWE-79 | Query input `q` and database titles become Jinja template source through an f-string passed to `render_template_string`, permitting server-side execution and unescaped browser content. | Use a fixed template and pass `q` and rows as template variables, retaining autoescaping. |
| 83–86 | SQL injection — **Severity: HIGH \| Confidence: 10/10** | CWE-89 | Request parameter `q` is interpolated directly into SQL, allowing a registered attacker to alter the query and bypass its owner restriction or extract database data. | Bind both owner ID and the complete search pattern using SQL parameters; require an authenticated session. |
| 91–97 | Missing note authorization / IDOR — **Severity: HIGH \| Confidence: 10/10** | CWE-862; CWE-639 | Anyone can retrieve another user’s note body by ID because the handler checks neither authentication nor `owner_id`. | Require authentication and query by both note ID and the authenticated user’s ID. |
| 111–114 | Arbitrary file read through path traversal — **Severity: HIGH \| Confidence: 10/10** | CWE-22 | Unauthenticated `name` input reaches `send_file(os.path.join(...))` without confinement, allowing disclosure of files readable by the application, including its database. | Use `send_from_directory` for confinement, reject unsuitable names, and enforce attachment authorization. |
| 18; 75; 85; 105 | Known session-signing key — **Severity: HIGH \| Confidence: 10/10** | CWE-321 | The fixed, disclosed Flask `SECRET_KEY` allows attackers to forge session cookies containing another user’s `user_id`, which the application trusts for ownership decisions. | Provision a strong deployment-specific secret outside source, rotate this key, and invalidate existing sessions. |
| 52–53; 59–61; 70–72 | Unsalted MD5 password hashing — **Severity: MEDIUM \| Confidence: 10/10** | CWE-916 | Passwords use fast, unsalted MD5, enabling efficient offline guessing if database hashes are obtained, including through the file-read vulnerability above. | Use Argon2id, scrypt, or an appropriate password-hashing helper, and migrate hashes on successful login. |

**Additional code evidence:** Note titles originate in `request.form["title"]` at lines **100–105**, enter HTML at **87**, and become template source at **88**; this establishes a stored input path alongside the direct `q` path.

## What CodeQL would likely miss—and what it can detect

- **Missing note ownership checks (91–97): likely missed by generic taint/data-flow rules.** The SQL is parameterized; the defect is the absent application-specific invariant that the requested note must belong to the authenticated user. Custom authorization modeling or dedicated checks are needed.
- **Stored title-to-template flow (100–105 → database → 87–88): potentially missed; needs verification against the selected query suite and models.** Establishing that flow requires linking separate requests through persistent database state. However, the direct `q`-to-template path is a known template-injection category, so missing the stored path would not necessarily leave this sink unreported.

SQL injection, shell injection, unsafe deserialization, path injection, template injection/XSS, weak cryptography, and hardcoded credentials have established CodeQL query categories; actual alerts depend on enabled queries and framework models. They should **not** be broadly described as analyzer blind spots.

The explicit development-only, loopback-bound `debug=True` setting at line **133** is not reported as a production exposure.

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| 1 | 🔴 CRITICAL | app.py | 117–120 | OS command injection | 10/10 |
| 2 | 🔴 CRITICAL | app.py | 124–127 | Unsafe pickle deserialization | 10/10 |
| 3 | 🔴 CRITICAL | app.py | 83–88 | Server-side template injection | 10/10 |
| 4 | 🟠 HIGH | app.py | 83–86 | SQL injection | 10/10 |
| 5 | 🟠 HIGH | app.py | 91–97 | Missing note ownership checks | 10/10 |
| 6 | 🟠 HIGH | app.py | 111–114 | Path traversal / arbitrary file read | 10/10 |
| 7 | 🟠 HIGH | app.py | 18, 75, 85, 105 | Hardcoded session-signing key | 10/10 |
| 8 | 🟡 MEDIUM | app.py | 52–53, 59–61, 70–72 | Unsalted MD5 password hashing | 10/10 |

These findings assume attacker access to the application; its default listener is loopback-only.

| line | weakness | CWE | why it matters (1 sentence) | fix |
|---|---|---|---|---|
| 117–120 | Command injection | CWE-78 | Unauthenticated `format` input enters a command executed with `shell=True`, permitting execution with application privileges. | Use an argument list with `shell=False`, allowlist formats, and require authorization. |
| 124–127 | Unsafe deserialization | CWE-502 | Attacker-controlled cookie data reaches `pickle.loads`, which can execute code during deserialization. | Replace pickle with schema-validated JSON; authenticate client-side state when integrity matters. |
| 83–88 | Template injection; XSS | CWE-1336, CWE-79 | Search input and stored titles become executable Jinja template source rather than escaped data. | Use a fixed template and pass values as template variables with autoescaping enabled. |
| 83–86 | SQL injection | CWE-89 | Interpolated search input can alter SQL semantics, bypass owner filtering, and expose database contents. | Bind both the owner ID and complete search pattern as SQL parameters; require authentication. |
| 91–97 | Missing authorization / IDOR | CWE-862, CWE-639 | Anyone can retrieve another user’s note by ID because neither authentication nor ownership is checked. | Require authentication and select notes by both note ID and authenticated owner ID. |
| 111–114 | Path traversal | CWE-22 | Untrusted download names can escape the intended directory and expose application-readable files. | Use `send_from_directory` for confinement and separately enforce attachment authorization. |
| 18, 75, 85, 105 | Known signing key | CWE-321 | A disclosed Flask signing key enables forged sessions whose `user_id` is trusted for ownership decisions. | Load a strong deployment-specific secret from protected configuration, rotate it, and invalidate existing sessions. |
| 52–53, 59–61, 70–72 | Weak password storage | CWE-916 | Fast, unsalted MD5 enables inexpensive offline password guessing after hash disclosure. | Use Argon2id or scrypt through an established password-hashing helper and migrate existing hashes. |

**Likely misses for generic data-flow analysis such as CodeQL:**

- **Note authorization, lines 91–97:** Parameterized SQL is not the problem; the missing application-specific rule—“only the owner may read this note”—usually requires custom authorization modeling.
- **Stored title-to-template flow, lines 100–105 → database → 87–88 — needs verification:** Cross-request persistence can break taint tracking unless the analyzer models database writes and reads. The direct search-input-to-template path remains independently detectable.

The remaining findings have established CodeQL query categories or analogous checks, although detection depends on the enabled suite, framework models, and version. Non-data-flow checks can identify issues such as weak hashing and hardcoded secrets; they are not inherent CodeQL blind spots.
