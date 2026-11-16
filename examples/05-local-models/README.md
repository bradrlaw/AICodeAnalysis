# Demo 5 / Take-Home: Local Models with Ollama

**On stage:** a 60-second comparison inside Demo 1 or 4 · **Take-home:** the full exercises below
**Why:** some code can't leave the machine (proprietary, export-controlled, classified, or covered by a client contract). Local models trade capability and context-gathering for **privacy, offline use, and zero per-token cost**.

## Setup

```powershell
winget install Ollama.Ollama          # or https://ollama.com/download
ollama pull qwen2.5-coder:7b          # ~4.7 GB; runs on a laptop GPU or CPU
# Larger/better if hardware allows, e.g.: ollama pull qwen2.5-coder:32b
ollama list
```

> Model names change quickly. Check the [Ollama library](https://ollama.com/library) for the current best code models and substitute freely. The prompts don't depend on a specific model.

Copilot CLI can also use models you run yourself. See `copilot help` and the CLI docs on bring-your-own/local providers, which let you compare **agentic workflow + local model** with plain chat.

## Helper: feed a file with line numbers

Local chat models can't navigate a repo, so you give them context. Add line numbers so citations are possible:

```powershell
function Show-Numbered($Path) { $i = 0; Get-Content $Path | ForEach-Object { '{0,4}: {1}' -f (++$i), $_ } | Out-String }

Show-Numbered targets\tinydb\tinydb\table.py |
  ollama run qwen2.5-coder:7b "Explain _update_table() and why it clears the query cache. Cite line numbers."
```

## Exercise 5.1: Same prompt, three tools

Run Prompt **1.2** from [Demo 1](../01-understanding/README.md) with:
1. Copilot CLI (agentic, navigates the repo itself)
2. Ollama with only `table.py` piped in
3. Ollama with `database.py` + `table.py` + `storages.py` concatenated

Record: correctness of each step, citation accuracy, hallucinations, and time. **Question:** how much of the quality gap is the *model* and how much is the *context*?

## Exercise 5.2: Private security review

```powershell
Show-Numbered labs\vuln-notes-flask\app.py |
  ollama run qwen2.5-coder:7b @"
You are a defensive application-security reviewer. Review this Flask app.
Output a table: line | weakness | CWE | severity | fix. Do not write exploit payloads.
Then list anything you are unsure about.
"@
```

Score it against [`labs/vuln-notes-flask/ANSWER_KEY.md`](../../labs/vuln-notes-flask/ANSWER_KEY.md): precision (how many findings are real?) and recall (how many real issues were found?). Compare with Copilot's score from Demo 4.

## Exercise 5.3: Map-reduce for big files

`targets\bottle\bottle.py` (4,680 lines) may exceed a small model's effective context. Practice **chunking**:

1. Split the file into ~400-line chunks.
2. *Map:* for each chunk, ask "list classes/functions with one-line responsibility and line range."
3. *Reduce:* feed all chunk summaries into one prompt: "propose module clusters" (as in Demo 3).

This is how agentic tools work behind the scenes (retrieval + summarization). Doing it by hand builds intuition for their failure modes, such as relationships that span chunks.

## Discussion

- When is a weaker private model the *right* choice?
- What organizational controls (approved-tool lists, content exclusion, data classification) decide that for you at work?
