# SPEDAS Codex plugin

`spedas_codex` is a standalone Codex plugin wrapper for the official
[SPEDAS MCP](https://github.com/spedas/spedas_mcp). It packages the MCP
connection and Codex-facing research instructions so Codex can use SPEDAS tools
without embedding SPEDAS logic in each project.

## What this repo provides

- `.codex-plugin/plugin.json` — plugin metadata for Codex-style plugin loaders.
- `.mcp.json` — starts the `spedas` MCP server from `spedas/spedas_mcp` via `uvx`.
- `AGENTS.md` — repo-level operating instructions for Codex.
- `skills/spedas-workflow/SKILL.md` — portable SPEDAS workflow guidance.
- `examples/prompts.md` — suggested prompts and expected tool flow.

## Relationship to `spedas_mcp`

```text
Codex -> spedas_codex plugin -> spedas MCP server -> CDAWeb / PDS / SPICE backends
```

The MCP presents a unified SPEDAS data layer by `source_type` (`cdaweb`, `pds`,
`spice`) plus higher-level science workflow tools. Treat `xhelio-*` as internal
backend packages unless you are maintaining the MCP itself.

## Requirements

- Codex CLI/runtime with MCP/plugin support.
- `uvx` available on `PATH`.
- Network access the first time `uvx` installs `spedas_mcp` from GitHub.

## Quick smoke prompt

```text
Use the SPEDAS MCP to compare CDAWeb, PDS, and SPICE for a Juno magnetic-field
analysis near Jupiter. Do not download large data; produce a plan and provenance.
```

## Local validation

```bash
python scripts/validate_plugin.py
python scripts/smoke_mcp_runtime.py --json
```

`validate_plugin.py` is network-free and checks wrapper structure plus MCP
reference. `smoke_mcp_runtime.py` is a real stdio MCP runtime smoke: it starts
the configured `spedas` server, performs `initialize` + `tools/list`, and verifies
the core SPEDAS tools without private credentials, interactive UI, data fetches,
or SPICE kernel downloads. It may need public network access the first time `uvx`
installs `spedas_mcp`.
