# Examples & Prompt Library

Each folder is one lecture demo. It contains the **goal**, **setup**, **progressive prompts** (copy-paste ready), **what a good answer contains** (an answer key you can check AI output against), and **pitfalls to call out live**.

| # | Folder | Theme | Primary target | Tools |
|---|--------|-------|----------------|-------|
| 1 | [01-understanding](01-understanding/README.md) | Understand an unfamiliar codebase | TinyDB (Python) | Copilot CLI, Ollama |
| 2 | [02-architecture](02-architecture/README.md) | Extract architecture & design | Express (JS), Flask (Python) | Copilot Chat (VS Code), Copilot CLI |
| 3 | [03-refactoring](03-refactoring/README.md) | Refactor safely | `labs/legacy-invoice`, Bottle | Copilot CLI / Chat, unittest |
| 4 | [04-vulnerabilities](04-vulnerabilities/README.md) | Find & fix vulnerabilities | `labs/vuln-notes-*`, minimist, requests | Copilot CLI, CodeQL, Copilot code review & Autofix |
| 5 | [05-local-models](05-local-models/README.md) | Private/offline analysis | All of the above | Ollama |

First run `.\scripts\setup-targets.ps1` to clone the pinned targets into `targets\`.

---

## The SCOPE-E prompt pattern

Analysis prompts fail in predictable ways: too vague, no boundaries, unverifiable output. Every prompt in this repo follows **SCOPE-E**:

| Letter | Meaning | Example fragment |
|---|---|---|
| **S**ituation | Who you are, what you're trying to accomplish | "I'm new to this repo and need to fix a bug in query caching." |
| **C**onstraints | What the AI must *not* do; boundaries | "Do not modify files. Only consider `tinydb/`. Ignore tests." |
| **O**bjective | One clear, concrete task | "Trace what happens when `db.insert()` is called." |
| **P**roduct format | Shape of the output | "Numbered steps, ≤ 15 lines, then a Mermaid sequence diagram." |
| **E**vidence | Demand proof and honesty | "Cite `file:line` for every claim. List what you're unsure about." |

> **Rule:** If an AI claim has no citation, treat it as a hypothesis, not a fact.

### Reusable template

```text
Situation: <who/why>.
Constraints: Read-only — do not modify files. Scope: <dirs>. <other limits>.
Objective: <single concrete task>.
Product: <format: bullets / table / Mermaid / patch>, <length limit>.
Evidence: Cite file:line for every claim. If you infer rather than read something,
label it "inferred". End with a list of open questions or uncertainties.
```

---

## Running prompts with each tool

### GitHub Copilot CLI (agentic, terminal)

```powershell
cd targets\tinydb
copilot                          # interactive; use @path to attach files, /model to pick a model
# Use plan mode (Shift+Tab) for "analyze, don't change anything" sessions.
```

Non-interactive (good for recording fallbacks):

```powershell
# Read-only analyst: deny file writes and shell so the agent can only read and reason
copilot -p "<prompt>" --deny-tool write --deny-tool shell > ..\..\examples\01-understanding\recorded\orientation.md
```

Built-in reviews on your own changes: `/review` (code review) and `/security-review` (security review of staged/unstaged changes or the branch diff).

> ⚠️ When analyzing **untrusted** code, never use `--allow-all` / `--yolo`. Repository text can contain prompt-injection aimed at your agent. See [docs/ethics-and-defense.md §2.6](../docs/ethics-and-defense.md).

### Copilot Chat in VS Code

Open the target folder as the workspace. Use **Ask** mode for analysis and reference context explicitly with `#codebase`, `#file`, or `#selection`. Use **Agent** or **Edit** mode only for refactoring demos.

### Copilot code review & Copilot Autofix (GitHub.com)

Push a lab to a throwaway repo, enable **Code scanning (CodeQL default setup)**, and open a PR. Request **Copilot** as a reviewer. CodeQL alerts show a **Generate fix** button (Autofix).

### CodeQL CLI (deterministic static analysis)

See [04-vulnerabilities](04-vulnerabilities/README.md#codeql) for exact commands.

### Ollama (local model)

See [05-local-models](05-local-models/README.md).

---

## Verification habits to model on stage

1. **Spot-check citations.** Open 2–3 cited lines live. Did the code say what the AI said?
2. **Ask for disconfirming evidence.** "What in the code would prove your explanation wrong? Go check."
3. **Run something.** Tests, a REPL snippet, CodeQL. Deterministic tools are the source of truth.
4. **Cross-examine with a second model or a fresh session.** Disagreements point at the claims you should verify.
5. **Save outputs** to `recorded/` folders so you have a fallback and can show model-to-model differences.
