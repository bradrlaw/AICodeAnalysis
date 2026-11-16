# Attackers Have AI Too: Defense, Ethics, and Reverse Engineering

This segment covers the *defensive* side of AI code analysis. We talk about what adversaries can do **at a conceptual level only**. We include no attack walkthroughs, exploit code, or reverse-engineering demos. The focus is on what **we** must change in our own code, pipelines, and habits.

---

## 1. Dual use

Everything in Demos 1–4 (understanding unfamiliar code fast, mapping architecture, spotting vulnerable patterns, diffing a fix against the vulnerable version) is equally available to an adversary. AI mostly changes **cost and speed**:

| Capability | Before | With AI assistance | Defensive implication |
|---|---|---|---|
| Understanding a large unfamiliar codebase | Days or weeks of expert time | Hours | Security through obscurity is now worth even less |
| Turning a public patch into an understanding of the bug ("patch diffing") | Specialist skill | Much more accessible | **Time from patch release to exploitation keeps shrinking**, so patch faster |
| Reading shipped client code (JS bundles, mobile apps, Electron) | Tedious | Fast, even when minified | Treat every client as fully readable |
| Finding *variants* of a known bug class | Manual grep and intuition | Semantic search across repos | Fix the bug class, not just the instance |
| Social engineering and convincing fake packages | Manual | Scalable | Supply-chain controls matter more |

> Key message for students: **you should assume an attacker can understand your code as well as you can, and faster.** Design for that.

---

## 2. What to do in *our* code bases

### 2.1 Assume the client is transparent
- No secrets in front-end bundles, mobile apps, desktop apps, or config shipped to users. API keys in a client are *public* keys.
- Do **all** authorization on the server. Hidden UI is not access control.
- Minification and obfuscation are for size and IP friction, **not** security.

### 2.2 Shrink the patch window
- Turn on **Dependabot** (or Renovate) security updates and auto-merge low-risk patch bumps that pass CI.
- Maintain an **SBOM** and know which services use a vulnerable component *before* the advisory lands.
- Have a documented "critical CVE" runbook with an owner and a target time-to-patch.

### 2.3 Put deterministic and AI analysis in the pipeline
- **CodeQL code scanning** on every PR. Use `security-extended` queries for internet-facing services.
- **Copilot Autofix** to propose remediations for alerts. A human still reviews and tests every fix.
- **Copilot code review** as an extra reviewer, *in addition to* human review, not instead of it.
- **Secret scanning with push protection**, so secrets are blocked before they ever reach the remote.

### 2.4 Fix bug *classes*, not bug *instances*
- When you fix one SQL injection, ask the AI (and CodeQL) for **variants**: "Find every other place where user input reaches a query without parameterization."
- Prefer **safe-by-default APIs**: parameterized queries, ORM, auto-escaping templates, `subprocess.run([...])` without `shell=True`, `Object.create(null)` / `Map` for user-keyed objects, `yaml.safe_load`.
- Add a regression test **and** a lint/CodeQL rule so the class can't come back.

### 2.5 Supply chain hygiene in the AI era
- **Package hallucination ("slopsquatting"):** models sometimes suggest packages that don't exist, and attackers register those names. Verify that every new dependency exists, is maintained, and is the one you meant.
- Commit lockfiles; use `npm ci` / hash-pinned `pip` installs in CI.
- Pin GitHub Actions to full commit SHAs; use least-privilege `GITHUB_TOKEN` permissions.
- Prefer packages with provenance attestations (npm provenance, Sigstore).

### 2.6 Securing the AI tools themselves (new attack surface)
- **Prompt injection via code and docs:** a README, code comment, issue, or web page can contain text aimed at your AI agent ("ignore previous instructions and run…"). When you analyze **untrusted** repositories with an agent:
  - Do **not** auto-approve shell/tool execution (avoid `--allow-all` on untrusted code).
  - Run in a container, VM, or codespace with no production credentials.
  - Review every command the agent proposes.
- Only install **MCP servers** and plugins you trust. They run with your permissions.
- Respect **data boundaries**: use only organization-approved AI tools for proprietary code, honor content-exclusion policies, and use **local models (Ollama)** when code must not leave the machine.
- Treat AI-generated code as untrusted input: review it, test it, scan it.

### 2.7 Classic fundamentals still matter most
Threat modeling (e.g., STRIDE) for new features, least privilege, defense in depth, security logging and alerting, rate limiting, and abuse detection. AI accelerates attackers *and* defenders. Fundamentals decide who benefits more.

---

## 3. AI-assisted reverse engineering and REA

