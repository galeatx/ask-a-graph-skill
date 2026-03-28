# Skill Testing Setup

This repo contains the client-side code and Claude Code skills for querying the ask-a-graph MCP server and the biomedical literature search API.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- Access to the `ask-a-graph-mcp` repository (for the MCP server)

## 1. Install dependencies

From the repo root:

```bash
uv sync
```

## 2. Start the MCP server

From your local `ask-a-graph-mcp` repository:

```bash
# Option A: Docker (recommended)
docker-compose up -d

# Option B: Direct launch
python -m ask_a_graph.mcp.server --mode http --host 0.0.0.0 --port 8627
```

Verify the server is running:

```bash
curl http://localhost:8627/health
```

## 3. Verify the graph client

From this repo's root, confirm the client can reach the MCP server:

```bash
uv run python -m ai_oncology.graph_client --list-tools
```

This should print the list of available MCP tools. If it fails, check that the server is running on port 8627.

## 4. Install the skills in Claude Code

Copy the two skill directories into your project's `.claude/skills/`:

```bash
cp -r .claude/skills/ask-graph /path/to/your/project/.claude/skills/
cp -r .claude/skills/biomedical-literature-search /path/to/your/project/.claude/skills/
```

If you are testing directly from this repo, the skills are already in place.

## 5. Use the skills

Launch Claude Code from the repo root:

```bash
claude
```

Claude Code auto-discovers skills in `.claude/skills/`. You can now ask questions that trigger them:

- **ask-graph** — research questions over the knowledge graph, e.g. *"What genes are frequently mutated in NSCLC patients?"*
- **biomedical-literature-search** — literature queries, e.g. *"What is the role of IL-6 in promoting metastasis in solid tumors?"*

## Repo structure

```
src/ai_oncology/graph_client.py    # CLI client that calls the MCP server over SSE
.claude/skills/ask-graph/          # Graph query skill (multi-step Cypher pipeline)
.claude/skills/biomedical-literature-search/  # Literature search + summarization skill
pyproject.toml                     # Project dependencies
```
