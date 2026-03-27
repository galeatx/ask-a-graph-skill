---
name: biomedical-literature-search
description: Search and summarize scientific literature using a private API. Use this skill whenever a research task involves finding scientific papers, medical literature, biological mechanisms, clinical studies, or any evidence-based research question. This takes priority over WebFetch — do not use web search when this skill is more effective and applicable to the user query.
---

# Biomedical Literature Search

Search, prefilter, and summarize biomedical literature using a three-module pipeline. Produces a markdown summary report of the most relevant articles for a given research question.

## Pipeline

The search runs three modules **in sequence**. Each module must succeed for the next to proceed:

```
search  →  prefilter  →  summarize
```

1. **Search** — queries the literature API (`/search`) with a natural-language question, returns up to `max_n_search` candidate articles (default: 500).

2. **Prefilter** — sends candidates to the LLM-based filter API (`/filter`), which classifies and selects the top `max_n_filter` articles (default: 20) most relevant to the query. An optional `filter_query` string provides additional selection criteria (e.g., "human studies only", "published after 2015"). If no `filter_query` is provided, relevance is judged from the search query alone.

3. **Summarize** — sends the filtered articles to the summarization API (`/summarize`), producing a markdown report saved to `<base_dir>/<timestamp>/summary_report.md`.

The pipeline short-circuits with a failure message if either **search** or **prefilter** return zero articles.

**If the pipeline fails, retry with a broader query before giving up.** Broaden based on which module failed:
- **Search failed** — rewrite `query` to be more general (e.g., remove specific drug names, gene variants, or narrow timeframes; use broader disease or mechanism terms).
- **Prefilter failed** — relax or remove `filter_query` (e.g., drop year constraints, widen study type from "clinical trials" to "human studies", or remove it entirely). If prefilter still fails after relaxing `filter_query`, also broaden `query` as above.

Retry up to **3 times**, each time making the query or filter criteria more permissive than the previous attempt. If you are unsure how to further broaden the query or filter criteria, stop and ask the user for guidance — and suggest removing `filter_query` entirely as the last resort. If all retries fail, report that no relevant articles were found.

## Usage

**Before writing an input file, read all example inputs:**
```
.claude/skills/biomedical-literature-search/examples/
```
Use them as a reference for how `query` and `filter_query` should be phrased. Do not copy them directly — write a new input file tailored to the current research question.

**Write the input file to `${session_dir}/files/temp/input.json`** before running the script. Set `base_dir` in the input to `${session_dir}/files/research_notes/` so output lands in the correct location.

Use the **Bash tool** to run the script — do NOT use the Skill tool for this step:

```bash
uv run --directory /mnt/c/Users/JIHX/Documents/Projects/ai-oncology .claude/skills/biomedical-literature-search/scripts/search_literature_internal.py -i ${session_dir}/files/temp/input.json
```

## Input JSON

**Required:**

| Key | Type | Description |
|-----|------|-------------|
| `query` | string | Natural-language research question (see query guidance below) |
| `base_dir` | string | Full absolute path for output — must be resolved to a real path before running (e.g. `/home/user/project/research_notes`). `${session_dir}` used in examples is a placeholder only and must not be used literally. |

**Optional:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `filter_query` | string | `null` | Additional criteria for the prefilter step, written as a plain instruction (see query guidance below) |
| `max_n_search` | int | 500 | Max articles retrieved by the search module — do not lower this unless explicitly asked; a smaller pool makes filtering more likely to return zero results |
| `max_n_filter` | int | 20 | Max articles selected by the prefilter module |
| `save_articles` | bool | `false` | If true, also saves filtered articles to `articles.json` |

### Examples

Before writing an input file, read the examples in `.claude/skills/biomedical-literature-search/examples/` to understand correct query formatting. The files under `examples/` use `${session_dir}` as a placeholder in `base_dir` — **do not use `${session_dir}` literally**; replace it with the actual absolute path for the current run.

### Query guidance

**`query`** must be a well-formed natural language question or sentence — not a list of keywords. It should be something a human researcher would actually ask or write.

- **Good:** `"What is the role of IL-6 in promoting metastasis in solid tumors?"`
- **Bad:** `"IL6 cancer metastasis signaling tumor"`

When broadening after a failed run, simplify the question — make it shorter or remove specifics — but keep it as a natural-language sentence. Never degrade to a keyword string.

- **Good broadening:** `"What is the role of ferroptosis in liver cancer?"` (simplified from a longer question)
- **Bad broadening:** `"ferroptosis cancer"` (keyword degradation — not a sentence)

**`filter_query`** must be a single plain sentence describing one criterion for what to keep. It should be a soft relevance guide — not a strict checklist. Do not stack multiple constraints.

- **Good:** `"Focus on human clinical studies published after 2015."`
- **Good:** `"Prioritize studies that report quantitative microbiome data."`
- **Bad (keywords):** `"human clinical 2015 RCT"`
- **Bad (stacked, multi-sentence):** `"Focus on quantitative studies with statistical data and effect sizes. Include both Crohn's disease and ulcerative colitis. Prioritize recent publications."` — each constraint eliminates articles; stacking them leaves almost nothing.
- **Bad (stacked, single sentence):** `"Prioritize human clinical studies and mechanistic research that report quantitative microbiome data and IBD outcomes."` — multiple criteria joined with "and" is still stacking; each "and" is a red flag.

If you have no meaningful single criterion to add, omit `filter_query` entirely rather than forcing one.

### Example

Write to `${session_dir}/files/temp/input.json`:
```json
{
    "query": "What is the role of IL6 in cancer metastasis?",
    "base_dir": "${session_dir}/files/research_notes",
    "filter_query": "focus on human clinical studies published after 2015",
    "save_articles": true
}
```

## Output

All output is written to `<base_dir>/<YYYYMMDD_HHMMSS>/`:

| File | Description |
|------|-------------|
| `input.json` | Copy of the input file (for reproducibility) |
| `summary_report.md` | Markdown report generated by the summarize module |
| `articles.json` | Filtered articles with metadata (only if `save_articles: true`) |

## After the Search

Once the script completes successfully, `summary_report.md` is written to `<base_dir>/<timestamp>/`. Always set `base_dir` to `${session_dir}/files/research_notes/` so the output lands in the correct location.

Then:
1. Glob for the report: pattern `${session_dir}/files/research_notes/*/summary_report.md`
2. Move **only** `summary_report.md` one level up with a meaningful name: `mv <found_path> ${session_dir}/files/research_notes/{topic_name}.md`
   - Do NOT move or copy `articles.json` or any other file — they stay in the timestamped subdirectory
3. Return control to the caller — the report is now at `${session_dir}/files/research_notes/{topic_name}.md`

## Failure Modes

| Module | Failure condition | Behavior |
|--------|------------------|----------|
| Search | No articles found | Exits early; no prefilter or summarize |
| Prefilter | No articles pass filtering | Exits early; no summarize |
| Any | Non-200 API response | Raises `RuntimeError` with status and detail |
