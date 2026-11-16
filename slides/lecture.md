---
marp: true
theme: default
paginate: true
size: 16:9
title: AI-Assisted Code Analysis
description: Using AI tools and models to understand, document, refactor, and secure codebases
style: |
  section { font-size: 26px; }
  section.lead h1 { font-size: 56px; }
  section.small { font-size: 21px; }
  code, pre { font-size: 0.78em; }
  table { font-size: 0.8em; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2em; }
  .muted { color: #666; }
  .warn { color: #b00020; font-weight: bold; }
  footer { color: #888; }
footer: AI-Assisted Code Analysis · University of Florida
---

<!-- _class: lead -->
<!-- _paginate: false -->

# AI-Assisted Code Analysis
## Understanding, Architecture, Refactoring & Security, with AI as a power tool, not an oracle

<br>

**Brad Lawrence** · Principal Architect, Microsoft
University of Florida · [Date]

<!--
Welcome. 50 minutes: about half concepts, half live demos. All prompts and code are in the course repo, so students don't need to copy anything down.
-->

---

# Monday morning

> You've just joined a team. You own a **50,000-line** service you've never seen.
> There's a **security advisory** for one of its dependencies.
> Your lead wants a **design doc** by Friday.

**Question:** what do you do in the first hour?

<!--
Hook: ask for a show of hands. Who would read the README? grep? Ask a teammate? Ask an AI?
Today: how to make "ask an AI" a rigorous engineering practice, not a gamble.
-->

---

# Agenda (50 min)

| | Segment | Min |
|---|---|--:|
| 1 | How AI "reads" code | 6 |
| 2 | The toolbox | 4 |
| 3 | Prompting for analysis: **SCOPE-E** | 4 |
| 4 | Demo: **Understanding** (TinyDB) | 6 |
| 5 | Demo: **Architecture** (Express / Flask) | 6 |
| 6 | Demo: **Refactoring** with guardrails | 6 |
| 7 | Demo: **Vulnerabilities**, find and fix | 8 |
| 8 | Attackers have AI too · **Ethics & REA** | 5 |
| 9 | Takeaways · Q&A | 3+ |

---

# Learning objectives

By the end you should be able to:

1. Explain **how** AI tools see a codebase, and why that predicts where they fail
2. Write **evidence-demanding** prompts for analysis tasks
3. Pair AI with **deterministic tools** (tests, CodeQL) so you *verify*, not trust
4. Describe what **defenders** must do now that attackers have the same tools
5. Reason about the **ethics and law** of AI-assisted reverse engineering

---

<!-- _class: lead -->

# Part 1
## How AI "reads" code

---

# An LLM never "sees" your repo, only its **context window**

<div class="cols">
<div>

**What fits in context**
- System and custom instructions (`AGENTS.md`, `copilot-instructions.md`)
- Your prompt and the conversation so far
- Files you attach (`@file`, `#file`)
- Results of **tool calls** the agent makes: grep, file reads, test output

</div>
<div>

**What doesn't**
- The other 49,000 lines it never opened
- Runtime state, config in prod, data
- Anything newer than its training data, unless it reads it

</div>
</div>

> **Corollary:** answer quality ≈ model quality × **context quality**

<!--
Context windows today are large (hundreds of thousands of tokens), but repos are larger, and "lost in the middle" effects mean more context is not always better context.
-->

---

# Three ways tools gather context

| Approach | How it works | Example | Failure mode |
|---|---|---|---|
| **Paste / attach** | You choose the files | Ollama + `Get-Content` | You forget the important file |
| **Retrieval (RAG)** | Index + semantic search pulls relevant chunks | VS Code `#codebase` | Misses relationships across chunks |
| **Agentic** | Model calls tools in a loop: search → read → run → reason | Copilot CLI, Agent mode | Wanders, costs tokens, **acts** on untrusted input |

Modern tools combine all three.

---

# Why AI analysis goes wrong

- **Hallucinated specifics:** wrong line numbers, nonexistent functions, made-up APIs
- **Version drift:** describes the library *from training memory*, not *this* version
- **Plausible-but-wrong narratives:** confident explanations of intent with no evidence
- **Silent omissions:** "no issues found" ≠ no issues
- **Sycophancy:** agrees with the premise in your question
- **Non-determinism:** run it twice, get two answers

> 🔑 **Treat every claim as a hypothesis until it's tied to a line of code or a passing test.**

---

<!-- _class: lead -->

# Part 2
## The toolbox

---

# Tools we'll use today

| Tool | Mode | Best for | Watch out for |
|---|---|---|---|
| **GitHub Copilot CLI** | Agent in the terminal | Repo-wide exploration, traces, running tests, scripted `-p` runs | Tool permissions on untrusted code |
| **Copilot Chat (VS Code)** | IDE chat: Ask / Edit / Agent | Visual work: diagrams, diffs, selections | Context limited to what's referenced |
| **Copilot code review & Autofix** | On GitHub PRs | Team workflow, fixes for CodeQL alerts | Suggestions still need review |
| **CodeQL** | Deterministic static analysis | Taint tracking, CI gate, variant queries | Misses logic and authorization flaws |
| **Ollama (local models)** | Offline chat/API | Private code, no data leaves the laptop | Smaller models, manual context |

---

# Data boundaries matter

- **Know where your code goes.** Use org-approved tools; respect content-exclusion policies.
- **Proprietary or regulated code** → enterprise tools with data protections, or **local models**
- **Never paste secrets** into any prompt
- **Open-source code** (today's targets) → fine to analyze, but **licenses still apply** to anything you copy

---

<!-- _class: lead -->

# Part 3
## Prompting for analysis: **SCOPE-E**

---

# SCOPE-E: a prompt pattern for analysis

| | | Example |
|---|---|---|
| **S** | **Situation:** who you are, why | "I'm new here and need to fix a caching bug." |
| **C** | **Constraints:** limits and scope | "Read-only. Only `lib/`. Ignore tests." |
| **O** | **Objective:** one concrete task | "Trace what `db.insert()` does." |
| **P** | **Product:** output format | "Numbered steps + Mermaid sequence diagram." |
| **E** | **Evidence:** proof and honesty | "Cite `file:line`. Mark inferences. List unknowns." |

> If a claim has no citation, it's a **hypothesis**.

---

<!-- _class: small -->

# Bad prompt → good prompt

<div class="cols">
<div>

❌ **Vague**
```text
Explain this codebase.
```
Gets you a README-style summary, possibly of a *different version*, with nothing you can check.

</div>
<div>

✅ **SCOPE-E**
```text
Situation: New contributor, need a mental model.
Constraints: Read-only. Only tinydb/.
Objective: Orientation map.
Product: module table; top 5 classes;
  Mermaid dependency diagram.
Evidence: file:line for every claim;
  label inferences; end with 3 open questions.
```

</div>
</div>

**Broad → narrow → verify:** orientation → trace one operation → probe one mechanism → check citations

---

<!-- _class: lead -->

# Demo 1
## Understanding an unfamiliar codebase
### TinyDB v4.8.0 · Python · ~2.3k LOC

`examples/01-understanding`

---

# Demo 1: what to watch for

1. **Orientation map:** modules, key classes, layered diagram
2. **Trace** `db.insert({'name': 'Ada'})` from `TinyDB.__init__` to bytes on disk
3. **Probe** how `Query().name == 'Ada'` becomes an executable, cacheable test
4. **Hidden assumptions:** "What breaks if two processes share `db.json`?"
5. **Verify:** open two cited lines and run a one-liner

<span class="muted">Optional: same question to a local model via Ollama. Compare.</span>

<!--
Live in Copilot CLI, plan mode. Expected insight from step 2: every insert reads and rewrites the ENTIRE file. From step 4: the query cache and _next_id are per-instance, so a second writer leads to stale results and duplicate IDs; no file locking. The AI didn't "know" this; it found it because the question was pointed.
Fallback: examples/01-understanding/recorded/
-->

---

# Demo 1: takeaways

- **Pointed questions find real insights**; generic ones produce summaries
- Agents **navigate**: they found `__getattr__` forwarding we didn't mention
- **Citations let you verify in seconds**, so always ask for them
- Local model: good on the file you gave it, **blind to everything else**

---

<!-- _class: lead -->

# Demo 2
## Extracting architecture & design
### Express 4.21.2 (JS) · Flask 3.0.3 (Python)

`examples/02-architecture`

---

# Demo 2: from code to design artifacts

1. **Component view:** Mermaid diagram plus responsibility table for `lib/`
2. **Sequence diagram:** `GET /users/42` through app → Router → Layer → Route → handler
3. **Design patterns,** each with evidence: middleware *Chain of Responsibility*, *Composite* routers, *Mixin* app, prototype extension of `req`/`res`
4. **ADR:** *why* extend Node's objects via prototypes? **Proven vs. inferred**
5. **Verify the diagram:** "quote the line that proves each arrow, or delete it"

<!--
Use VS Code Copilot Chat in Ask mode with #codebase so Mermaid renders.
Key facts: express.js createApplication returns a function and mixes in EventEmitter + application proto; request.js/response.js are Object.create(http.IncomingMessage/ServerResponse.prototype); router/index.js next() loop; layer.js handle_request try/catch → next(err).
Version-drift trap: models often describe Express 5 router layout.
-->

---

# Demo 2: takeaways

- AI is **excellent at first drafts** of diagrams and docs
- Diagrams are **persuasive**, so make the AI **prove every arrow**
- **Intent isn't in the code.** Separate *what the code shows* from *why we think they did it*
- Turn the architecture into **fitness functions** (automated dependency rules) so it stays true

---

<!-- _class: lead -->

# Demo 3
## Refactoring with guardrails
### `labs/legacy-invoice` · Bottle (4,680-line single file)

`examples/03-refactoring`

---

# The safe refactoring loop

```text
 Understand → Pin behavior (characterization tests) → ONE small AI step
     ↑                                                      ↓
     └───────────── Commit ← Run tests + review diff ←──────┘
```

- **Refactor = change structure, *not* behavior**
- AI loves to "improve" behavior along the way. **The tests catch it.**
- Small steps → diffs a human can actually review

---

# Demo 3: watch for the trap

1. **Smell inventory:** long method, duplication, magic numbers, global state
2. **Flag behavior questions without fixing them:**
   - Electronics bulk discount uses `> 10`; everything else uses `>= 10`
   - A $110 order with `SAVE10` costs *more* than a $120 one
3. **One step:** data-driven discount table, run tests, read the diff
4. **Behavior changes go in a separate, explicit PR** with the test changes visible

**At scale:** ask the AI to *plan* splitting `bottle.py`, including whether you *should*

<!--
If the AI "fixes" the electronics quirk, test_electronics_quirk_no_discount_at_exactly_10 fails. That's the moment.
Bottle is single-file by design (easy vendoring). The best answer to "should we?" is "probably not." Architecture = trade-offs.
-->

---

<!-- _class: lead -->

# Demo 4
## Finding & remedying vulnerabilities
### Lab apps · CodeQL · Copilot Autofix · real CVEs

`examples/04-vulnerabilities`

---

# AI review and static analysis are complementary

| | **CodeQL** | **AI review** |
|---|---|---|
| Finds | Tainted data flow: SQLi, XSS, command injection, path traversal, unsafe deserialization | Missing authz/IDOR, CSRF, **chained** issues, business logic |
| Strength | Precise, repeatable, a CI gate | Explains, prioritizes, writes fixes |
| Weakness | Blind to *missing* logic | Misses and invents; varies per run |

**Use both:** CodeQL as the gate, AI for triage and remediation, humans for the decision

---

# Demo 4: flow

1. **AI review** of `vuln-notes-express`, then find the **chain**:
   prototype pollution in `merge()` → `user.isAdmin` authorization bypass
2. **CodeQL** results (pre-built DB) → *"Which issues did CodeQL miss, and why?"*
3. **Copilot Autofix** on a GitHub alert, and **Copilot code review** on the PR
4. **Real CVE:** minimist 1.2.5 (CVE-2021-44906)
   - It *already* blocked `__proto__`… but not `constructor.prototype`
   - Compare the AI's fix with the **upstream fix**
   - **Variant analysis:** "Find everything shaped like this in *our* code"

<!--
Defensive scope: our lab code + publicly disclosed, already-fixed CVEs. We explain, fix, and regression test. No exploit development.
requests CVE-2023-32681 is the take-home: unguided "find bugs" usually misses it; a threat-model-guided prompt finds it. Lesson: threat model first, then prompt.
-->

---

# Demo 4: takeaways

- **"No issues found" is not a security guarantee**
- **Fix the class, not the instance.** Incomplete fixes cause follow-up CVEs
- **Threat model first, then prompt.** AI finds what you point it at
- **Autofix is a suggestion.** Review, test, and re-scan
- Add a **regression test** *and* a **rule** so the bug can't come back

---

<!-- _class: lead -->

# Part 8
## Attackers have AI too
### …so what do *we* change?

---

# Same capabilities, different intent

Everything we just did helps **adversaries** too. Mostly it changes **cost and speed**:

- Understanding unfamiliar code: **weeks → hours**
- Turning a public patch into an understanding of the bug: **specialist skill → accessible**
- Reading shipped JS bundles, mobile and desktop apps: **tedious → fast**
- Finding *variants* of known bugs: **manual → semantic search**

> Assume an attacker can understand your code **as well as you can, and faster.**

<span class="muted">We discuss this at a conceptual level only; no attack techniques today.</span>

---

<!-- _class: small -->

# Defend: what to do in *our* code bases

<div class="cols">
<div>

**Design**
- **Assume the client is transparent:** no secrets in bundles or apps; all authz on the server
- Obfuscation is **not** security
- Threat model new features (STRIDE)
- Safe-by-default APIs: parameterized queries, autoescaping, no `shell=True`, `Map` / `Object.create(null)`

**Pipeline**
- CodeQL on every PR · Copilot Autofix · AI review **plus** human review
- Secret scanning **with push protection**

</div>
<div>

**Patch velocity**
- Dependabot / Renovate, SBOM, a critical-CVE runbook
- The window from patch to exploitation is **shrinking**

**Supply chain**
- Verify AI-suggested packages exist (**slopsquatting**)
- Lockfiles, pinned Action SHAs, provenance

**The AI tools themselves**
- **Prompt injection** hides in READMEs, comments, issues
- Don't `--allow-all` on untrusted repos; sandbox it
- Trust MCP servers and plugins like any dependency

</div>
</div>

---

# AI-assisted reverse engineering: REA

**REA ("Reverse Engineer Anything")** connects AI agents (via MCP) to RE tooling such as Ghidra to inspect **binaries, Electron apps, APKs, and websites**, and explain or rebuild features.

- Its own docs: for **lawful** use (security research, interoperability, education, preservation, software you own or are authorized to examine). **Not** for DRM circumvention, unauthorized access, or wholesale copying.
- **We will not demo it.** Our goals are achievable on code we're licensed to read.
- Defensive lesson: **anything you ship can be explained.** Design accordingly.

---

<!-- _class: small -->

# Ethics, IP & the law (U.S. overview, *not legal advice*)

| Area | Key point |
|---|---|
| **Copyright** | Protects expression, not ideas; interoperability disassembly has been fair use in some cases (*Sega v. Accolade*, *Sony v. Connectix*) |
| **DMCA §1201** | Don't circumvent protection measures; narrow exemptions exist (interoperability, good-faith security research) |
| **EULAs** | Anti-RE clauses are often enforceable (*Bowers v. Baystate*) |
| **CFAA** | Probing systems you're not authorized to access is a crime |
| **Trade secrets / patents** | RE of lawfully obtained products may be proper means, but **rebuilding a feature doesn't avoid patents** |

**"Clean room" with AI?** If the same agent reads the decompiled code *and* writes the "new" code, **it is not a clean room.**

---

# Before you analyze anything: the checklist

1. **Authorization:** do I own it, have a license, or have written permission?
2. **Purpose:** security, interoperability, or education, or copying a competitor?
3. **Proportionality:** am I touching only what I need?
4. **Harm:** what if my notes or code leaked?
5. **Disclosure:** found a bug? `SECURITY.md` → private report → ~90 days → CVE

UF context: Student Honor Code and UF IT acceptable-use policy. **No testing of systems without written authorization.**

---

# Discussion (pick one)

1. Your Electron app checks a **premium feature flag client-side**. What does REA-style tooling mean for that design?
2. A teammate asks an agent to *"see how Competitor X does sync and build ours the same way."* Where are the lines?
3. A dependency ships a security patch at **9 a.m.** How long do you have? What process gets you patched?
4. You point an agent at a repo cloned from an **unknown account**. What could go wrong?

---

<!-- _class: lead -->

# Takeaways

---

# Seven things to remember

1. **Context is everything:** the AI only knows what it reads
2. **SCOPE-E prompts**, especially the **E**: cite `file:line`, label inferences
3. **Broad → narrow → verify**
4. **Tests before refactors**; small steps; behavior changes in the open
5. **AI + CodeQL + humans**: complementary, not substitutes
6. **Fix the class, not the instance**; patch fast; the client is transparent
7. **Authorization and licenses first**: powerful tools, ethical use

---

# Resources

- **Course repo:** all prompts, labs, answer keys → `examples/`, `labs/`, `docs/`
- GitHub Copilot CLI docs · Copilot code review · Copilot Autofix
- CodeQL: `codeql.github.com` · query suites `*-security-extended`
- OWASP Top 10 · CWE Top 25 · OWASP Juice Shop · OWASP PyGoat
- Ollama: `ollama.com/library`
- Fowler, *Refactoring* (2nd ed.) · Feathers, *Working Effectively with Legacy Code*
- Nygard, *Documenting Architecture Decisions* (ADRs)

**Take-home:** pick a library from `docs/library-recommendations.md` → cited architecture doc + diagram + safe refactor PR + reflection

---

<!-- _class: lead -->
<!-- _paginate: false -->

# Questions?

**Brad Lawrence** · Principal Architect, Microsoft
brad.lawrence@microsoft.com

<span class="muted">Slides and examples: github.com/bradrlaw/AICodeAnalysis</span>
