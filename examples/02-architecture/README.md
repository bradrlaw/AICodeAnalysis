# Demo 2: Extracting Architecture & Design

**Time on stage:** 6 minutes · **Targets:** `targets\express` (Express 4.21.2, JS) and optionally `targets\flask` (Flask 3.0.3, Python)
**Tools:** Copilot Chat in VS Code (primary, for the visual Mermaid preview), Copilot CLI

## Goal

Go from code to **diagrams, patterns, and documented design decisions**, then show how to **check a diagram against the code** instead of trusting it.

## Setup

```powershell
code targets\express      # open as workspace; Copilot Chat → Ask mode
```

Install a Mermaid preview extension (e.g., *Markdown Preview Mermaid Support*) so diagrams render live.

---

## Prompt 2.1: Component view (C4 level 3)

```text
#codebase
Situation: I need to document the architecture of this library for a design review.
Constraints: Read-only. Only consider lib/. Ignore examples/, test/, benchmarks/.
Objective: Produce a component-level architecture description.
Product:
  1. A Mermaid `flowchart` showing the main components (files/objects) in lib/ and their dependencies.
  2. A table: component, file, responsibility, key exported functions.
  3. A list of design patterns you can identify, each with the file:line that shows it.
Evidence: Cite file:line. Label any pattern you inferred but could not point to as "inferred".
```

**A good answer includes:**
- `express.js:37` `createApplication()` returns a **function** `app(req, res, next)` and **mixes in** `EventEmitter.prototype` and `application.js` (`express.js:42-43`). That's the *mixin* pattern; the app is literally an HTTP request handler.
- `application.js` holds settings, `use`, `route`, the verb methods (`methods.forEach`, `:489`), `render`, and `listen` → `http.createServer(this)` (`:633-634`).
- `router/index.js` (Router), `router/layer.js` (Layer = path matcher + handler), `router/route.js` (Route = per-path verb dispatch).
- `request.js:31` / `response.js:43` are `Object.create(http.IncomingMessage.prototype)` / `ServerResponse.prototype`. Express **extends Node's objects via prototype chains**, re-pointed per request in `middleware/init.js:35-36`.
- Patterns: **Chain of Responsibility / Pipeline** (middleware `next()`), **Composite** (Router is itself middleware, so routers nest), **Mixin**, **Prototype-based extension**, **Lazy initialization** (`app.lazyrouter`, `application.js:144`), **Template Method/Strategy** for view engines (`view.js`, `app.engine`).

## Prompt 2.2: Runtime behavior (sequence diagram)

```text
#codebase
Draw a Mermaid sequenceDiagram of what happens for a GET /users/42 request in this app:

    const app = express();
    app.use(express.json());
    app.get('/users/:id', (req, res) => res.json({ id: req.params.id }));
    app.listen(3000);

Participants: Node http server, app (application.js), Router (router/index.js), Layer, Route, the handler.
Show how `next()` advances through the stack and what happens if a handler throws.
Cite file:line for each arrow.
```

**A good answer includes:** `http.Server` → `app(req,res)` → `app.handle` (`application.js:165`) → `router.handle` (`router/index.js:136`) → internal `next()` loop (`:177`) → `matchLayer` (`:583`) → `layer.handle_request` (`layer.js:86`) → for route layers `Route.dispatch` (`route.js:101`) → handler. Errors make `next(err)` skip to 4-argument handlers through `layer.handle_error` (`layer.js:62`). A sync `throw` is caught by `handle_request`'s try/catch and passed to `next(err)`.

## Prompt 2.3: Design-decision archaeology (ADR)

```text
Write an Architecture Decision Record (ADR, Michael Nygard format: Title, Status, Context, Decision,
Consequences) explaining WHY Express 4 extends Node's req/res via prototypes instead of wrapping them
in new objects. Base it on evidence in lib/ (cite file:line). Include at least two negative consequences.
Clearly separate what the code proves from what you are inferring about the authors' intent.
```

> 🎤 **Talking point:** AI is good at *proposing* rationale, but intent is not in the code. Insist on the proven-vs-inferred split. Real ADRs and commit history (`git log -S`) are better evidence when they exist.

## Prompt 2.4: Check the diagram against the code (verification)

```text
Here is the diagram you produced. For each arrow, quote the single line of code that proves it.
If you cannot find such a line, mark the arrow "UNSUPPORTED" and remove it from a corrected diagram.
```

## Prompt 2.5 (optional): Fitness functions

```text
Propose 3 architectural rules for this codebase that could be enforced automatically
(e.g., "router/* must not import application.js"). For each, give a dependency-cruiser rule
or a small Node script that checks it, and say whether the current code passes.
```

---

## Flask variant (Python, if time allows)

```powershell
cd targets\flask
copilot --plan
```

```text
Situation: I'm preparing a lecture on Flask's internals.
Constraints: Read-only. Only src/flask/.
Objective: Explain Flask's context architecture.
Product:
  1. A Mermaid classDiagram of Flask, App (sansio), Scaffold, Blueprint, AppContext, RequestContext.
  2. A sequenceDiagram of how `flask.request` resolves to the current request object during a view call.
  3. Why does src/flask/sansio/ exist? What is in it vs. what is outside it? (cite files)
Evidence: file:line for every claim; label inferences.
```

**A good answer includes:** `sansio/app.py`, `sansio/scaffold.py`, `sansio/blueprints.py` hold I/O-agnostic logic. `app.py`'s `Flask` subclasses `sansio.app.App` and adds WSGI. `globals.py` defines `request`, `g`, `current_app` as Werkzeug `LocalProxy` objects over `contextvars` (`_cv_app`, `_cv_request`). `ctx.py` defines `AppContext` and `RequestContext`, which push and pop those context vars.

## Pitfalls to call out

- **Version drift:** models may describe Express 5 (which moved the router into the separate `router` package) or Flask 2.x. Pinning versions and demanding citations prevents this.
- **Pretty but wrong diagrams:** diagrams are persuasive. Prompt 2.4 exists because of that.
- **Missing the dynamic parts:** static reading can miss runtime monkey-patching and plugins. Mention runtime tracing (debugger, `NODE_DEBUG`, `sys.settrace`) as a complement.
