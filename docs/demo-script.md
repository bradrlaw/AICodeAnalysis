# Demo Cheat Sheet: AI-Assisted Code Analysis (50 min)

Everything runs in **GitHub Copilot CLI**. **VS Code** is used only to *display* results (Mermaid diagrams, SARIF, diffs). Repo root below is `C:\projects\AICodeAnalysisLecture` (`$R`).

---

## T-minus 30 minutes

```powershell
cd C:\projects\AICodeAnalysisLecture
.\scripts\demo-preflight.ps1      # everything should be green
.\scripts\reset-demos.ps1         # fresh refactoring scratch repo + empty demo-output\
```

**Screen layout** (font ≥ 20pt in terminal and VS Code; turn off notifications and Teams):

| Window | What | Open with |
|---|---|---|
| Slides | `dist\lecture.pptx` in PowerPoint, **or** `dist\lecture.html` in Edge (press **P** for presenter view) | `start dist\lecture.pptx` |
| Windows Terminal, 5 tabs | One Copilot session per demo (see each demo's **Tab** line) | Pre-open all five tabs; launch `copilot` in each, *before* class |
| VS Code | The lecture repo (`code .`) for diagrams, SARIF, and diffs | `code $R` |
| Browser | [PR #2](https://github.com/bradrlaw/AICodeAnalysis-demo-labs/pull/2/files) (Autofix) and [PR #1](https://github.com/bradrlaw/AICodeAnalysis-demo-labs/pull/1) (scale + Copilot review) | — |

**In every Copilot tab, before class:** answer the *trust this folder* prompt, run `/model` to confirm the model, then `/clear`. If it says the model is *administrator-managed*, that's expected.

> 🎤 **Running theme:** every analysis session is launched **read-only** (`--deny-tool write --deny-tool shell`). Say it out loud in Demo 1. It's the safe default for analyzing code you don't trust (prompt-injection defense, slide 30).

---

## Demo 1: Understanding (TinyDB) · 6 min · slides 15–17

**Tab 1:** `cd $R\targets\tinydb; copilot --deny-tool write --deny-tool shell`

**① Orientation (≈90 s)**
```text
I'm a new contributor. Read-only; only the tinydb/ package, ignore tests and docs.
Give me: (1) what the library does in 2 sentences, (2) a table of each module and its responsibility,
(3) the 5 most important classes with file:line, (4) 3 questions a new contributor should investigate next.
Cite file:line for every claim and label anything inferred as "inferred".
```
👉 Point out: the agent **searched and read files itself**. Mention `TinyDB.__getattr__` forwarding to the `_default` table.

**② Trace (≈90 s)**
```text
Trace step by step what happens when this runs on a fresh file, from TinyDB.__init__ until bytes are on disk:
  db = TinyDB('db.json'); db.insert({'name': 'Ada'})
Give file:line for each step. How many times is the whole file read and written per insert? What does that imply?
```
👉 Key insight: `_update_table` (`table.py:719`) **reads the whole DB and rewrites the whole file** on every write.

**③ Hidden assumptions, the "aha" (≈90 s)**
```text
Based only on the code: what does TinyDB assume about concurrency and about being the only writer to its file?
Describe a concrete scenario where two processes sharing db.json get stale results or duplicate doc_ids.
Cite the exact in-memory state that goes stale.
```
👉 Expect: per-instance `_query_cache` and `_next_id`, no file locking, and `CachingMiddleware` buffering 1000 writes (data loss on crash).
🎤 "It didn't *know* this. It *found* it because the question was pointed."

**④ Verify (≈60 s)**: Ctrl+click a cited `table.py:NNN` link (or `code -g targets\tinydb\tinydb\table.py:719`). Then:
```powershell
# in a plain terminal tab, from $R\targets\tinydb
python -c "from tinydb import TinyDB; from tinydb.storages import MemoryStorage; db=TinyDB(storage=MemoryStorage); print(db.insert({'name':'Ada'}), db.all())"
```

*Optional (only if ahead of time):* `/model`, switch models, re-ask ③, and compare. 🎤 "Different models, different answers. That's why you verify."

**Fallback:** `examples\01-understanding\recorded\` (`trace-insert.md`, `hidden-assumptions.md`, `sample-module-table.md`)

---

## Demo 2: Architecture (Express) · 6 min · slides 18–20

**Tab 2:** `cd $R; copilot --deny-tool shell` (writes allowed **with approval**, so Copilot can save diagrams to `demo-output\`)

**① Component view and patterns (≈2 min)**
```text
Read-only analysis of targets/express/lib only (Express 4.21.2; ignore examples, test, benchmarks).
Write demo-output/express-architecture.md containing:
 1. A Mermaid flowchart of the main components in lib/ and their dependencies.
 2. A table: component | file | responsibility.
 3. Design patterns you can identify, each with the file:line that proves it.
Label any pattern you could not point to in code as "inferred".
```
Approve the file write → in VS Code open `demo-output\express-architecture.md` → **Ctrl+Shift+V** (Mermaid renders).
👉 Expect: `createApplication` returns a *function* and mixes in EventEmitter (`express.js:37-43`); `req`/`res` = `Object.create(http.IncomingMessage/ServerResponse.prototype)`; patterns: Chain of Responsibility (`next()`), Composite (nested routers), Mixin, lazy init (`lazyrouter`).

**② Sequence diagram (≈2 min)**
```text
Append to demo-output/express-architecture.md a Mermaid sequenceDiagram for GET /users/42 in:
  app.use(express.json()); app.get('/users/:id', (req,res) => res.json({id:req.params.id}));
Participants: http server, app (application.js), Router (router/index.js), Layer, Route, handler.
Show how next() advances and what happens if the handler throws. Cite file:line on each arrow.
```
👉 Key: `layer.js:86` `handle_request` has a try/catch, so a sync throw becomes `next(err)`.

**③ Prove every arrow (≈1 min)**
```text
For each arrow in the sequence diagram, quote the single line of code that proves it.
Mark any arrow you cannot prove as UNSUPPORTED.
```
🎤 "Diagrams are persuasive. Make the AI prove every arrow." If anything is UNSUPPORTED, that's a *great* moment.

**④ (if time) ADR, 30 s talk only:** "Ask it *why* Express extends Node's prototypes, but demand **proven vs. inferred**. Intent isn't in the code."

**Fallback:** open `examples\02-architecture\recorded\express-architecture.md` in VS Code and press Ctrl+Shift+V (component and sequence diagrams included)

---

## Demo 3: Refactoring with guardrails · 6 min · slides 21–23

**Tab 3:** `cd $env:TEMP\legacy-invoice; copilot --allow-tool "shell(python:*)" --allow-tool "shell(git:*)"`
(created by `reset-demos.ps1`; Copilot can run tests and git freely, and **file edits still ask for approval**, so you can show each diff)
**VS Code:** `code $env:TEMP\legacy-invoice` → Source Control view.

**① Smells, flag but don't fix (≈90 s)**
```text
@invoice.py Don't modify anything yet. Table of code smells: smell | line | why it matters | Fowler refactoring.
Then list places where CURRENT behavior looks like a bug or inconsistency. Flag them as questions; don't fix them.
```
👉 Must flag: electronics `> 10` vs `>= 10` (line 29); the `SAVE10` cliff ($110 order costs more than $120); `HALFSHIP` on free shipping.

**② Show the safety net (≈30 s):** `! python -m unittest` (13 green). 🎤 "Characterization tests pin *current* behavior, quirks included."

**③ One small step (≈2.5 min)**
```text
Refactor step 1 only: replace the per-category if/elif chain in calc() with a data-driven table
(category -> threshold, comparison, rate) and reuse it in print_invoice() to remove duplication.
Preserve behavior EXACTLY, including the electronics quirk. Don't touch tax, shipping, coupons, or discount_log.
Then run python -m unittest and show me the results.
```
Approve the edit → show the diff in VS Code → tests green → `! git commit -am "step 1"`.
👉 **If the AI "fixes" the quirk**, `test_electronics_quirk_no_discount_at_exactly_10` fails. 🎤 **Best possible outcome.** "Refactor means no behavior change. The test caught it."

**④ Scale (≈1 min, talk over a recorded output):** Bottle is one 4,680-line file. Show `examples\03-refactoring\recorded\bottle-plan.md` (scroll to **§5 Recommendation**). 🎤 "Its answer to *should we split it?* is **no**: copy-one-file deployment is a product feature, not tech debt. Architecture is trade-offs."

---

## Demo 4: Vulnerabilities · 8 min · slides 24–27

### A. AI review and the chain (≈2 min)

**Tab 4:** `cd $R\labs\vuln-notes-express; copilot --deny-tool write --deny-tool shell`
```text
@server.js Defensive review only; don't write exploit payloads.
Table sorted by severity: line | weakness | CWE | why it matters (1 sentence) | fix.
Then identify CHAINS where two individually-minor issues combine into a serious one.
Mark low-confidence findings "needs verification".
```
👉 Look for **merge() prototype pollution (line 22) → `user.isAdmin` check (line 46) = authorization bypass**. Compare with `labs\vuln-notes-express\ANSWER_KEY.md`.
**Fallback:** `examples\04-vulnerabilities\recorded\express-review.md` (it found the chain) and `flask-review.md` (it found the IDOR)

### B. CodeQL, the deterministic baseline (≈2 min)

VS Code: open `express.sarif` (SARIF Viewer panel opens) → click results to jump to code. *(Pre-built; show the command on the slide or in the terminal, don't run it live.)*
```powershell
codeql database analyze codeql-db-express codeql/javascript-queries:codeql-suites/javascript-security-extended.qls --format=sarif-latest --output=express.sarif
```
**Actual CodeQL 2.27.4 results** (15 alerts):

| Lab | CodeQL found | CodeQL missed (AI/human must catch) |
|---|---|---|
| Express | XSS 35 · prototype pollution 25/28 · path injection 53 · command injection 57 · ReDoS 64/65 · open redirect 75 · missing rate limiting · remote property injection | Hard-coded key (E1) · **`isAdmin` authz chain (E4)** · `Math.random` token (E8) |
| Flask | SQLi 85 · template injection 88 · path injection 114 · command injection 120 · unsafe deserialization 127 · debug 133 · weak hashing 53 | Hard-coded secret · **IDOR** · missing auth · CSRF · stored XSS |

Back in **Tab 4**:
```text
@../../express.sarif For each CodeQL result, explain the source -> sink path in one line and mark it true or false positive.
Then: which vulnerabilities in server.js did CodeQL NOT report, and why would a data-flow analyzer miss them?
```
🎤 "CodeQL is the gate, AI does the triage and catches the missing logic, and humans decide."

### C. In the PR workflow, on GitHub (≈1.5 min)

Two PRs in `bradrlaw/AICodeAnalysis-demo-labs`, each with a different job:

| PR | Contents | Use it to show |
|---|---|---|
| [**#2**](https://github.com/bradrlaw/AICodeAnalysis-demo-labs/pull/2) *Add order lookup and receipt endpoints* | 2 vulns (SQLi, command injection) | **Inline CodeQL comments and Copilot Autofix** suggestions on the diff |
| [**#1**](https://github.com/bradrlaw/AICodeAnalysis-demo-labs/pull/1) *Add notes and settings features* | Both full labs, 22 alerts | **Scale:** with >20 alerts CodeQL posts one summary, not inline comments. Also **Copilot code review** |

1. **PR #2 → Files changed:** inline CodeQL comment on `flask-app/app.py` line 26 → the Autofix suggestion (parameterized query). Show the diff; *don't commit* (keep the demo reusable).
   - If no suggestion is shown inline, click **Show more details** → alert page → **Generate fix** (takes ~30 s; do it before class). This is web-UI only; the REST autofix API only works for default-branch alerts. Preflight shows a yellow `[WARN]` until it exists.
2. **PR #1 → Checks:** CodeQL failed with 22 new alerts. Same results as our local SARIF.
3. **PR #1 → Conversation → Copilot review** (already requested and posted: 20 issues). Scroll its summary and point at the ones **CodeQL missed**: *"Note lookup exposes private bodies without … ownership checks"* (IDOR), *"Recursive merge allows prototype pollution and admin bypass"* (the chain), hard-coded signing key, CSRF. It did **not** flag the `Math.random` reset token. 🎤 "Neither tool is complete. Layer them."
   - To re-run: Reviewers ⚙ → **Copilot** → re-request (1–3 minutes).

🎤 "This caught it *before merge*. That's where you want it."

### D. Real CVE: incomplete fix and variant analysis (≈2.5 min)

**Tab 5:** `cd $R` (plain PowerShell first)
```powershell
git diff --no-index targets\minimist-1.2.5\index.js targets\minimist-1.2.6\index.js
.\scripts\minimist-regression.ps1      # upstream regression tests: 1.2.5 → 2 RED; 1.2.6 → all GREEN
```
🎤 "1.2.5 *already* had a `__proto__` guard. It missed paths through a function's `constructor`. That's an incomplete fix."

Then `copilot --deny-tool write --deny-tool shell`:
```text
@targets/minimist-1.2.6/index.js Here is the upstream fix for CVE-2021-44906 (isConstructorOrProto).
Defensive analysis only: explain in 3 bullets what bug class it closes and whether any risk remains.
Then search labs/ for OTHER functions that recursively assign user-controlled keys, i.e., variants of the same bug class.
```
👉 Expect it to find `merge()` in `labs/vuln-notes-express/server.js`. 🎤 **"Fix the class, not the instance."**

*(requests CVE-2023-32681 is take-home. Mention it in one sentence: "unguided 'find bugs' misses it; a threat-model prompt finds it.")*

---

## Part 8 and close · 8 min · slides 28–38
No demos. Pick **one** discussion question (slide 34). Watch the clock: stop Q&A at 0:50.

---

## If things go wrong

| Problem | Do this |
|---|---|
| Copilot slow or rate-limited | Switch to the `recorded\` output for that demo; keep talking over it |
| Agent asks for a permission you didn't expect | Read it aloud. That *is* the safety lesson. Deny if unsure. |
| Wrong or hallucinated answer | 🎉 Teachable moment: "Let's verify." Open the cited line. |
| Mermaid doesn't render | Paste the Mermaid block into https://mermaid.live |
| Running long | Cut in this order: Demo 2 ③/④ → Demo 1 ④ → Demo 4 B triage prompt → Demo 3 ④ |
| `codeql` not found | New terminal (PATH), or `& "$env:LOCALAPPDATA\codeql-bundle\codeql\codeql.exe"` |

---

## Prep reference

### Prep: CodeQL (already done; repeat only if labs change)
```powershell
cd $R
codeql database create codeql-db-flask   --language=python                --source-root=labs\vuln-notes-flask   --overwrite
codeql database create codeql-db-express --language=javascript-typescript --source-root=labs\vuln-notes-express --overwrite
codeql database analyze codeql-db-flask   codeql/python-queries:codeql-suites/python-security-extended.qls         --format=sarif-latest --output=flask.sarif
codeql database analyze codeql-db-express codeql/javascript-queries:codeql-suites/javascript-security-extended.qls --format=sarif-latest --output=express.sarif
```
CodeQL bundle 2.27.4 is installed at `%LOCALAPPDATA%\codeql-bundle\codeql` (on the user PATH, with query packs included, so no download is needed).

### Prep: GitHub (already done)
- Repo: **bradrlaw/AICodeAnalysis-demo-labs** (public). `main` = safe starter apps. **PR #1** (`feature/notes-and-settings`) adds both vulnerable labs. **PR #2** (`feature/order-lookup`) adds two small vulns for inline Autofix.
- Code scanning: CodeQL default setup, `extended` suite. Secret scanning and push protection are on. Copilot Autofix is on by default with CodeQL.
- **Never merge either PR.** If you commit an Autofix during a rehearsal, reset the branch from a clone: `git push --force origin <original-sha>:<branch>`.

### Prep: fallbacks (recorded; re-record during rehearsal if you like)
Already recorded with Copilot CLI into `examples\0N-*\recorded\`. To re-record one non-interactively:
```powershell
[Console]::OutputEncoding = [Text.Encoding]::UTF8   # otherwise output is garbled (cp437)
cd $R\targets\tinydb
copilot -p "<prompt text>" --deny-tool write --deny-tool shell --no-color | Set-Content -Encoding utf8 ..\..\examples\01-understanding\recorded\trace.md
```

### Why no npm/pip for the vulnerable versions?
The internal package proxies may block known-vulnerable versions (minimist 1.2.5, requests 2.30.0). All analysis targets are **git clones of tagged releases** (`scripts\setup-targets.ps1`), so no package manager is involved. Only current, non-vulnerable packages come through npm/pip (Express 4.21.x for the lab, Flask 3.1 in `.venv`, `tape`, and Marp).
