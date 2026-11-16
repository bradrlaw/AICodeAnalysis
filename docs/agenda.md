# Lecture Agenda — AI-Assisted Code Analysis (50 minutes)

**Audience:** University of Florida undergraduate / graduate CS students
**Format:** Slides (Marp) + live demos with pre-recorded fallbacks
**Featured tools:** GitHub Copilot CLI · Copilot Chat in VS Code · Copilot code review & Autofix · CodeQL · Local models via Ollama
**Languages:** Python and JavaScript/TypeScript

## Learning objectives

By the end of the lecture students should be able to:

1. Explain *how* AI tools "see" a codebase (context windows, retrieval, agents/tools) and why that drives both their strengths and their failure modes.
2. Write structured, evidence-demanding prompts for **understanding**, **architecture extraction**, **refactoring**, and **vulnerability analysis**.
3. Combine AI with deterministic tools (tests, linters, CodeQL) so AI output is *verified*, not trusted.
4. Describe how attackers can use the same AI capabilities and what defenders must do in their own code and pipelines.
5. Reason about the ethics and legality of AI-assisted reverse engineering (e.g., REA) and respect IP and licensing.

## Timeline

| Time | Min | Segment | Slides / Demo | Materials |
|------|----:|---------|---------------|-----------|
| 0:00 | 2 | **Hook & intro** — "You just inherited 50k lines of code. Monday." | Title, hook | — |
| 0:02 | 6 | **How AI reads code** — tokens & context windows, retrieval/indexing, agentic tool use, hallucination & confident wrongness | Concepts | — |
| 0:08 | 4 | **The toolbox** — CLI agent vs IDE chat vs PR review vs static analysis vs local models; data-privacy trade-offs | Tool matrix | — |
| 0:12 | 4 | **Prompting for analysis** — the *SCOPE-E* prompt pattern (Situation, Constraints, Objective, Product format, Evidence) | Prompt anatomy | [examples/README.md](../examples/README.md) |
| 0:16 | 6 | **Demo 1 — Understanding** an unfamiliar library | Live: Copilot CLI on TinyDB | [01-understanding](../examples/01-understanding/README.md) |
| 0:22 | 6 | **Demo 2 — Architecture & design extraction** → Mermaid diagrams, patterns, ADRs | Live: Express (and/or Flask) | [02-architecture](../examples/02-architecture/README.md) |
| 0:28 | 6 | **Demo 3 — Refactoring with guardrails** — characterization tests first, then refactor | Live: `labs/legacy-invoice` | [03-refactoring](../examples/03-refactoring/README.md) |
| 0:34 | 8 | **Demo 4 — Finding & fixing vulnerabilities** — AI review + CodeQL + Autofix; variant analysis on a real CVE | Live: `labs/vuln-notes-*`, minimist CVE-2021-44906 | [04-vulnerabilities](../examples/04-vulnerabilities/README.md) |
| 0:42 | 5 | **Attackers have AI too + Ethics** — defensive posture; REA & IP; responsible disclosure | Discussion | [ethics-and-defense.md](ethics-and-defense.md) |
| 0:47 | 3 | **Takeaways & Q&A** | Summary, resources | — |

> **Local models (Ollama)** are woven into Demo 1 or Demo 4 as a 60-second "same prompt, private model" comparison. Full exercises live in [05-local-models](../examples/05-local-models/README.md) as take-home work.

## Timing guardrails

- Every live demo has a **pre-recorded fallback** (screenshot or saved output). Record these the day before using the exact prompts in `examples/`.
- If running long, cut in this order: Flask half of Demo 2 → Ollama comparison → requests CVE (keep minimist).
- Keep terminals pre-opened in each target directory; font size ≥ 20pt.

## Pre-lecture checklist

- [ ] `.\scripts\setup-targets.ps1` (clones pinned targets into `targets\`)
- [ ] `npm install` then `npm run build` (slides → `dist\`)
- [ ] Copilot CLI signed in (`copilot` → `/login`), model chosen (`/model`)
- [ ] VS Code with Copilot Chat; workspace opened on `targets\express`
- [ ] CodeQL CLI on PATH (`codeql version`) and databases **pre-built** for the labs (database creation is too slow to do live)
- [ ] Ollama running with a code model pulled (e.g., `ollama pull qwen2.5-coder:7b`)
- [ ] A throwaway GitHub repo with the vuln labs pushed and **code scanning + Copilot Autofix** enabled, with an open PR ready to show
- [ ] Fallback outputs saved under each example's `recorded\` folder

## Take-home assignment (optional)

Students pick one library from [library-recommendations.md](library-recommendations.md) and submit:

1. An AI-generated architecture overview **with every claim cited to file:line** and at least three claims they personally verified (and one they found to be wrong or imprecise, if any).
2. A Mermaid diagram of one key flow.
3. One safe refactoring PR (to their fork) with characterization tests written *before* the change.
4. A short reflection: where did the AI help most, where did it mislead, and how did they catch it?
