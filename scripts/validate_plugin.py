#!/usr/bin/env python3
"""Validate standalone SPEDAS Codex wrapper structure without network access."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "spedas-codex"

MIRRORED_PACKAGE_FILES = [
    ".codex-plugin/plugin.json",
    ".mcp.json",
    "AGENTS.md",
    "skills/spedas-workflow/SKILL.md",
    "examples/prompts.md",
]


def require(path: str, *, base: Path = ROOT) -> Path:
    p = base / path
    if not p.exists():
        where = "repo root" if base == ROOT else str(base.relative_to(ROOT))
        raise SystemExit(f"missing required file in {where}: {path}")
    if p.is_file() and p.stat().st_size == 0:
        where = "repo root" if base == ROOT else str(base.relative_to(ROOT))
        raise SystemExit(f"empty required file in {where}: {path}")
    return p


def load_json(path: str, *, base: Path = ROOT) -> Any:
    p = require(path, base=base)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"invalid JSON in {p.relative_to(ROOT)}: {exc}") from exc


def validate_marketplace() -> None:
    data = load_json(".agents/plugins/marketplace.json")
    if data.get("name") != "spedas":
        raise SystemExit("marketplace name must be spedas")
    interface = data.get("interface")
    if not isinstance(interface, dict) or interface.get("displayName") != "SPEDAS":
        raise SystemExit("marketplace interface.displayName must be SPEDAS")
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        raise SystemExit("marketplace must define exactly one plugin entry")
    plugin = plugins[0]
    if plugin.get("name") != "spedas-codex":
        raise SystemExit("marketplace plugin name must be spedas-codex")
    source = plugin.get("source")
    if not isinstance(source, dict):
        raise SystemExit("marketplace plugin must define a source object")
    if source.get("source") != "local":
        raise SystemExit("marketplace plugin source.source must be local")
    if source.get("path") != "./plugins/spedas-codex":
        raise SystemExit("marketplace plugin source.path must be ./plugins/spedas-codex")
    if (ROOT / source["path"]).resolve() != PLUGIN_ROOT.resolve():
        raise SystemExit("marketplace source.path must resolve to plugins/spedas-codex")
    require(".codex-plugin/plugin.json", base=PLUGIN_ROOT)
    require(".mcp.json", base=PLUGIN_ROOT)
    require("AGENTS.md", base=PLUGIN_ROOT)
    require("skills/spedas-workflow/SKILL.md", base=PLUGIN_ROOT)
    require("examples/prompts.md", base=PLUGIN_ROOT)
    require("scripts/smoke_mcp_runtime.py", base=PLUGIN_ROOT)
    policy = plugin.get("policy")
    if not isinstance(policy, dict):
        raise SystemExit("marketplace plugin must define policy")
    if policy.get("installation") != "AVAILABLE":
        raise SystemExit("marketplace policy.installation must be AVAILABLE")
    if policy.get("authentication") != "ON_INSTALL":
        raise SystemExit("marketplace policy.authentication must be ON_INSTALL")
    if plugin.get("category") != "Education & Research":
        raise SystemExit("marketplace category must be Education & Research")
    plugin_interface = plugin.get("interface")
    if not isinstance(plugin_interface, dict) or plugin_interface.get("displayName") != "SPEDAS Codex":
        raise SystemExit("marketplace plugin interface.displayName must be SPEDAS Codex")

    legacy = load_json("marketplace.json")
    legacy_plugins = legacy.get("plugins")
    if not isinstance(legacy_plugins, list) or not legacy_plugins:
        raise SystemExit("legacy marketplace.json must list the spedas-codex plugin")
    if legacy_plugins[0].get("path") != "plugins/spedas-codex":
        raise SystemExit("legacy marketplace.json path must be plugins/spedas-codex")


def validate_mcp(*, base: Path) -> None:
    data = load_json(".mcp.json", base=base)
    servers = data.get("mcpServers") or data.get("mcp_servers")
    label = "repo root" if base == ROOT else str(base.relative_to(ROOT))
    if not isinstance(servers, dict) or "spedas" not in servers:
        raise SystemExit(f"{label}/.mcp.json must define a spedas MCP server")
    server = servers["spedas"]
    args = server.get("args") or []
    joined = " ".join(args)
    if "github.com/spedas/spedas_agent_kit" not in joined or "spedas-agent-kit" not in joined:
        raise SystemExit(f"{label} spedas MCP server must install/run github.com/spedas/spedas_agent_kit spedas-agent-kit")
    if server.get("command") != "uvx":
        raise SystemExit(f"{label} expected MCP command uvx for portable install")
    from_arg = ""
    for i, arg in enumerate(args):
        if arg == "--from" and i + 1 < len(args):
            from_arg = args[i + 1]
            break
    if not re.search(r"git\+https://github\.com/spedas/spedas_agent_kit\.git@[0-9a-f]{40}($|[#\s])", from_arg):
        raise SystemExit(f"{label} spedas_agent_kit source must be pinned to a full commit SHA")
    mcp_reqs = [arg.replace(" ", "") for arg in args if arg.replace(" ", "").startswith("mcp")]
    if not any(("<" in req or "==" in req or "~=" in req) for req in mcp_reqs):
        raise SystemExit(f"{label} mcp dependency must include an upper bound")


def validate_plugin_package() -> None:
    data = load_json(".codex-plugin/plugin.json", base=PLUGIN_ROOT)
    if data.get("name") != "spedas-codex":
        raise SystemExit("Codex plugin name must be spedas-codex")
    if data.get("skills") != "./skills":
        raise SystemExit("Codex plugin skills path must be ./skills relative to the plugin package")
    if data.get("mcpServers") != "./.mcp.json":
        raise SystemExit("Codex plugin mcpServers path must be ./.mcp.json relative to the plugin package")
    require("AGENTS.md", base=PLUGIN_ROOT)


def validate_mirrors() -> None:
    """Root copies are kept for direct-checkout compatibility; keep them in sync."""
    for rel in MIRRORED_PACKAGE_FILES:
        root_file = require(rel)
        package_file = require(rel, base=PLUGIN_ROOT)
        if root_file.read_bytes() != package_file.read_bytes():
            raise SystemExit(f"root {rel} and plugins/spedas-codex/{rel} must stay identical")


def main() -> int:
    require("README.md")
    require("LICENSE")
    require("scripts/smoke_mcp_runtime.py")
    validate_marketplace()
    validate_mcp(base=ROOT)
    validate_mcp(base=PLUGIN_ROOT)
    validate_plugin_package()
    validate_mirrors()
    print("SPEDAS Codex plugin wrapper validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