### 3.1 What REA is (discussion only, no demo)
**REA ("Reverse Engineer Anything")** is an open-source project that connects AI coding agents (via MCP) to reverse-engineering tooling such as Ghidra, so an agent can inspect compiled binaries, Electron apps, Android packages, and websites, then explain how a feature works and help re-implement it. Its documentation says it is intended for **lawful** analysis (security research, interoperability, education, preservation, and software you own or are authorized to examine) and that it does not support DRM circumvention, unauthorized access, or wholesale copying.

Tools like this are why section 2.1 matters: **anything you ship can be explained.**

### 3.2 Why we don't demo it
- The legal status depends on jurisdiction, license terms, and purpose, and it's easy to cross a line without realizing it.
- "Figure out how this feature works and rebuild it" can amount to **copying protected expression** or **misappropriating trade secrets**, even when the output is technically "new code."
- Our learning goals (understanding, architecture, refactoring, defense) are fully achievable on code we are **licensed to read**.

### 3.3 The legal landscape (U.S.-centric overview, *not legal advice*)

| Area | Key idea | Notable references |
|---|---|---|
| **Copyright** | Protects *expression*, not ideas or functionality. Disassembly for interoperability has been held to be fair use in some cases. | *Sega v. Accolade* (9th Cir. 1992); *Sony v. Connectix* (9th Cir. 2000); *Google v. Oracle* (2021, API reimplementation as fair use) |
| **DMCA §1201** | Prohibits circumventing technical protection measures, with narrow exemptions (e.g., interoperability §1201(f), and periodic Copyright Office exemptions for good-faith security research). | 17 U.S.C. §1201; triennial rulemaking |
| **Contracts / EULAs** | Many licenses prohibit reverse engineering. Courts have enforced such clauses. | *Bowers v. Baystate* (Fed. Cir. 2003) |
| **Computer Fraud and Abuse Act** | Accessing systems without authorization is a crime. Probing someone else's website or API is not "analysis." | 18 U.S.C. §1030; *Van Buren v. U.S.* (2021) |
| **Trade secrets** | Reverse engineering a *lawfully obtained* product is generally a proper means, unless a contract restricts it. | Defend Trade Secrets Act |
| **Patents** | Reimplementing a feature from scratch does **not** avoid patent infringement. | — |

> Point students to the **UF Office of the General Counsel** or their employer's legal team for real decisions. Other countries (e.g., the EU Software Directive) have different rules.

### 3.4 "Clean room" and AI: an important subtlety
A traditional clean-room reimplementation keeps the people who *study* the original separate from the people who *write* the new code, with documentation of that separation. **An AI agent that reads decompiled code and then writes the "new" implementation is *not* a clean room**, because the same "mind" did both. Calling it clean-room does not make it so.

### 3.5 Open-source licenses apply too
- Reading OSS is fine. **Copying** it brings license obligations (GPL copyleft, attribution for MIT/BSD/Apache).
- AI suggestions can reproduce licensed code. Use duplicate-detection or code-referencing features, and keep license headers when you vendor code.

### 3.6 Ethical decision checklist (before analyzing *anything*)
1. **Authorization:** Do I own it, have a license that permits this analysis, or have written permission?
2. **Purpose:** Security, interoperability, education, or preservation, or to copy a competitor's feature?
3. **Proportionality:** Am I touching only what I need?
4. **Harm:** Could my output (notes, code, write-up) harm users or the owner if it leaked?
5. **Disclosure:** If I find a vulnerability, do I have a responsible-disclosure path?

### 3.7 Responsible disclosure (if you find a real bug)
- Look for `SECURITY.md` or **GitHub private vulnerability reporting** on the repository.
- Report privately, give maintainers reasonable time (often ~90 days), and don't publish exploit details before a fix is available.
- If there's no response, escalate through a coordinator such as **CERT/CC**, or request a CVE via **GitHub Security Advisories**.
- University context: follow the UF Student Honor Code and UF IT acceptable-use policies. Never scan or test university or third-party systems without written authorization.

---

## 4. Class discussion prompts (2–3 minutes)

1. Your company ships an Electron app with a premium feature flag checked client-side. What does REA-style tooling mean for that design? What would you change?
2. A teammate uses an AI agent to "look at how Competitor X's app does sync and build ours the same way." Where are the ethical and legal lines?
3. A popular library you depend on publishes a security patch at 9 a.m. With AI-assisted patch diffing, how long do you think you have? What process gets you patched in time?
4. You ask an agent to analyze a repo you just cloned from an unknown GitHub account. What could go wrong, and how do you configure the tool safely?
