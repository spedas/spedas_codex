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

The runtime smoke is the authoritative wrapper/runtime check because it starts the
same pinned `uvx ... spedas-agent-kit` command from `.mcp.json` and performs MCP
initialize + tools/list plus resources/list/read for packaged skills. Expected
current-base evidence: `ok: true`, a `tool_count` of at least the 13 base tools,
no missing core tools, and readable `spedas-skill://index` /
`spedas-skill://skills/spedas-workflow` resources. The direct HAPI/FDSN tools are
not in this default surface (Agent Kit #87/#145); set
`SPEDAS_AGENT_KIT_DATASOURCE_TOOLS=1` to advertise them, and
`SPEDAS_AGENT_KIT_COMPAT_TOOLS=1` for the legacy CDAWeb/PDS compat tools.

## MCP skill resources

The current Agent Kit pin exposes packaged workflow skills as read-only MCP
resources while keeping `tools/list` compact:

- `spedas-skill://index` — markdown index of bundled skills.
- `spedas-skill://skills/spedas-workflow` — primary workflow skill body.

Use `list_resources` to discover the full catalog and `read_resource` on a
`spedas-skill://skills/<name>` URI when a Codex session needs deeper workflow
guidance than the tool schemas alone provide.

## Event preset and provenance resources

Recent Agent Kit pins also expose paper/event reproduction scaffolding as MCP
resources without expanding `tools/list`:

- `spedas-preset://index` — event/paper preset catalog; read it before
  hand-authoring time ranges for known solar-wind or magnetospheric events.
- `spedas-preset://events/<id>` — one preset record with interval, labels,
  recommended skills, and caveats.
- `spedas-preset://schemas/reproduction_provenance` — canonical JSON schema for
  run provenance emitted by paper/event reproduction workflows.

If a Codex runtime exposes tools but not resources interactively, keep the run
artifact-first and state that the preset/schema resource could not be read rather
than fabricating provenance fields from memory.

## Publishing / installing for Codex

Use the same marketplace package shape as this repo:

```text
.agents/plugins/marketplace.json
plugins/spedas-codex/.codex-plugin/plugin.json
plugins/spedas-codex/.mcp.json
plugins/spedas-codex/skills/...
```

For a repo/team marketplace, install the marketplace and then the plugin:

```bash
codex plugin marketplace add owner/repo
codex plugin marketplace add owner/repo --ref main
codex plugin marketplace add https://github.com/spedas/spedas_codex.git
codex plugin add spedas-codex@<marketplace-name>
```

For this repository:

```bash
codex plugin marketplace add spedas/spedas_codex --ref main
codex plugin add spedas-codex@spedas
```

For personal testing, copy/adapt this repo's `.agents/plugins/marketplace.json` as
a local marketplace entry such as `~/.agents/plugins/marketplace.json`, pointing it
at the local `plugins/spedas-codex` package. Codex app sharing is workspace-scoped
and separate from marketplace publishing; use **Plugins -> Created by you -> Share** for ad hoc workspace sharing.

## Codex Desktop MCP tool exposure

Codex Desktop can load the bundled `spedas-codex:spedas-workflow` skill without
attaching the plugin-provided MCP server to the current thread. Treat these as two
separate checks:

1. `python scripts/smoke_mcp_runtime.py --json` verifies the wrapper can start the
   `spedas` MCP server and list tools.
2. A fresh Codex Desktop thread must expose callable tools named like
   `mcp__spedas__spedas_overview`, `mcp__spedas__browse_data_sources`,
   `mcp__spedas__plan_spedas_observation`, and `mcp__spedas__fetch_data_product`.

After installing or upgrading `spedas-codex@spedas`, fully restart Codex Desktop
and start a new thread before expecting the MCP tools. Existing threads can keep a
stale tool surface.

If only the skill is visible and no `mcp__spedas__...` tools appear, confirm or
add this plugin-scoped block in `~/.codex/config.toml`, then restart Codex and
open a new thread:

```toml
[plugins."spedas-codex@spedas"]
enabled = true

[plugins."spedas-codex@spedas".mcp_servers.spedas]
enabled = true
default_tools_approval_mode = "prompt"
```

A no-fetch first verification prompt for the new thread:

> Use the SPEDAS MCP tool `spedas_overview` to summarize the available SPEDAS
> Agent Kit tool surface. Do not fetch data. If no `mcp__spedas__...` tools are
> attached, say so explicitly and do not fall back to a data download.

## Safe first question

Ask for planning, not data download:

> Which SPEDAS Agent Kit MCP tools and data sources should I use for an MMS magnetopause interval around 2015-10-16T13:06Z? Do not fetch data yet.
