# Step 6 — Retrieve, present, and save results

Fetch the stored query results, present key findings to the user, then write artifacts to disk.

**Quality over quantity. You MUST write exactly these three files and nothing else:**
- `step6_results.json` — written by the `summarize_results` command
- `query_metadata.json` — written manually using the Write tool
- `summary.md` — written manually using the Write tool

Do NOT create any other files. This means no `README.md`, no `KEY_FINDINGS.txt`, no `COHORT_SUMMARY.md`, no `.csv` exports, no additional `.json` files. If you find yourself about to write a file not on this list — stop.

Think critically before writing the summary: do not just restate the data, interpret it.

---

## Step 6a — Retrieve and present results

```
uv run python -m ai_oncology.graph_client summarize_results '{
  "storage_object_id": "<storage_object_id from Step 5>"
}' > $output_dir/step6_results.json
```

**What to retain from the output:**
- `records` — the full query results
- `record_count` — total number of records returned
- `truncated` — whether the result set was cut off

**Presenting results to the user:**
- If results contain tabular data (rows with consistent fields), format as a markdown table
- If `truncated` is true, state: *"Showing [N] of [record_count] total results."*
- If `record_count` is 0, inform the user: *"The query returned no results."* — suggest narrowing or rephrasing the question, or exploring related entity types

---

## Step 6b — Save query metadata

Write `query_metadata.json` to `$output_dir` using the Write tool:

```json
{
  "user_question": "<original user question>",
  "interpreted_question": "<revised question from Step 1b, or same as user_question if no revision>",
  "revision_rationale": "<one sentence explaining the revision, or null if unchanged>",
  "database_name": "<database queried>",
  "cypher_query": "<cypher_query from Step 4>",
  "cypher_explanation": "<explanation field from Step 4>",
  "parameters": "<parameters from Step 4>",
  "record_count": "<record_count from Step 6a>"
}
```

---

## Step 6c — Save natural language summary

Write `summary.md` to `$output_dir` using the Write tool.

**Always open with the query audit trail**, so the user can see exactly how their question was handled:

```
## How your question was answered

**Original question:** <what the user asked>
**Interpreted as:** <revised question if Step 1b changed it, otherwise same as above>
**Rationale:** <one sentence explaining any revision — or "no revision needed" if unchanged>
**Query:** <plain-English description of what the Cypher query actually retrieved, from the explanation field in Step 4>
```

**Then interpret the results critically.** Do not simply restate the numbers. A good summary:
- Interprets what the results mean in the biological or clinical context of the user's question
- Flags unexpected, suspicious, or counter-intuitive findings
- Notes limitations — thresholds used, subtypes excluded, what was not captured
- Distinguishes signal from noise
- States clearly if results are truncated by a `LIMIT` and what that means for interpretation

---

## Step 6d — Exporting / downloading results

If the user asks to download results, export to CSV, or get a download link:

1. Call `export_results` with the `storage_object_id` from Step 5
2. The tool returns a `download_link` — present that URL to the user
3. **Never construct or guess a download URL yourself** — always use `export_results`
4. If Step 5 has not been run yet, run the full query first to obtain a `storage_object_id`

```
uv run python -m ai_oncology.graph_client export_results '{
  "storage_object_id": "<storage_object_id from Step 5>"
}'
```

---

## Completion

Inform the user:

> *"Results saved to `$output_dir/`"*

with a brief listing of what was written:
- `step6_results.json` — full result records
- `query_metadata.json` — query details and record count
- `summary.md` — critical analysis & summary of findings
