# Demo 3: Refactoring with Guardrails

**Time on stage:** 6 minutes · **Targets:** `labs\legacy-invoice` (hands-on), `targets\bottle` (refactoring *planning* at scale)
**Tools:** Copilot CLI or Copilot Chat (Agent/Edit mode), Python `unittest`

## Goal

Teach the **safe refactoring loop**:

```text
 1. Understand  →  2. Pin behavior (characterization tests)  →  3. Small AI-proposed step
        ↑                                                              ↓
        └──────────────  5. Commit  ←  4. Run tests + review diff  ────┘
```

Key idea: **refactoring means changing structure *without* changing behavior.** AI is eager to "improve" behavior too, and that's where bugs come from.

## Setup

```powershell
# Work on a scratch copy so the lab stays pristine for the next class section
Copy-Item -Recurse -Force labs\legacy-invoice $env:TEMP\legacy-invoice
cd $env:TEMP\legacy-invoice
git init -q; git add .; git commit -qm "baseline"     # so every AI step is a reviewable diff
python -m unittest -v                                 # 13 characterization tests, all green
```

---

## Prompt 3.1: Smell inventory (no changes yet)

```text
@invoice.py
Situation: I need to refactor this legacy module safely.
Constraints: Do NOT modify any files yet.
Objective: Identify code smells and risks.
Product: A table of smell | location (line) | why it matters | suggested refactoring (Fowler name).
Then list any places where the CURRENT behavior looks like a bug or inconsistency. Do not fix them;
just flag them as questions for the product owner.
Evidence: Cite line numbers.
```

**A good answer finds:** a long method; duplicated discount logic across categories *and* between `calc` and `print_invoice`; magic numbers (0.9, 0.95, 0.97, 0.06, 5.99, 50, 100, 10); stringly-typed `customer_type`/`state`/`coupon`; global mutable `discount_log`; `!= None`; floats for money.
**Behavior questions it should flag (not fix):**
- Electronics bulk discount uses `> 10` while others use `>= 10` (**the planted quirk**).
- `SAVE10` applies only if the post-discount total is `> 100`, so a $110 gold order costs *more* than a $120 one.
- `HALFSHIP` halves shipping even when shipping is already 0.

## Prompt 3.2: Characterization tests (if they didn't exist)

> In this lab they're provided in `test_invoice.py`. Show the prompt anyway, because it's the most valuable habit in the demo.

```text
@invoice.py
Write Python unittest characterization tests that pin the CURRENT behavior of calc() and print_invoice(),
including edge cases at every threshold (qty 9/10/11, totals 50/100), every customer type, every state,
both coupons, and the discount_log side effect. Do not "correct" any behavior: if something looks like a
bug, write a test that asserts the current behavior and add a comment "QUIRK:".
```

## Prompt 3.3: One small, verifiable step

```text
@invoice.py @test_invoice.py
Refactor step 1 only: replace the per-category if/elif chain in calc() with a data-driven table of
(bulk_threshold, comparison, discount_rate) per category, and reuse it in print_invoice() to remove the
duplication. Preserve behavior EXACTLY (including the electronics `> 10` quirk).
Do not touch tax, shipping, coupons, or discount_log in this step.
After editing, run: python -m unittest -v   and show me the result and the diff.
```

Then iterate with similar single-purpose prompts:
- Step 2: extract `apply_customer_discount`, `apply_coupon`, `compute_tax`, `compute_shipping`.
- Step 3: replace magic numbers with named constants; replace strings with `Enum`s, but keep the public signature backward-compatible.
- Step 4: make `discount_log` injectable (pass a logger/list) while keeping the module-level default.

**After each step:** `python -m unittest -v` → review `git diff` → commit.

## Prompt 3.4: Behavior-changing improvements, done honestly

```text
Now, separately from the refactor, propose (do not apply) changes that WOULD alter behavior:
switching to Decimal for money, fixing the electronics threshold, and fixing the SAVE10 cliff.
For each: show which characterization tests would need to change and why, so the change is explicit
and reviewable.
```

> 🎤 **Talking point:** the test diff is the behavior change. If the AI's "refactor" made a test fail, it changed behavior, whether or not it "looks better."

---

## Refactoring at scale: Bottle (planning, not executing)

`targets\bottle\bottle.py` is a single **4,680-line** file. You don't refactor that live, but AI is very good at producing the **plan**.

```text
@bottle.py
Situation: Hypothetically, we want to split bottle.py into a package without breaking its public API.
Constraints: Do not modify files. Bottle is single-file BY DESIGN (easy vendoring). Acknowledge this trade-off.
Objective: Propose a modular decomposition.
Product:
  1. Clusters of classes/functions that belong together (e.g., routing, request/response, templates,
     server adapters, plugins, utilities), with line ranges.
  2. A Mermaid dependency graph between proposed modules; highlight any cycles.
  3. The public names that must be re-exported from bottle/__init__.py to keep `import bottle` working.
  4. A migration order that keeps tests green at each step.
  5. Your recommendation: should this project actually do it? Why or why not?
Evidence: line numbers for every cluster boundary.
```

> 🎤 **Talking point:** the best answer to part 5 is *"probably not."* The single-file design is a deliberate distribution feature. **Architecture is about trade-offs, and AI should surface them, not just apply "best practices."**

## Pitfalls to call out

- **Big-bang refactors:** a single prompt that rewrites everything produces a diff no human can review. Keep steps small.
- **Silent behavior "fixes":** the electronics quirk is the trap. Watch for the test failure.
- **Hallucinated APIs:** AI may introduce helpers or imports that don't exist. Tests catch it.
- **Lost side effects:** `discount_log` is easy to drop. That's why the test exists.
