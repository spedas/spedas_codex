# SPEDAS Codex plugin

`spedas_codex` is a thin standalone Codex plugin wrapper for the official
[SPEDAS Agent Kit](https://github.com/spedas/spedas_agent_kit) core. It packages the MCP
connection and Codex-facing research instructions so Codex can use SPEDAS tools
without owning or duplicating the Agent Kit science logic/skills.

## What this repo provides

- `.agents/plugins/marketplace.json` — repo-scoped Codex marketplace catalog for `codex plugin marketplace add spedas/spedas_codex --ref main`.
- `plugins/spedas-codex/` — the conventional marketplace plugin package that Codex should discover/install:
  - `.codex-plugin/plugin.json` — plugin metadata for Codex-style plugin loaders.
  - `.mcp.json` — starts the `spedas-agent-kit` MCP server from `spedas/spedas_agent_kit` via `uvx`.
  - `AGENTS.md` — operating instructions for Codex.
  - `skills/*/SKILL.md` — portable SPEDAS workflow guidance.
  - `examples/prompts.md` — suggested prompts and expected tool flow.
  - `scripts/smoke_mcp_runtime.py` — package-local MCP runtime smoke.
- Root-level `.codex-plugin/`, `.mcp.json`, `AGENTS.md`, `skills/`, and `examples/` are retained as direct-checkout compatibility mirrors of the package files. `scripts/validate_plugin.py` enforces that these mirrors stay in sync.

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
- Network access the first time `uvx` installs `spedas_agent_kit` from GitHub. This wrapper pins `spedas_agent_kit` to `8fcfc7dd0e6f01800f301590ed8213eb33683582` and bounds the MCP protocol dependency as `mcp>=1.26.0,<2`.

## Quick smoke prompt

```text
Use the SPEDAS Agent Kit MCP to compare CDAWeb, PDS, and SPICE for a Juno magnetic-field
analysis near Jupiter. Do not download large data; produce a plan and provenance.
```

## Codex marketplace install

This repository includes the supported repo-scoped Codex marketplace manifest at
`.agents/plugins/marketplace.json`. Add it to Codex with:

```bash
codex plugin marketplace add spedas/spedas_codex --ref main
```

The marketplace entry now uses the conventional marketplace package layout:

```text
.agents/plugins/marketplace.json
plugins/spedas-codex/
  .codex-plugin/plugin.json
  .mcp.json
  AGENTS.md
  skills/
  examples/
  scripts/
```

Specifically, `.agents/plugins/marketplace.json` points the `spedas-codex` plugin
at `source.path: "./plugins/spedas-codex"` and classifies it as
`Education & Research`. This avoids relying on marketplace-root (`"./"`) plugin
discovery, which Codex can accept as a marketplace but fail to expose as an
installable plugin.

On Codex builds that expose plugin listing/installation commands, the plugin
should then be visible/installable as:

```bash
codex plugin list
codex plugin add spedas-codex@spedas
```

After installing or upgrading the plugin, restart Codex Desktop (or fully restart
the Codex runtime) and start a new thread before expecting the MCP tools to appear.
Existing threads can keep the tool surface they loaded before the plugin MCP server
was enabled. Seeing only the `spedas-codex:spedas-workflow` skill means the skill
bundle loaded, but it does **not** prove the `spedas` MCP server is attached to the
current session.

If the skill is available but no callable `mcp__spedas__...` tools appear, confirm
or add the plugin-scoped MCP block in `~/.codex/config.toml`:

```toml
[plugins."spedas-codex@spedas"]
enabled = true

[plugins."spedas-codex@spedas".mcp_servers.spedas]
enabled = true
default_tools_approval_mode = "prompt"
```

Then fully restart Codex and open a new thread. In that new thread, the visible
MCP tool names should include entries such as `mcp__spedas__spedas_overview`,
`mcp__spedas__browse_data_sources`, `mcp__spedas__plan_spedas_observation`, and
`mcp__spedas__fetch_data_product` (verify the name is available; do not call the
fetch tool in a no-fetch smoke).

The legacy root-level `marketplace.json` is kept only as a lightweight compatibility
index and also points at `plugins/spedas-codex`; Codex marketplace add uses
`.agents/plugins/marketplace.json`.


## Publishing / installing for Codex

The supported package shape is the repo/team marketplace layout used by this repo:

```text
.agents/plugins/marketplace.json
plugins/spedas-codex/
  .codex-plugin/plugin.json
  .mcp.json
  AGENTS.md
  skills/
  examples/
  scripts/
```

### Local / personal marketplace

For personal testing, keep the same plugin package shape and expose it through a
local marketplace entry (for example in `~/.agents/plugins/marketplace.json`) that
points at the `plugins/spedas-codex` package. This repository's
`.agents/plugins/marketplace.json` is the reference entry to copy/adapt: it names
the marketplace `spedas`, points `source.path` at `./plugins/spedas-codex`, and
uses the package-local `.codex-plugin/plugin.json` + `.mcp.json`.

After changing a local marketplace or reinstalling the plugin, remove/re-add the
plugin if needed, then restart Codex and open a new thread. Do not judge MCP tool
exposure from an old thread that was already running before the reinstall.

### Repo / team marketplace

For a repo-hosted marketplace, keep `.agents/plugins/marketplace.json` in the repo
and install the marketplace with one of the forms supported by your Codex build:

```bash
codex plugin marketplace add owner/repo
codex plugin marketplace add owner/repo --ref main
codex plugin marketplace add https://github.com/spedas/spedas_codex.git
```

Then install the plugin from that marketplace:

```bash
codex plugin add spedas-codex@<marketplace-name>
```

For this repository, the expected marketplace/plugin id is:

```bash
codex plugin marketplace add spedas/spedas_codex --ref main
codex plugin add spedas-codex@spedas
```

### Workspace sharing in the Codex app

Codex app sharing is workspace-scoped and is not the same as publishing a public
or repo/team marketplace. For ad hoc app sharing, use **Plugins -> Created by you -> Share** in the Codex app. Users who receive a shared workspace/plugin should
still restart Codex or open a new thread before checking the native MCP tool
surface.

### Fresh-thread verification

Keep `python scripts/smoke_mcp_runtime.py --json` as the lower-level server health
check. It proves the packaged `.mcp.json` can start the SPEDAS Agent Kit MCP server
and that the server advertises tools. It does **not** prove that the current Codex
thread mounted those tools.

In a fresh thread after install/reinstall, verify native Codex MCP callables such
as:

```text
mcp__spedas__spedas_overview
mcp__spedas__browse_data_sources
mcp__spedas__fetch_data_product
```

If those names are absent, first confirm the plugin-scoped
`[plugins."spedas-codex@spedas".mcp_servers.spedas]` block above, then restart
and open another new thread.

## Local validation

```bash
python scripts/validate_plugin.py
python scripts/smoke_mcp_runtime.py --json
python plugins/spedas-codex/scripts/smoke_mcp_runtime.py --json
```

`validate_plugin.py` is network-free and checks the marketplace catalog,
`plugins/spedas-codex` package layout, root compatibility mirrors, MCP reference,
pinned `spedas_agent_kit` SHA, bounded MCP dependency, and the Codex Desktop
MCP-tool-exposure troubleshooting snippets. `smoke_mcp_runtime.py` is a real stdio
MCP runtime smoke: it starts the configured `spedas` server, performs `initialize`
+ `tools/list` plus `resources/list` / `resources/read`, and verifies the current
13-tool base SPEDAS surface and packaged skill resources without private
credentials, interactive UI, data fetches, or SPICE kernel downloads. The
direct HAPI/FDSN data-source tools are demoted out of this base surface (Agent Kit
#87/#145) and only appear with `SPEDAS_AGENT_KIT_DATASOURCE_TOOLS=1`; the legacy
CDAWeb/PDS compat tools require `SPEDAS_AGENT_KIT_COMPAT_TOOLS=1`. The smoke does
not require either optional tier unless its flag is set. It may need public network
access the first time `uvx` installs `spedas_agent_kit`. It verifies the wrapper
runtime command, not whether Codex Desktop attached those tools to an already-open
agent session.

## Real Codex CLI / Desktop smoke

Validate the package structure and the MCP runtime command first:

```bash
python scripts/validate_plugin.py
python scripts/smoke_mcp_runtime.py --json
```

Then ask Codex CLI to try the wrapper without editing files:

```bash
codex exec --cd . --sandbox workspace-write   "Validate the SPEDAS Codex wrapper. Prefer live MCP tools if this Codex build exposes them; otherwise run the safe runtime smoke and summarize evidence. Do not edit files or fetch data."
```

For Codex Desktop, separate two checks:

1. **Wrapper runtime health**: `python scripts/smoke_mcp_runtime.py --json` starts
the same `uvx ... spedas-agent-kit` command from `.mcp.json`, performs MCP
`initialize` + `tools/list` plus `resources/list` / `resources/read`, and verifies
core SPEDAS tools plus packaged skill resources. This confirms the plugin package
can start the MCP server.
2. **Active-session tool exposure**: after enabling the plugin MCP server, restart
Codex Desktop and start a new thread. The new thread should have callable tools
named like `mcp__spedas__spedas_overview`, `mcp__spedas__browse_data_sources`,
`mcp__spedas__plan_spedas_observation`, and `mcp__spedas__fetch_data_product`. If
those tools are missing but the
`spedas-codex:spedas-workflow` skill is present, the skill loaded but the MCP
server did not attach to that session; add the plugin-scoped `mcp_servers.spedas`
config block above and restart again.

The runtime smoke isolates SPEDAS data caches and falls back to temporary
`uv`/XDG/tmp caches when the default cache location is not writable. This is
important in Codex sandboxes and CI. First runs may be slow because `uvx` resolves
the pinned `spedas_agent_kit` commit from GitHub. Expected default smoke evidence
is `ok: true`, a `tool_count` of at least the 13 base tools (optional tiers may
add more), a `resource_count` of at least 65, empty `missing_core_tools`,
`missing_skill_resources`, and `missing_preset_resources` lists, and readable
`spedas-skill://index`, `spedas-skill://skills/spedas-workflow`,
`spedas-preset://schemas/reproduction_provenance`, and
`spedas-preset://schemas/analysis_bundle_run` resources.
Setting `SPEDAS_AGENT_KIT_DATASOURCE_TOOLS=1` or
`SPEDAS_AGENT_KIT_COMPAT_TOOLS=1` additionally requires the corresponding optional
tier.

If your Codex/MCP client exposes resources, use `list_resources` and read
`spedas-skill://index` or `spedas-skill://skills/spedas-workflow` for the
Agent Kit packaged skill catalog. These resources are read-only guidance and do
not add to the compact 13-tool default surface.

### Shared skill set

This wrapper now carries the full shared SPEDAS skill set exported from the
canonical Agent Kit package resources. Refresh both root and packaged plugin
copies from Agent Kit with:

```bash
python /path/to/spedas_agent_kit/scripts/export_packaged_skills.py \
  --source /path/to/spedas_agent_kit/src/spedas_agent_kit/resources/skills \
  --target skills --clean
python /path/to/spedas_agent_kit/scripts/export_packaged_skills.py \
  --source /path/to/spedas_agent_kit/src/spedas_agent_kit/resources/skills \
  --target plugins/spedas-codex/skills --clean
```

`spedas_agent_kit` remains the source of truth for MCP tools/resources and
shared skills. This repository should only hold Codex packaging, plugin metadata,
MCP config, validation/smoke scripts, and synchronized skill copies.
