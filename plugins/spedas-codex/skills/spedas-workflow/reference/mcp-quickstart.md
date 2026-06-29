# SPEDAS Agent Kit MCP quickstart

## Claude Code smoke

From the `spedas_claude` repository:

```bash
claude -p   --plugin-dir .   --mcp-config .mcp.json   --allowedTools mcp__spedas__spedas_overview,mcp__spedas__browse_data_sources,mcp__spedas__plan_spedas_observation   "Use the SPEDAS Agent Kit MCP for a safe metadata-only MMS planning smoke. Do not fetch data."
```

Expected: Claude initializes the `spedas` MCP server and can call `spedas_overview`, `browse_data_sources`, and `plan_spedas_observation`.

## Codex smoke

From the `spedas_codex` repository:

```bash
python scripts/validate_plugin.py
python scripts/smoke_mcp_runtime.py --json
```

Then try Codex CLI:

```bash
codex exec --cd . --sandbox workspace-write   "Validate the SPEDAS Codex wrapper without editing files. Prefer the MCP if available; otherwise run the safe runtime smoke and summarize evidence."
```

Depending on Codex CLI version/config, `.mcp.json` may not automatically expose MCP tools in the interactive session. The runtime smoke is the authoritative wrapper check because it starts the same pinned `uvx ... spedas-agent-kit` command from `.mcp.json` and performs MCP initialize + tools/list. Expected current-base evidence: `ok: true`, a `tool_count` of at least the 13 base tools, and no missing core tools. The direct HAPI/FDSN tools are not in this default surface (Agent Kit #87/#145); set `SPEDAS_AGENT_KIT_DATASOURCE_TOOLS=1` to advertise them, and `SPEDAS_AGENT_KIT_COMPAT_TOOLS=1` for the legacy CDAWeb/PDS compat tools.

## Safe first question

Ask for planning, not data download:

> Which SPEDAS Agent Kit MCP tools and data sources should I use for an MMS magnetopause interval around 2015-10-16T13:06Z? Do not fetch data yet.

