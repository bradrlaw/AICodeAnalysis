# Sample output: module table (Copilot CLI, read-only `-p` run)

Command (run from `targets\tinydb`):

```powershell
copilot -p "Situation: new contributor. Constraints: read-only; only the tinydb/ package. Objective: table of each module in tinydb/ with a one-line responsibility. Evidence: cite file:line for each main class. Keep it under 20 lines." --deny-tool write --deny-tool shell
```

| Module | Responsibility and main-class evidence |
|---|---|
| `tinydb\__init__.py` | Exposes the public database, query, and storage API; no classes defined (`tinydb\__init__.py:27–32`). |
| `tinydb\database.py` | Manages storage, named tables, and default-table delegation: `TinyDB` (`tinydb\database.py:16`). |
| `tinydb\table.py` | Implements document CRUD and query caching: `Table` (`tinydb\table.py:39`); documents carry IDs via `Document` (`tinydb\table.py:26`). |
| `tinydb\queries.py` | Builds and combines document predicates: `Query` (`tinydb\queries.py:136`), `QueryInstance` (`tinydb\queries.py:61`), and the `QueryLike` protocol (`tinydb\queries.py:37`). |
| `tinydb\storages.py` | Defines persistence contracts and JSON-file/in-memory backends: `Storage` (`tinydb\storages.py:36`), `JSONStorage` (`tinydb\storages.py:79`), `MemoryStorage` (`tinydb\storages.py:160`). |
| `tinydb\middlewares.py` | Wraps storage behavior and provides cached reads/batched writes: `Middleware` (`tinydb\middlewares.py:10`), `CachingMiddleware` (`tinydb\middlewares.py:76`). |
| `tinydb\operations.py` | Supplies field-update functions for deletion, assignment, and arithmetic; no classes (`tinydb\operations.py:12–62`). |
| `tinydb\utils.py` | Provides caching, immutable query-hash data, and typing helpers: `LRUCache` (`tinydb\utils.py:39`), `FrozenDict` (`tinydb\utils.py:114`). |
| `tinydb\mypy_plugin.py` | Makes mypy understand dynamic bases created by `with_typehint`: `TinyDBPlugin` (`tinydb\mypy_plugin.py:12`). |
| `tinydb\version.py` | Defines the package version; no classes (`tinydb\version.py:1`). |
