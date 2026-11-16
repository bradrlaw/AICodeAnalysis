# AI-Assisted Code Analysis: UF Guest Lecture

> *A deep dive into using AI tools and models to analyze a codebase: understanding it, extracting architecture and design, refactoring safely, and finding and fixing vulnerabilities. It also covers what defenders must do now that attackers have the same tools, and the ethics of AI-assisted reverse engineering.*

**Length:** 50 minutes · **Languages:** Python, JavaScript/TypeScript
**Tools:** GitHub Copilot CLI · Copilot Chat (VS Code) · Copilot code review & Autofix · CodeQL · Ollama

## Repository layout

```text
slides/lecture.md            Marp slide deck, with speaker notes in HTML comments
docs/
  agenda.md                  Timed agenda, learning objectives, pre-lecture checklist, take-home
  library-recommendations.md Which open-source libraries to analyze and why (pinned versions)
  ethics-and-defense.md      Attackers-have-AI-too, defensive measures, REA, IP and law, disclosure
examples/
  README.md                  SCOPE-E prompt pattern, tool cheat sheet, verification habits
  01-understanding/          TinyDB: orientation, tracing, mechanisms, hidden assumptions
  02-architecture/           Express / Flask: component and sequence diagrams, patterns, ADRs
  03-refactoring/            legacy-invoice lab + Bottle decomposition planning
  04-vulnerabilities/        Lab apps, CodeQL, Autofix, minimist & requests CVE variant analysis
  05-local-models/           Ollama: private analysis, context experiments, map-reduce
labs/
  legacy-invoice/            Smelly Python module + 13 characterization tests (refactoring target)
  vuln-notes-flask/          INTENTIONALLY VULNERABLE Flask app + instructor ANSWER_KEY.md
  vuln-notes-express/        INTENTIONALLY VULNERABLE Express app + instructor ANSWER_KEY.md
scripts/
  setup-targets.ps1 / .sh    Clones pinned open-source targets into targets/ (git-ignored)
```

## Quick start

```powershell
# 1. Clone the pinned analysis targets (TinyDB, Flask, Express, Bottle, minimist, requests)
.\scripts\setup-targets.ps1

# 2. Build the slides (HTML + PDF; PPTX optional)
npm install
npm run build            # → dist\lecture.html, dist\lecture.pdf
npm run build:pptx       # → dist\lecture.pptx  (needs Chrome or Edge installed)
npm run preview          # live-reload preview server

# 3. Sanity-check the labs
cd labs\legacy-invoice; python -m unittest -v
```

Then follow the **pre-lecture checklist** in [docs/agenda.md](docs/agenda.md).

## Suggested open-source targets

| Purpose | Target | Why |
|---|---|---|
| Understanding | **TinyDB** v4.8.0 (Python) | Small, clean layering, clever query DSL, real hidden assumptions to discover |
| Architecture | **Express** 4.21.2 (JS), **Flask** 3.0.3 (Python) | Middleware pipeline, context locals, patterns students already use |
| Refactoring at scale | **Bottle** 0.13.2 (Python) | A 4,680-line single file, a good trade-off discussion |
| Security (real CVEs) | **minimist** 1.2.5→1.2.6, **requests** 2.30.0→2.31.0 | Tiny, already-fixed diffs: incomplete-fix and logic-bug lessons |

Details and stretch targets (OWASP Juice Shop, PyGoat, ms, httpx, Zod, click) are in [docs/library-recommendations.md](docs/library-recommendations.md).

## Ground rules for this material

- Security content is **defensive**: our own intentionally vulnerable labs and **publicly disclosed, already-patched** CVEs. No exploit development and no testing of systems we don't own.
- Reverse-engineering tools (e.g., REA) are **discussed, not demonstrated**. See [docs/ethics-and-defense.md](docs/ethics-and-defense.md).
- The `labs/vuln-notes-*` apps are **intentionally insecure**. They bind to `127.0.0.1` only. **Never deploy them.** Remove `ANSWER_KEY.md` files before sharing labs with students.

## TODO before delivery

- [x] Speaker name, title, and contact on the title and closing slides
- [x] Repo URL on the closing slide
- [ ] Fill in the lecture date (title slide)
- [ ] Record fallback outputs for every demo into `examples/*/recorded/`
- [ ] Pre-build CodeQL databases and the throwaway GitHub repo for Autofix
- [ ] Dry run with a timer; trim per the cut order in `docs/agenda.md`
