# Demo 1: Understanding an Unfamiliar Codebase (TinyDB)

**Time on stage:** 6 minutes · **Target:** `targets\tinydb` (TinyDB v4.8.0, ~2.3k LOC Python, MIT)
**Tools:** GitHub Copilot CLI (read-only: `copilot --deny-tool write --deny-tool shell`), optional `/model` comparison

## Goal

Show that a good AI workflow goes **broad → narrow → verify**: get an orientation map, trace one concrete operation end to end, probe a subtle mechanism, then verify claims against the source.

## Setup

```powershell
cd targets\tinydb
copilot --deny-tool write --deny-tool shell   # read-only analysis session
```

---

## Prompt 1.1: Orientation map (broad)

```text
Situation: I'm a new contributor to this repository and need a mental model before touching code.
Constraints: Read-only. Do not modify files. Focus on the tinydb/ package; ignore tests and docs.
Objective: Give me an orientation to the codebase.
Product:
  1. What the library does (2 sentences).
  2. A table of each module in tinydb/ with its responsibility (1 line each).
  3. The 5 most important classes: name, file:line, responsibility, and who uses it.
  4. A short layered diagram (Mermaid flowchart) of how the main classes depend on each other.
Evidence: Cite file:line for every class or function you mention. Mark anything inferred as "inferred".
End with 3 questions a new contributor should investigate next.
```

**A good answer includes:**
- `TinyDB` (`database.py`) → owns `Table` instances (cached in `self._tables`, `database.py:111-131`) and one `Storage`.
- `Table` (`table.py:39`) does all CRUD. `Document` (`table.py:26`) is a `dict` with a `doc_id`.
- `Storage` ABC (`storages.py:36`) with `JSONStorage` and `MemoryStorage`. `Middleware` / `CachingMiddleware` (`middlewares.py`) wraps a storage (**decorator pattern**).
- `Query` / `QueryInstance` (`queries.py`): a query-builder DSL.
- `LRUCache` (`utils.py:39`) backs the per-table query cache.
- `TinyDB.__getattr__` (`database.py:251`) forwards unknown attributes to the default table (`_default`), which is why `db.insert(...)` works without calling `db.table(...)`.

## Prompt 1.2: Trace a concrete operation (narrow)

```text
Trace, step by step, exactly what happens when this code runs on a fresh file:

    from tinydb import TinyDB
    db = TinyDB('db.json')
    db.insert({'name': 'Ada'})

Start at TinyDB.__init__ and end when bytes are on disk. For each step give file:line and one sentence.
Then answer: how many times is the whole file read and written for one insert? What does that imply for performance as the DB grows?
```

**A good answer includes:**
- `db.insert` is resolved by `TinyDB.__getattr__` → `self.table('_default')` → `Table.insert` (`table.py:137`).
- `_get_next_id()` (`table.py:659`) reads the table if the next id isn't cached.
- `_update_table()` (`table.py:719`) **reads the entire DB** from storage, mutates it in memory, **writes the entire DB back** (`JSONStorage.write`: `json.dumps`, `flush`, `os.fsync`, `truncate`, `storages.py:138-157`), then clears the query cache.
- Insight: every write is O(size of whole DB). That's fine for small data, which is the library's stated niche.

## Prompt 1.3: Probe a subtle mechanism

```text
Explain how `Query().name == 'Ada'` becomes something Table.search() can execute.
Show the minimal chain of methods involved (file:line) and explain:
  (a) what `_path` holds,
  (b) how the query is hashed for the query cache,
  (c) which kinds of queries are NOT cacheable and why.
```

**A good answer includes:** `Query.__getattr__` (`queries.py:188`) builds a new query with an extended `_path`. `__eq__` calls `_generate_test` (`queries.py:213`), which returns a `QueryInstance` wrapping a test callable plus a hash tuple. `is_cacheable()` (`queries.py:82`) is `self._hash is not None`. `.map(fn)` deliberately sets `_hash = None` (`queries.py:518`) because callables may be mutable.

## Prompt 1.4: Hunt for hidden assumptions (where AI shines when asked)

```text
Based only on the code, what assumptions does TinyDB make about concurrency and about
being the only writer to its file? Describe a concrete scenario where two TinyDB instances
(or two processes) using the same db.json could return stale results or produce duplicate doc_ids.
Cite the exact state that becomes stale.
```

**A good answer includes:** the query cache (`Table._query_cache`) and `Table._next_id` are **per-instance, in-memory** state. A write from another instance or process doesn't invalidate them, so you can get stale search results and duplicate IDs. There is no file locking. `CachingMiddleware` (`middlewares.py:86`) buffers up to 1000 writes, so a crash before `flush()`/`close()` loses data.

> 🎤 **Talking point:** the AI didn't "know" this. It *found* it because we asked a pointed question. Good analysis prompts are hypotheses to test.

## Prompt 1.5: Turn it into learning material (optional)

```text
Write 5 quiz questions (with answers and file:line citations) that test whether a new
contributor understands TinyDB's storage, middleware, and query-cache design.
```

---

## Verify live (1 minute)

Pick two citations from the AI output and open them. Then run a quick check:

```powershell
cd targets\tinydb
python -c "from tinydb import TinyDB; from tinydb.storages import MemoryStorage; db=TinyDB(storage=MemoryStorage); print(db.insert({'name':'Ada'}), db.all())"
```

## Model comparison (optional, 60 seconds)

In the same Copilot CLI session, run `/model`, pick a different model, and re-ask Prompt 1.4 (hidden assumptions). Compare which in-memory state each model cites, and whether the citations are correct. Different models give different answers, which is why you verify.

For a private/offline comparison with a local model, see [05-local-models](../05-local-models/README.md) (take-home).

## Pitfalls to call out

- **Plausible but wrong line numbers.** Always spot-check.
- **Over-generalization:** "TinyDB is thread-safe" is false, and sometimes models say it confidently.
- **Training-data bleed:** the model may describe a *different version* of TinyDB from memory. Ask it to quote the code it's relying on.
