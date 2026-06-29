# SPEDAS Codex plugin

`spedas_codex` is a thin standalone Codex plugin wrapper for the official
[SPEDAS Agent Kit](https://github.com/spedas/spedas_agent_kit) core. It packages the MCP
connection and Codex-facing research instructions so Codex can use SPEDAS tools
without owning or duplicating the Agent Kit science logic/skills.

## What this repo provides

- `.codex-plugin/plugin.json` — plugin metadata for Codex-style plugin loaders.
- `.mcp.json` — starts the `spedas-agent-kit` MCP server from `spedas/spedas_agent_kit` via `uvx`.
- `AGENTS.md` — repo-level operating instructions for Codex.
- `skills/spedas-workflow/SKILL.md` — portable SPEDAS workflow guidance.
- `examples/prompts.md` — suggested prompts and expected tool flow.

## Relationship to `spedas_agent_kit`

```text
Codex -> spedas_codex plugin -> spedas-agent-kit MCP server -> CDAWeb / PDS / SPICE backends
```

The MCP presents a unified SPEDAS data layer by `source_type` (`cdaweb`, `pds`,
`spice`) plus higher-level science workflow tools. Treat `xhelio-*` as internal
backend packages unless you are maintaining the MCP itself.

## Requirements

- Codex CLI/runtime with MCP/plugin support.
- `uvx` available on `PATH`.
- Network access the first time `uvx` installs `spedas_agent_kit` from GitHub. This wrapper pins `spedas_agent_kit` to `52ccfcb0384dd71fa224bdc65ce813d0fa60a5c7` and bounds the MCP protocol dependency as `mcp>=1.26.0,<2`.

## Quick smoke prompt

```text
Use the SPEDAS Agent Kit MCP to compare CDAWeb, PDS, and SPICE for a Juno magnetic-field
analysis near Jupiter. Do not download large data; produce a plan and provenance.
```

## Local validation

```bash
python scripts/validate_plugin.py
python scripts/smoke_mcp_runtime.py --json
```

`validate_plugin.py` is network-free and checks wrapper structure plus MCP
reference and enforces the pinned `spedas_agent_kit` SHA plus bounded MCP dependency. `smoke_mcp_runtime.py` is a real stdio MCP runtime smoke: it starts
the configured `spedas` server, performs `initialize` + `tools/list`, and verifies
the current 17-tool base SPEDAS surface without private credentials, interactive UI, data fetches,
or SPICE kernel downloads. It may need public network access the first time `uvx`
installs `spedas_agent_kit`.

## Real Codex CLI smoke

Validate the package structure and the MCP runtime command first:

```bash
python scripts/validate_plugin.py
python scripts/smoke_mcp_runtime.py --json
```

Then ask Codex CLI to try the wrapper without editing files:

```bash
codex exec --cd . --sandbox workspace-write   "Validate the SPEDAS Codex wrapper. Prefer live MCP tools if this Codex build exposes them; otherwise run the safe runtime smoke and summarize evidence. Do not edit files or fetch data."
```

Depending on Codex CLI version/config, `.mcp.json` may not automatically expose MCP tools inside the agent session. In that case, `scripts/smoke_mcp_runtime.py --json` is the authoritative wrapper check: it starts the same `uvx ... spedas-agent-kit` command from `.mcp.json`, performs MCP initialize + tools/list, and verifies core SPEDAS tools.

The runtime smoke isolates SPEDAS data caches and falls back to temporary `uv`/XDG/tmp caches when the default cache location is not writable. This is important in Codex sandboxes and CI. First runs may be slow because `uvx` resolves the pinned `spedas_agent_kit` commit from GitHub. Expected smoke evidence is `ok: true`, `tool_count: 17`, and an empty `missing_core_tools` list.
