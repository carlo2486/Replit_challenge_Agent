---
name: Arena project layout
description: Where files live and how to run arena commands without hitting the git lock
---

## Persisted project root: `/home/runner/workspace/`
```
workspace/
  arena.yaml            — competition config (name, competition, agent, environment)
  arena_start.sh        — session restore script (run at start of every session)
  mcp/corpus-search/    — MCP server with all tools
    server.py           — tools: list_bulletins, find_bulletins_for_period, search_corpus,
                          search_files, search_bulletin, read_bulletin, extract_tables,
                          extract_column_values, calculate, linear_regression, write_answer
    mcp.toml            — fastmcp entrypoint
  prompts/system.j2     — Jinja2 system prompt with task-type playbook
  skills/treasury-domain.md — Treasury Bulletin domain knowledge
  .arena/               — arena CLI venv + credentials (all persisted here)
    bin/arena           — wrapper script → .arena/venv/bin/arena
    credentials         — auth token (persistent copy)
    venv/               — Python 3.13 venv with all arena wheels
```

## Run commands from `/tmp/arena-project/` NOT from workspace
The workspace is a git repo. `arena doctor`, `arena pull`, `arena submit` trigger git operations that hit `.git/index.lock` (Replit checkpoints lock it). Running from `/tmp/arena-project/` (which has symlinks to workspace files) avoids this.

```bash
cd /tmp/arena-project
arena doctor   # check everything
arena pull     # download samples
arena submit   # submit to Arena infra (local arena test fails — needs 8GB RAM)
arena history  # check submission status + scores
```

## arena.yaml schema (v1)
Required fields: `name` (alphanumeric+-_), `competition`, `agent`.
Timeout goes under `environment.timeout_per_task` (max 900).
```yaml
name: office-qa-agent
competition: office-qa
agent:
  harness_name: "opencode"
  model: "openrouter/deepseek/deepseek-r1:free"
  prompt_template_path: "prompts/system.j2"
  skills_dir: "skills/"
  mcp_dir: "mcp/"
environment:
  timeout_per_task: 900
```

## Local testing
`arena test` (even `--smoke`) fails locally — Docker containers need 8 GB, Replit caps at 4 GB.
Always submit directly with `arena submit`. 1 submission per day quota.

**Why:** The corpus-search MCP server and all project files are in workspace; /tmp symlinks let arena see them without git interference.
