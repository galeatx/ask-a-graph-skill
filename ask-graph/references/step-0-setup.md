# Step 0 — One-time setup (per session)

> **IMPORTANT:** Check `setup_complete.json` FIRST. Do NOT run `curl`, `docker ps`, or any manual health checks — setup.py handles all of that internally. Do NOT run setup as a background task; run it synchronously and wait for it to finish before proceeding.

---

**1. Check if setup is already complete:**
```
uv run python -c "import json; d=json.load(open('$setup_dir/setup_complete.json')); print(d.get('setup_complete', False))"
```

- If this command **succeeds and prints `True`** → setup is done, proceed to Step 1.
- If the file **does not exist** (FileNotFoundError) or prints `False` → run setup.

**2. If setup is needed, run it synchronously (never as a background task):**

Run from the project root — the path `.claude/skills/ask-graph/scripts/setup.py` is relative to it:
```
uv run --directory /mnt/c/Users/JIHX/Documents/Projects/ai-oncology .claude/skills/ask-graph/scripts/setup.py $setup_dir
```

Wait for the command to finish before moving to Step 1. Setup performs all server/DB checks internally — do not add any curl or connectivity checks before or after.

---

**Path:** `setup_complete.json` is always written to `$setup_dir`, which is `${session_dir}/files/graph_results/setup_complete.json`. `${session_dir}` is the absolute session path provided by the agent's system prompt — do not use it literally; it will be substituted at runtime. Use the actual absolute path when reading this file.

Setup performs 3 checks in order:
1. MCP server health
2. Database connectivity (oncograph, arch-v5)
3. Schema cache — bootstraps if missing

On success it writes `setup_complete.json`:
```json
{
  "setup_complete": true,
  "databases": ["oncograph", "arch-v5"]
}
```

Entity and relationship types are **not** fetched here — they are retrieved dynamically per query via `list_entity_types` in Step 1.

> **Do not proceed** if setup fails — subsequent tool calls will not work.
