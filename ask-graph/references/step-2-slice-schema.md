# Step 2 — Slice the schema

Extract only the schema subset relevant to the entities identified in Step 1. Use progressive mode to get a lightweight semantic index first, then read full property details for each relevant node and relationship type before generating Cypher.

**Build `node_labels`** from the unique `entity_type` values collected in Step 1. Include all node types that appear in the query, even those not explicitly tagged (e.g. add `"Patient"` if the query asks about patients but it was not tagged as an entity).

## Step 2a — Slice (progressive mode)

```
uv run python -m ai_oncology.graph_client slice_schema '{
  "database_name": "<database>",
  "node_labels": <node_labels derived from Step 1>,
  "detail_level": "progressive"
}' > $output_dir/step2_slice.json
```

Output is saved to `$output_dir/step2_slice.json` for troubleshooting. Process the output inline — do not re-read the file unless debugging.

**What to retain from the output:**
- `schema_context_id` — passed to `generate_cypher`; identifies the schema slice stored server-side
- `included_nodes` — node types included in the slice
- `included_relationships` — relationship types connecting the requested nodes

> `schema_context_id` is stored server-side and is only valid within the same MCP server session. It cannot be reused across sessions or separate `graph_client` invocations that use a different `task_id`.

---

## Step 2b — Feasibility check (mandatory before proceeding)

**Before reading schema details**, critically examine whether `included_relationships` can actually answer the user's question.

Map each data requirement implied by the question to a relationship type in `included_relationships`. Be specific — do not assume a relationship exists because it sounds plausible.

| If the user's question requires... | Check for... |
|------------------------------------|--------------|
| Mutation data (e.g. G12C, G12V) | `HAS_MUTATION`, `HAS_VARIANT`, or similar |
| Drug response / treatment | `TREATED_WITH`, `RESPONDS_TO`, or similar |
| Pathway membership | `IS_MEMBER_OF`, `PART_OF`, or similar |
| Gene essentiality / CRISPR | `HAS_GENE_ESSENTIALITY` |
| Expression | `EXPRESSES` |
| Methylation | `HAS_METHYLATION_*` |

**If a required relationship is missing**, revise the question to use what is available, record the revision, and continue. Do not stop to ask the user — report the revision in Step 6. See `step-1-annotate.md` for guidance on how to re-annotate with the revised question if entity types have changed as a result.

---

## Step 2c — Read schema details (mandatory before generate_cypher)

The progressive slice returns a lightweight semantic index — it does **not** include full property schemas. You must read the full detail for every node type and relationship type that will appear in the query before calling `generate_cypher`. Skipping this causes property name hallucinations (e.g. `r.score` instead of `r.ESSENTIALITY_SCORE`).

**For each node type in `included_nodes`:**
```
uv run python -m ai_oncology.graph_client read_schema_detail '{
  "database_name": "<database>",
  "detail_type": "node",
  "name": "<NodeType>"
}' > $output_dir/step2_detail_node_<NodeType>.json
```

**For each relationship type in `included_relationships`:**
```
uv run python -m ai_oncology.graph_client read_schema_detail '{
  "database_name": "<database>",
  "detail_type": "relationship",
  "name": "<RelType>"
}' > $output_dir/step2_detail_rel_<RelType>.json
```

After reading all details, `generate_cypher` has accurate property names and can be called safely.
