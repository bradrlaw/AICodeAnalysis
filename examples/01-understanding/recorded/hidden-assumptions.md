> **Recorded fallback** · GitHub Copilot CLI, read-only (`--deny-tool write --deny-tool shell`) · model gpt-6.1-sol · prompt: see docs/demo-script.md

 / Search "tinydb\**\*.py" 10 files found

 PY Read tinydb\table.py L1:240 (240 lines read)

 PY Read tinydb\storages.py 177 lines read

 PY Read tinydb\middlewares.py 127 lines read

 PY Read tinydb\database.py L1:280 (274 lines read)

 / Search "_query_cache|_next_id|def _get_next_id|def _read_table|def _update_table|… 22 lines found

 PY Read tinydb\table.py L235:283 (49 lines read)

 PY Read tinydb\table.py L598:810 (172 lines read)

 ✗ Shell Get exact sourc… Permission to run this tool was denied due to the following rules: `shell`
   $files = @(@{Path='tinydb\storages.py';Start=110;End=159},
   @{Path='tinydb\middlewares.py';Start=85;End=129}, @{Path='tinydb\table.py';Start=147;End=174});
   foreach ($f in $files) { $i = 0; Get-Content $f.Path | ForEach-Object { $i++; if ($i -ge $f.Start
   -and $i -le $f.End) { '{0}:{1}: {2}' -f $f.Path,$i,$_ } } }

 / Search "cached_results|_query_cache\[cond\]|self\.clear_cache|tables = self\._sto… 25 lines found

 / Search "self\.cache|_cache_modified_count|WRITE_CACHE_SIZE|def flush|def close" i… 15 lines found

 / Search "self\._handle|json\.load|json\.dumps|os\.fsync" in *.py (tinydb\storages.… 12 lines found

**TinyDB’s built-in implementation assumes serialized access and no independent writer changing its state.** There is no locking or conflict detection around the whole-database read–modify–write (`tinydb\table.py:733–766`). JSONStorage overwrites the file in place, then flushes, fsyncs, and truncates (`tinydb\storages.py:138–157`); those operations do not make the transaction atomic or coordinate processes.

Two concrete scenarios sharing `db.json`:

- **Stale results, even without overlapping operations:** A searches for `Query().status == 'new'` and gets `[]`. That result lives in A’s **`Table._query_cache`**, initialized at `tinydb\table.py:109–110` and populated at `tinydb\table.py:275`. B inserts a matching document and finishes writing. A repeats the search and returns its cached `[]` without reading storage (`tinydb\table.py:245–247`). B’s update clears only B’s table cache (`tinydb\table.py:769`, `638`), not A’s.
- **Duplicate allocated IDs and a lost insert:** A inserts ID 1, leaving its **`Table._next_id == 2`** (`tinydb\table.py:678–680`). B opens the file, derives ID 2 from the maximum existing ID, and inserts it (`tinydb\table.py:685–690`). A’s counter is now stale: its next insertion still allocates 2 without checking storage (`tinydb\table.py:665–669`). **For sequential `insert()` calls, this raises `ValueError`**, because the updater checks for an existing ID (`tinydb\table.py:163–165`). But if A and B both read the table before either writes ID 2, both checks pass; each writes its own snapshot, both can return ID 2, and the last write loses the other insertion (`tinydb\table.py:733–766`). The JSON ends with one key `"2"`, not two distinct records with that key.

**Optional `CachingMiddleware` makes the assumption stronger:** its **`self.cache`** retains the entire database after the first non-`None` read (`tinydb\middlewares.py:93–102`). It never checks for external changes, and a later flush writes that cached snapshot wholesale (`tinydb\middlewares.py:117–120`), potentially overwriting another process’s updates.
