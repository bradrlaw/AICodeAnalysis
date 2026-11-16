# Instructor Answer Key: vuln-notes-flask

> Hide this file from students before the exercise (e.g., don't push it to the student copy).
> CWE references are from [cwe.mitre.org](https://cwe.mitre.org). Line numbers refer to `app.py`.

| # | Location | Issue | CWE | Severity | Remediation |
|---|----------|-------|-----|----------|-------------|
| F1 | `app.config["SECRET_KEY"] = "dev-secret-123"` | Hard-coded secret. Anyone who reads the repo can forge session cookies (and with them `user_id`). | CWE-798 | High | Load from environment or a secrets manager; fail fast if missing; rotate. |
| F2 | `hash_password()` | Unsalted MD5 password hashing | CWE-916 / CWE-328 | High | `werkzeug.security.generate_password_hash` / `check_password_hash` (scrypt/pbkdf2), or `argon2-cffi`. |
| F3 | `list_notes()` f-string SQL | SQL injection via `q` (and `user_id` interpolation) | CWE-89 | Critical | Parameterized query: `... WHERE owner_id = ? AND title LIKE ?`, `(uid, f"%{q}%")`. |
| F4 | `render_template_string(f"...{q}...")` | **Server-side template injection**: user input becomes Jinja *template source*. Can lead to remote code execution. | CWE-1336 / CWE-94 | Critical | Never build templates from input. Use `render_template_string("<h1>Results for {{ q }}</h1>...", q=q, rows=rows)` or a template file. |
| F5 | `items = "".join(f"<li>...{r['title']}...")` | Stored XSS. Note titles are inserted without escaping. | CWE-79 | High | Let Jinja autoescape (pass `rows` to the template) or `markupsafe.escape`. |
| F6 | `get_note()` | IDOR / missing authorization. Any (even anonymous) user can read any note by id. | CWE-639 / CWE-862 | High | Require login; `WHERE id = ? AND owner_id = ?`; return 404 when not owned. |
| F7 | `list_notes()`, `create_note()` | Missing authentication. `session.get('user_id')` may be `None`. | CWE-306 | Medium | `login_required` decorator. |
| F8 | `download_attachment()` | Path traversal (`name=../app.py`) | CWE-22 | High | `flask.send_from_directory(ATTACHMENTS_DIR, name)` or `werkzeug.utils.safe_join`; also authz on attachments. |
| F9 | `export_notes()` | OS command injection via `format` with `shell=True` | CWE-78 | Critical | Allow-list formats (`{"zip","tar"}`), `subprocess.run([...], shell=False)`, or use Python's `zipfile`/`tarfile`. |
| F10 | `preferences()` | Insecure deserialization: `pickle.loads` on a client cookie leads to RCE | CWE-502 | Critical | Store prefs server-side or in signed JSON (`itsdangerous` / Flask `session`); never unpickle untrusted data. |
| F11 | `app.run(debug=True)` | Werkzeug debugger exposes an interactive console | CWE-489 / CWE-215 | High (if exposed) | Drive debug from env; never enable in production. |
| F12 | All POST routes | No CSRF protection | CWE-352 | Medium | Flask-WTF `CSRFProtect`, `SameSite` cookies. |

## Teaching notes

- **Chains matter.** F1 lets an attacker forge `session["user_id"]`, which makes F6 and F7 trivially worse. Ask students: *"Which single fix reduces the most risk?"*
- **What tools tend to catch:**
  - **Actual run (CodeQL 2.27.4, `python-security-extended`, 7 alerts):** F2 `py/weak-sensitive-data-hashing` (L53) · F3 `py/sql-injection` (L85) · F4 `py/template-injection` (L88) · F8 `py/path-injection` (L114) · F9 `py/command-line-injection` (L120) · F10 `py/unsafe-deserialization` (L127) · F11 `py/flask-debug` (L133).
  - **CodeQL did NOT report:** F1 (hard-coded secret; secret scanning's job), F5 (stored XSS: the tainted source is the database, not the request), F6/F7 (missing authorization/authentication), F12 (CSRF). These are what AI review and humans must catch.
  - AI review usually finds the authorization problems (F6, F7) and the "chain" story that static analysis misses, but may **miss** issues or invent ones (e.g., claiming `/register` is SQL-injectable even though it's parameterized). **Use that as a teaching moment.**
- **Actual Copilot code review** (PR #1 in the demo repo): flagged F1, F2, F3, F4, F6, F7, F8, F9, F10, F11, and F12. That includes the IDOR and CSRF CodeQL missed.
