---
name: ask-graph
description: Query domain-specific Neo4j knowledge graphs containing clinical and biomedical data using natural language. Use when the user asks research questions about patients, genes, cancer types, or multi-omics data (gene expression, copy number variation, DNA methylation, mutational signatures, CRISPR essentiality) that may be encoded in a predefined list of available databases.
---

# Ask-A-Graph Skill

Query domain-specific Neo4j knowledge graphs containing clinical and biomedical data
using natural language via the ask-a-graph-mcp server. This skill supports research
questions over patient-level multi-omics data (gene expression, copy number variation,
DNA methylation, mutational signatures, CRISPR essentiality) as well as other
biomedical knowledge graphs.

---

## Prerequisites

**Step 0 (setup)** uses a dedicated script — NOT graph_client:
```
uv run python .claude/skills/ask-graph/scripts/setup.py $output_dir
```

**Steps 1–6** use the graph_client module:
```
uv run python -m ai_oncology.graph_client <tool_name> '<json_args>'
```

If Step 0 reports an unhealthy server or no database connections, do not attempt to fix it yourself — inform the user and ask them to contact the administrator to verify the MCP server is running.

**Latency:** `graph_client` commands can take anywhere from a few seconds to several minutes depending on LLM call volume and Neo4j query execution speed. **Always wait for a command to finish before proceeding.** Do NOT launch additional Bash processes to probe, debug, or check on a running command. If a command is taking unusually long (>3 minutes), inform the user and ask whether to keep waiting or abort.

---

## Directories

Two directories are used — create both before running any step.

**Step 1:** Get the current timestamp:
```bash
date +%Y%m%d_%H%M%S
```

**Step 2:** Create both directories using the timestamp output from Step 1. Replace `<ts>` with the actual value:
```bash
mkdir -p "${session_dir}/files/graph_results" "${session_dir}/files/graph_results/<ts>"
```

- **`setup_dir`** — fixed shared path: `${session_dir}/files/graph_results/`. `setup_complete.json` always lives here, shared across all graph analyst invocations in the same session.
- **`output_dir`** — timestamped subdirectory for this query's artifacts: `${session_dir}/files/graph_results/<ts>/`. All step outputs (step1–step6, probes) go here.

**The `output_dir` name is the timestamp — do not change it.** Do not use semantic names like `kras_analysis` or `lung_cancer_query`. The format is always `YYYYMMDD_HHMMSS`.

`${session_dir}` is provided by the agent's system prompt — do not use it literally; it will be substituted at runtime.

---

## Database selection

**Before doing anything else**, read `.claude/skills/ask-graph/references/databases.md` and decide which database to query based on the user's question. Use that database name for all subsequent steps.

---

## Workflow

For each step below, **read the reference file before executing**. Check each box as you go:

- [ ] **Step 0** — Read `.claude/skills/ask-graph/references/step-0-setup.md`
- [ ] **Step 1** — Read `.claude/skills/ask-graph/references/step-1-annotate.md`
- [ ] **Step 2** — Read `.claude/skills/ask-graph/references/step-2-slice-schema.md`
- [ ] **Step 3** — Read `.claude/skills/ask-graph/references/step-3-disambiguate.md`
- [ ] **Step 4** — Read `.claude/skills/ask-graph/references/step-4-generate-cypher.md`
- [ ] **Step 5** — Read `.claude/skills/ask-graph/references/step-5-execute.md`
- [ ] **Step 6** — Read `.claude/skills/ask-graph/references/step-6-results.md`

Do not proceed to a step until you have read its reference file in this session. Do not skip based on memory or prior runs.

| Step | Description | Tool | Key Inputs | Key Outputs | Output File |
|------|-------------|------|------------|-------------|-------------|
| 0 | One-time session setup — verify server, connections, schema cache | `setup.py` | `$setup_dir` | `setup_complete` flag | `setup_complete.json` |
| 1 | Fetch entity and relationship types; revise question if required data is unavailable (Step 1b); annotate and expand the confirmed question (Step 1c) | `list_entity_types` (with relationships) → *(revision if needed)* → `user_query_annotation_and_expansion` | `database_name`; `node_labels` + `relationship_types`; original or revised question | `annotated_query`, `entities[].entity_type`, `entities[].classification`, `entities[].variations` | `step1_annotation.json` |
| 2 | Slice the schema (progressive mode); run feasibility check (Step 2b); read full schema detail for every node and relationship type (Step 2c) — mandatory before generate_cypher | `slice_schema` (progressive) → `read_schema_detail` × N | `database_name`, `node_labels` (from Step 1 `entity_type` values) | `schema_context_id`, `included_relationships`, full property schemas | `step2_slice.json`, `step2_detail_*.json` |
| 3 | Resolve instance entities against the graph — find candidates, apply selections | `identify_disambiguation_candidates` → `apply_entity_selections` | instance `entities[]` (Step 1), `schema_context_id` (Step 2), `user_query` | `session_id`, `resolved_entities` (with Neo4j node IDs) | `step3a_candidates.json`, `step3b_resolved.json` |
| 4 | Generate Cypher query — translate user question into a grounded Cypher query | `generate_cypher` | `user_question`, `database_name`, `schema_context_id` (Step 2, must be fresh), `resolved_entities` (Step 3) | `cypher_query`, `parameters`, `explanation` | `step4_cypher.json` |
| 5 | Execute the Cypher query — run against the database; results stored server-side to protect context | `execute_cypher` | `database_name`, `cypher_query`, `parameters` (Step 4) | `storage_object_id`, `record_count` | `step5_execute.json` |
| 6 | Retrieve and present results, then write artifacts to disk — summarize key findings critically (format as table if tabular; note truncation if applicable), write query metadata and a natural language analysis to disk. Do not generate extra files. | `summarize_results` | `storage_object_id` (Step 5) | `records`, `record_count`, `truncated` | `step6_results.json`, `query_metadata.json`, `summary.md` |
