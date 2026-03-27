# Step 1 — Annotate and expand the user query

## Step 1a — Fetch entity and relationship types

```
uv run python -m ai_oncology.graph_client list_entity_types '{
  "database_name": "<database>",
  "include_relationships": true
}'
```

**What to retain:**
- `node_labels` — passed as `entity_types` in Step 1c; use the full list
- `relationship_types` — used in Step 1b to assess whether the user's question is answerable

---

## Step 1b — Revise the question if needed

For each data type or action implied by the user's question, check whether a corresponding relationship exists in `relationship_types`:

| If the question implies... | Look for... |
|---------------------------|-------------|
| Mutation / variant data | `HAS_MUTATION`, `HAS_VARIANT` |
| Drug treatment / response | `TREATED_WITH`, `RESPONDS_TO`, `APPROVED_TREATMENT_FOR` |
| Gene expression | `EXPRESSES`, `AFFECTS_EXPRESSION` |
| Pathway membership | `IS_MEMBER_OF`, `PART_OF` |
| CRISPR / essentiality | `HAS_GENE_ESSENTIALITY` |
| Methylation | `HAS_METHYLATION_*` |
| Copy number | `HAS_COPY_NUMBER_VARIANT` |
| Side effects | `HAS_SIDE_EFFECT` |
| Protein interactions | `PROTEIN_PROTEIN_INTERACTIONS` |

**If all required relationships exist** → proceed to Step 1c with the original question unchanged.

**If a required relationship is missing**, determine the severity of the gap:

**Minor revision** — the core intent is still answerable, only a specific detail is unavailable (e.g. a specific variant when the gene itself is present):
1. Revise the question to drop the unavailable detail
2. Record the revision for Step 6
3. Proceed to Step 1c silently

**Major revision** — the core premise of the question cannot be answered (e.g. mutation question when no mutation relationship exists):
1. Record both the original and revised question for Step 6
2. Output a single sentence announcing what you are doing, then immediately proceed to Step 1c — do not pause, do not ask for approval

The announcement is informational only. Format it as a statement of intent, not a question:
> *"Mutation data is not available in this database — querying KRAS expression and essentiality scores as proxies for KRAS dependency instead."*

The Cypher generation agent has full schema context and may further adjust interpretation. Trust the pipeline.

---

## Step 1c — Annotate and expand the confirmed question

```
uv run python -m ai_oncology.graph_client user_query_annotation_and_expansion '{
  "query": "<original or revised question from Step 1b>",
  "entity_types": <node_labels from Step 1a>
}' > $output_dir/step1_annotation.json
```

Output is saved to `$output_dir/step1_annotation.json` for troubleshooting. Process the output inline — do not re-read the file unless debugging.

**What to retain from the output:**
- `annotated_query` — the query with entity placeholders (e.g. `{GENE_INSTANCE_1}`); passed to `generate_cypher` later
- `entities[]` — each entity's `annotation_tag`, `entity_type`, `classification`, `normalized_text`, and `variations`

**Derive `node_labels` for Step 2** from `entities[]` by collecting the unique `entity_type` values from all entities.
