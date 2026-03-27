# Step 4 — Generate Cypher query

Translate the user question into a Cypher query grounded in the schema slice from Step 2 and the resolved entities from Step 3.

---

## Schema context validity

`schema_context_id` is stored **in-memory inside the running Docker container**. It does not survive a container restart and expires after 1 hour.

**Before calling this tool**, verify the `schema_context_id` from Step 2 is still valid:
- If Step 2 was run in the current session and the container has not been restarted, proceed
- If unsure, re-run Step 2 (`slice_schema`) to obtain a fresh `schema_context_id` before continuing

**Symptom of a stale/missing schema context**: the `explanation` field says *"Without schema context"* and the query contains relationship types that don't appear in `included_relationships` from `step2_slice.json` (e.g. hallucinated types like `ADDICTED_TO`, `DEPENDENT_ON`). If this happens, re-run Step 2 and retry.

---

## Latency

This step makes an LLM call and may take 30–90 seconds. Wait for it to complete — do not launch additional Bash processes to check on it or debug while it is running.

## Tool call

```
uv run python -m ai_oncology.graph_client generate_cypher '{
  "user_question": "<original user question>",
  "database_name": "<database>",
  "schema_context_id": "<schema_context_id from Step 2>",
  "resolved_entities": <merged resolved_entities from Step 3>
}' > $output_dir/step4_cypher.json
```

Output is saved to `$output_dir/step4_cypher.json` for troubleshooting. Process the output inline — do not re-read the file unless debugging.

**`resolved_entities` format** — each entry must include:
```json
{
  "annotation_tag": "GENE_INSTANCE_1",
  "entity_type": "Gene",
  "classification": "instance",
  "original_text": "KRAS",
  "node_id": 7231
}
```

**What to retain from the output:**
- `cypher_query` — the generated Cypher query to execute in Step 5
- `parameters` — the parameter map (e.g. `{"kras_id": 7231}`) to pass alongside the query
- `explanation` — the LLM's reasoning; read this to verify the query is grounded in the schema and not hallucinated

**Validate the query before proceeding**: check that all relationship types in `cypher_query` appear in `included_relationships` from `step2_slice.json`. If any do not, the schema context was not loaded — re-run Step 2 and retry this step.

**If the user's question is general or exploratory**, pass a straightforward interpretation to `generate_cypher` — do not let it produce a deeply nested, multi-condition query. A simple MATCH → WHERE → RETURN is almost always better than a stacked query with multiple WITH clauses and OPTIONAL MATCHes.

**Do NOT silently modify the generated query.** If you spot a glaring syntax error (e.g. mismatched brackets, missing RETURN clause), correct it, save the revised query to `$output_dir/step4_cypher.revised.json`, and **tell the user what was changed and why** before proceeding. For anything beyond obvious syntax — wrong relationship types, unexpected logic — re-run `generate_cypher` or ask the user rather than fixing it yourself.

> Property name accuracy is handled by `read_schema_detail` in Step 2c — no post-generation probing is needed.