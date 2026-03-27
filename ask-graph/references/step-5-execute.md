# Step 5 — Execute the Cypher query

Run the validated Cypher query against the database. Results are stored server-side to protect the agent's context window — they are not returned inline.

---

## Latency

Execution time depends on query complexity and graph size — simple queries finish in seconds, broad traversals over large cohorts may take several minutes. Wait for the command to complete. Do not launch additional Bash processes to probe or debug while it is running. If execution appears to be taking longer than 3 minutes, inform the user and ask whether to keep waiting.

## Tool call

```
uv run python -m ai_oncology.graph_client execute_cypher '{
  "database_name": "<database>",
  "cypher_query": "<cypher_query from Step 4>",
  "parameters": <parameters from Step 4>
}' > $output_dir/step5_execute.json
```

Output is saved to `$output_dir/step5_execute.json` for troubleshooting. Process the output inline — do not re-read the file unless debugging.

**What to retain from the output:**
- `storage_object_id` — identifier for the stored results; pass to `summarize_results` in Step 6
- `total_record_count` — total number of records stored; use to gauge whether results are complete or unexpectedly empty

**Example output:**
```json
{
  "status": "success",
  "database_name": "oncograph",
  "storage_object_id": "results_3f8a21c7b4e9",
  "total_record_count": 47,
  "byte_size": 18432,
  "execution_time_ms": 312,
  "query_type": "read"
}
```

---

## Diagnosing suspicious results

If `total_record_count` is 0, or results contain unexpectedly all-NULL columns, consult **`.claude/skills/ask-graph/references/cypher-query-debugging.md`** for diagnostic Cypher queries. Common causes:

- **All-NULL column** — wrong relationship or node property name (the LLM guesses; use `keys(r)` to find the real name)
- **0 rows with a filter** — threshold may be outside the actual value range; check with `min()`/`max()` before revising
- **0 rows without a filter** — the entity may have no relationships of that type, or the direction is reversed
- **Write operations** — `CREATE`, `MERGE`, `SET`, `DELETE` are blocked; only `MATCH`/`RETURN` queries are allowed
