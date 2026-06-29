#!/usr/bin/env python3
"""Validate standalone SPEDAS plugin wrapper structure without network access."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str) -> Path:
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"missing required file: {path}")
    if p.is_file() and p.stat().st_size == 0:
        raise SystemExit(f"empty required file: {path}")
    return p


def load_json(path: str):
    p = require(path)
    try:
        return json.loads(p.read_text())
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def validate_mcp():
    data = load_json('.mcp.json')
    servers = data.get('mcpServers') or data.get('mcp_servers')
    if not isinstance(servers, dict) or 'spedas' not in servers:
        raise SystemExit('.mcp.json must define a spedas MCP server')
    server = servers['spedas']
    args = server.get('args') or []
    joined = ' '.join(args)
    if 'github.com/spedas/spedas_mcp' not in joined or 'spedas-mcp' not in joined:
        raise SystemExit('spedas MCP server must install/run github.com/spedas/spedas_mcp spedas-mcp')
    if server.get('command') != 'uvx':
        raise SystemExit('expected MCP command uvx for portable install')
    from_arg = ''
    for i, arg in enumerate(args):
        if arg == '--from' and i + 1 < len(args):
            from_arg = args[i + 1]
            break
    if not re.search(r'git\+https://github\.com/spedas/spedas_mcp\.git@[0-9a-f]{40}($|[#\s])', from_arg):
        raise SystemExit('spedas_mcp source must be pinned to a full commit SHA')
    mcp_reqs = [arg.replace(' ', '') for arg in args if arg.replace(' ', '').startswith('mcp')]
    if not any(('<' in req or '==' in req or '~=' in req) for req in mcp_reqs):
        raise SystemExit('mcp dependency must include an upper bound')


def main() -> int:
    require('README.md')
    require('LICENSE')
    require('skills/spedas-workflow/SKILL.md')
    validate_mcp()
    # Repo-specific plugin manifest checks.
    claude = ROOT / '.claude-plugin/plugin.json'
    codex = ROOT / '.codex-plugin/plugin.json'
    if claude.exists():
        data = load_json('.claude-plugin/plugin.json')
        if data.get('name') != 'spedas-claude':
            raise SystemExit('Claude plugin name must be spedas-claude')
        require('commands/overview.md')
        require('commands/data.md')
        require('commands/workflow.md')
    elif codex.exists():
        data = load_json('.codex-plugin/plugin.json')
        if data.get('name') != 'spedas-codex':
            raise SystemExit('Codex plugin name must be spedas-codex')
        require('AGENTS.md')
    else:
        raise SystemExit('missing .claude-plugin/plugin.json or .codex-plugin/plugin.json')
    print('SPEDAS plugin wrapper validation OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
