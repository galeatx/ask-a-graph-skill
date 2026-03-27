# Step 3 — Resolve entities against the graph

Map instance entities from Step 1 to actual Neo4j nodes. This is a two-part process: find candidates, then apply selections.

Only pass **instance entities** (`classification == "instance"`) — class entities (e.g. "patients") map directly to node labels and do not need graph lookup.

---

## Step 3a — Identify disambiguation candidates

```
uv run python -m ai_oncology.graph_client identify_disambiguation_candidates '{
  "database_name": "<database>",
  "entities": <instance entities from Step 1>,
  "schema_context_id": "<schema_context_id from Step 2>",
  "user_query": "<original user question>"
}' > $output_dir/step3a_candidates.json
```

**Latency:** This step runs multiple sequential LLM and database calls internally and routinely takes 30–120 seconds. Wait for it — do not launch additional Bash processes to check on it while it is running.

**Timeout handling:** This step can time out (the MCP server enforces a 120 s limit) because it runs several sequential LLM and database calls internally. If the command exits with a timeout error or returns `"error_type": "timeout"`, retry the exact same call up to **3 times** before giving up. Wait a few seconds between retries. If all 3 attempts fail, stop and tell the user:

> "The disambiguation step is taking too long to complete right now — the server appears to be under load. Please try again in a few minutes."

Do not proceed to Step 3b or Step 4 if this step has not returned a successful result.

**What to retain from the output:**
- `session_id` — required for Step 3b (only if `widgets` is non-empty)
- `already_resolved` — entities that matched uniquely or failed to match; inspect each one
- `widgets[]` — one widget per entity that needs disambiguation; each contains `entity_tag`, `original_text`, and `options[]`

**Before proceeding, inspect every entry in `already_resolved`** — not all of them are clean successes:

- `resolution_status: "resolved"` → carry forward normally
- `resolution_status: "not_found"` with error `"No searchable properties found in schema for entity type '...'"` → this entity type is a **node label** (e.g. `LUAD`, `LUSC`, `GBM`), not a searchable instance. Do NOT pass it as a resolved entity. Instead, treat it as a class — use it as a node label constraint in `generate_cypher` (e.g. `MATCH (p:LUAD)` rather than `WHERE id(p) = $id`). Note this reclassification explicitly when calling `generate_cypher`.
- `resolution_status: "not_found"` for any other reason → inform the user the entity could not be matched and ask them to rephrase or use an alternate name

**If `widgets` is empty and all `already_resolved` are clean**: skip Step 3b — use `already_resolved` as `resolved_entities` and proceed to Step 4.

**If `widgets` is non-empty** — for each widget:
- **Present the options clearly to the user**, ask them to specify which one they mean, and wait for confirmation before proceeding
- **Zero candidates** (`special_options` only contains "None of the above"): inform the user — no match found, ask them to rephrase or use an alternate name

Never auto-select based on score, position, or name similarity — always ask the user.

**Example output:**
```json
{
  "status": "needs_disambiguation",
  "session_id": "disamb_1e35d72bef0b",
  "already_resolved": [],
  "widgets": [
    {
      "widget_id": "widget_83439cc5",
      "entity_tag": "GENE_INSTANCE_1",
      "entity_type": "Gene",
      "original_text": "KRAS",
      "prompt": "Multiple Gene nodes match 'kras'. Select one or more:",
      "options": [
        {"id": 1, "label": "KRASP1", "node_id": 68980},
        {"id": 2, "label": "ITPRID2", "node_id": 29872},
        {"id": 5, "label": "KRAS",   "node_id": 7231}
      ],
      "special_options": [
        {"id": "all", "label": "All 7 matches"},
        {"id": "none", "label": "None of the above"}
      ]
    }
  ],
  "resolution_summary": {
    "total_entities": 1,
    "already_resolved": 0,
    "needs_disambiguation": 1,
    "not_found": 0
  }
}
```

> Ignore the `a2ui` field — it is a UI rendering payload and is not needed for agent-based resolution.

---

## Step 3b — Apply entity selections

```
uv run python -m ai_oncology.graph_client apply_entity_selections '{
  "session_id": "<session_id from Step 3a>",
  "selections": {
    "<annotation_tag>": {"option_id": <id>, "node_id": <node_id>}
  }
}' > $output_dir/step3b_resolved.json
```

**Example** (selecting KRAS, option 5, node 7231):
```
uv run python -m ai_oncology.graph_client apply_entity_selections '{
  "session_id": "disamb_c9f875cd901b",
  "selections": {
    "GENE_INSTANCE_1": {"option_id": 5, "node_id": 7231}
  }
}'
```

**What to retain from the output:**
- `resolved_entities` from `apply_entity_selections` — merge with clean `already_resolved` entries from Step 3a to form the complete resolved entity list passed to `generate_cypher` in Step 4

**If `apply_entity_selections` returns `status: "partial_success"`**: some entities could not be resolved. Check `resolved_entities[]` for entries with `resolution_status: "error"` — apply the same reclassification logic as above (node label constraint vs. instance lookup). Proceed with the successfully resolved entities; do not abort the workflow over unresolvable label-type entities.
