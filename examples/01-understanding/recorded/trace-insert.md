> **Recorded fallback** · GitHub Copilot CLI, read-only (`--deny-tool write --deny-tool shell`) · model gpt-6.1-sol · prompt: see docs/demo-script.md

 ✗ Shell Check working t… Permission to run this tool was denied due to the following rules: `shell`
   git --no-pager status --short

 / Search "tinydb\*.py" 10 files found

 PY Read tinydb\database.py L1:300 (274 lines read)

 PY Read tinydb\storages.py L1:260 (177 lines read)

 PY Read tinydb\__init__.py 32 lines read

 / Search "def (__init__|insert|_get_next_id|_update_table|__getattr__|_read_table)|… 16 lines found

 PY Read tinydb\table.py L77:177 (101 lines read)

 PY Read tinydb\table.py L659:780 (111 lines read)

 / Search "default_table_name =|default_storage_class =|storage = kwargs|self\._stor… 13 lines found

 / Search "^|$" in tinydb\storages.py 160 lines found

 / Search "self\._storage =|self\._name =|self\._query_cache:|self\._next_id =|if no… 63 lines found

**On a fresh file: two storage-read calls and one whole-database write.** Both reads find an empty file, so neither actually parses JSON. Subsequent inserts on the same table normally read the whole database once and rewrite it once.

### Step-by-step trace

Paths below are relative to the repository root.

1. **Construct the database.** `TinyDB.__init__` selects the default `JSONStorage`, passes it `'db.json'`, and initializes the opened flag and table-instance cache. No database contents are read yet.  
   `tinydb\database.py:84,91–97`

2. **Create and open the file.** `JSONStorage.__init__` defaults to text-mode `'r+'`. It calls `touch`, which opens in append mode to create an empty file without adding content, then opens the persistent read/write handle.  
   `tinydb\storages.py:84,112–116,32–33`

3. **Resolve `db.insert`.** `TinyDB.__getattr__` forwards this lookup to the `_default` table. `table()` creates and caches a `Table` sharing the storage. The table initializes its query cache and sets `_next_id = None`; this does not read the file.  
   `tinydb\database.py:255,79,127–133`; `tinydb\table.py:107–112`

4. **Validate the document and allocate an ID.** `Table.insert` accepts the dictionary as a `Mapping`. Because it is not a `Document` carrying an explicit ID, it calls `_get_next_id()`.  
   `tinydb\table.py:146–159`

5. **Storage read #1: determine the initial ID.** With no cached next ID, `_get_next_id()` calls `_read_table()`, which calls storage `read()`. That seeks to EOF, observes size zero, and returns `None`; `_read_table()` converts that to `{}`. The new ID is **1**, and `_next_id` becomes **2**.  
   `tinydb\table.py:665–682,704–708`; `tinydb\storages.py:124–130`

6. **Storage read #2: prepare the update.** `insert` calls `_update_table(updater)`. This independently reads storage again, gets `None` again, and creates empty database/table dictionaries. It converts existing document IDs to integers—there are none here.  
   `tinydb\table.py:173,733–752`; `tinydb\storages.py:124–130`

7. **Insert in memory.** The updater checks for a duplicate ID and stores a dictionary copy under integer key `1`. `_update_table` then converts IDs back to strings and places the table under `_default`.  
   `tinydb\table.py:162–170,755–763`

8. **Write the complete database.** `_update_table` calls `JSONStorage.write(tables)`. It seeks to the beginning, serializes the entire database with `json.dumps`, and writes:
   ```json
   {"_default": {"1": {"name": "Ada"}}}
   ```
   It then **flushes Python’s buffer, calls `os.fsync`, and truncates any leftover tail**. Persistence happens during `insert`, not only on close.  
   `tinydb\table.py:766`; `tinydb\storages.py:140–157`

9. **Finish.** The table clears its query-result cache, and `insert` returns `1`.  
   `tinydb\table.py:769,175`

### Read/write count and implications

| Case | Storage reads | Full-database writes |
|---|---:|---:|
| This first insert into an empty file | 2 empty-file checks; no JSON loads | 1 |
| First ordinary insert after reopening a populated database | 2 full JSON loads | 1 |
| Further ordinary inserts on the same table instance | 1 full JSON load | 1 |

The later ID-allocation read disappears because `_next_id` is cached (`tinydb\table.py:665–669`), **not because database contents are cached**.

Consequently, a single-document insert costs **O(total database size)** in reading, serialization, and rewriting—including other tables—plus an `fsync`. Repeated individual inserts of similarly sized documents therefore have roughly quadratic cumulative work as the database grows. The update is also an **in-place read–modify–write**, not a locked transaction or atomic file replacement: concurrent writers can lose updates, and interruption during rewriting can leave damaged JSON.
