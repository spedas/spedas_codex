#!/usr/bin/env python3
"""Runtime smoke-test the packaged SPEDAS Agent Kit MCP server configuration.

This is intentionally a no-credential, no-interactive-UI, no-data-fetch smoke.
It reads the repo's .mcp.json, starts the configured ``spedas`` stdio MCP server,
performs MCP ``initialize`` and ``tools/list`` JSON-RPC calls, verifies the
default base SPEDAS tool surface, then exits. The optional direct HAPI/FDSN
data-source tier and the legacy CDAWeb/PDS compat tier are only required when
their respective ``SPEDAS_AGENT_KIT_DATASOURCE_TOOLS=1`` /
``SPEDAS_AGENT_KIT_COMPAT_TOOLS=1`` flags are set. Cache directories are isolated
in a temporary folder unless the caller already set them.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Base SPEDAS Agent Kit surface that the default (no-flag) runtime always
# advertises. Keep in sync with spedas_agent_kit.server's _primary_tool set
# (https://github.com/spedas/spedas_agent_kit). After Agent Kit #87/#145 the
# direct HAPI/FDSN data-source tools are demoted out of this default surface and
# are advertised only with SPEDAS_AGENT_KIT_DATASOURCE_TOOLS=1, so they are NOT
# required here.
EXPECTED_CORE_TOOLS = [
    "spedas_overview",
    "search_spedas_data_sources",
    "plan_spedas_observation",
    "compare_cdaweb_pds_spice",
    "create_spedas_analysis_bundle",
    "browse_data_sources",
    "load_data_source",
    "browse_data_parameters",
    "fetch_data_product",
    "manage_data_cache",
    "get_ephemeris",
    "compute_distance",
    "transform_coordinates",
]

EXPECTED_SKILL_RESOURCES = [
    "spedas-skill://index",
    "spedas-skill://skills/spedas-workflow",
]
EXPECTED_PRESET_RESOURCES = [
    "spedas-preset://schemas/reproduction_provenance",
    "spedas-preset://schemas/analysis_bundle_run",
]

# Optional tiers gated by environment flags. These are only EXPECTED when the
# corresponding flag is set in the process environment; otherwise they are
# absent from the default surface by design and the smoke does not require them.
DATASOURCE_TOOLS = [
    "browse_hapi_catalog",
    "fetch_hapi_data",
    "browse_fdsn_datasets",
    "fetch_fdsn_data",
]
COMPAT_CDAWEB_PDS_TOOLS = [
    "browse_observatories",
    "load_observatory",
    "browse_parameters",
    "fetch_data",
    "browse_pds_missions",
    "load_pds_mission",
    "browse_pds_parameters",
    "fetch_pds_data",
]


def _expected_tools() -> list[str]:
    """Base surface plus any optional tiers enabled via Agent Kit env flags."""
    expected = list(EXPECTED_CORE_TOOLS)
    if os.environ.get("SPEDAS_AGENT_KIT_DATASOURCE_TOOLS") == "1":
        expected.extend(DATASOURCE_TOOLS)
    if os.environ.get("SPEDAS_AGENT_KIT_COMPAT_TOOLS") == "1":
        expected.extend(COMPAT_CDAWEB_PDS_TOOLS)
    return expected


def _load_server_config() -> dict[str, Any]:
    data = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    servers = data.get("mcpServers") or data.get("mcp_servers")
    if not isinstance(servers, dict) or "spedas" not in servers:
        raise SystemExit(".mcp.json must define a spedas MCP server")
    server = servers["spedas"]
    if not isinstance(server, dict):
        raise SystemExit("spedas MCP server config must be an object")
    return server


def _expand(value: str) -> str:
    # Support the common plugin form ${HOME}/... plus ordinary shell-style vars.
    return os.path.expandvars(value)


def _server_command(server: dict[str, Any]) -> tuple[str, list[str]]:
    command = server.get("command")
    args = server.get("args") or []
    if not isinstance(command, str) or not command:
        raise SystemExit("spedas MCP server config must provide a command")
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise SystemExit("spedas MCP server args must be a list of strings")
    return _expand(command), [_expand(item) for item in args]


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".spedas-smoke-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _prefer_temp_if_unwritable(env: dict[str, str], key: str, candidate: Path, fallback: Path) -> None:
    current = os.environ.get(key)
    if current:
        expanded = Path(_expand(current))
        if not _is_writable_dir(expanded):
            fallback.mkdir(parents=True, exist_ok=True)
            env[key] = str(fallback)
        return
    if not _is_writable_dir(candidate):
        fallback.mkdir(parents=True, exist_ok=True)
        env[key] = str(fallback)


def _server_env(server: dict[str, Any], tmp: Path) -> dict[str, str]:
    env = os.environ.copy()
    configured = server.get("env") or {}
    if not isinstance(configured, dict):
        raise SystemExit("spedas MCP server env must be an object when present")
    for key, value in configured.items():
        if isinstance(key, str) and isinstance(value, str):
            env[key] = _expand(value)

    # The packaged .mcp.json points at normal user caches for real plugin use.
    # Runtime smoke tests should be hermetic unless the caller explicitly set a
    # cache variable in the process environment. This keeps CI/Codex sandboxes
    # from writing to user caches and avoids false failures when HOME is read-only.
    isolated_data_caches = {
        "XHELIO_CDAWEB_CACHE_DIR": tmp / "cdaweb",
        "PDSMCP_CACHE_DIR": tmp / "pds",
        "XHELIO_SPICE_KERNEL_DIR": tmp / "spice",
    }
    for key, path in isolated_data_caches.items():
        if key not in os.environ:
            path.mkdir(parents=True, exist_ok=True)
            env[key] = str(path)

    _prefer_temp_if_unwritable(env, "UV_CACHE_DIR", Path.home() / ".cache" / "uv", tmp / "uv-cache")
    _prefer_temp_if_unwritable(env, "XDG_CACHE_HOME", Path.home() / ".cache", tmp / "xdg-cache")
    tmp_candidate = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
    _prefer_temp_if_unwritable(env, "TMPDIR", tmp_candidate, tmp / "tmp")
    return env


async def _read_message(reader: asyncio.StreamReader) -> dict[str, Any]:
    # The Python MCP stdio transport uses JSON-RPC messages framed as one JSON
    # object per line. This avoids depending on the mcp Python client package in
    # the plugin wrapper repos.
    line = await reader.readline()
    if not line:
        raise RuntimeError("MCP server closed stdout before responding")
    return json.loads(line.decode("utf-8"))


async def _send_message(writer: asyncio.StreamWriter, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    writer.write(body + b"\n")
    await writer.drain()


async def _request(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    request_id: int,
    method: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    await _send_message(
        writer,
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}},
    )
    while True:
        message = await _read_message(reader)
        if message.get("id") == request_id:
            if "error" in message:
                raise RuntimeError(f"MCP {method} failed: {message['error']}")
            return message.get("result") or {}


def _read_resource_text(result: dict[str, Any]) -> str:
    contents = result.get("contents") or []
    if not isinstance(contents, list):
        return ""
    chunks: list[str] = []
    for item in contents:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            chunks.append(item["text"])
    return "\n".join(chunks)


async def _smoke(command: str, args: list[str], env: dict[str, str], timeout: float) -> dict[str, Any]:
    proc = await asyncio.create_subprocess_exec(
        command,
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    assert proc.stdin is not None and proc.stdout is not None
    try:
        init = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "spedas-plugin-runtime-smoke", "version": "0.1.0"},
        }
        await asyncio.wait_for(_request(proc.stdout, proc.stdin, 1, "initialize", init), timeout)
        await _send_message(proc.stdin, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        result = await asyncio.wait_for(_request(proc.stdout, proc.stdin, 2, "tools/list"), timeout)
        tools = result.get("tools") or []
        resources_result = await asyncio.wait_for(_request(proc.stdout, proc.stdin, 3, "resources/list"), timeout)
        resources = resources_result.get("resources") or []
        skill_index = await asyncio.wait_for(
            _request(proc.stdout, proc.stdin, 4, "resources/read", {"uri": "spedas-skill://index"}),
            timeout,
        )
        workflow_skill = await asyncio.wait_for(
            _request(proc.stdout, proc.stdin, 5, "resources/read", {"uri": "spedas-skill://skills/spedas-workflow"}),
            timeout,
        )
        reproduction_schema = await asyncio.wait_for(
            _request(proc.stdout, proc.stdin, 6, "resources/read", {"uri": "spedas-preset://schemas/reproduction_provenance"}),
            timeout,
        )
        analysis_run_schema = await asyncio.wait_for(
            _request(proc.stdout, proc.stdin, 7, "resources/read", {"uri": "spedas-preset://schemas/analysis_bundle_run"}),
            timeout,
        )
        return {
            "tools": [tool.get("name") for tool in tools if isinstance(tool, dict) and isinstance(tool.get("name"), str)],
            "resources": [resource.get("uri") for resource in resources if isinstance(resource, dict) and isinstance(resource.get("uri"), str)],
            "skill_index_readable": "spedas-skill://skills/" in _read_resource_text(skill_index),
            "workflow_skill_readable": "SPEDAS" in _read_resource_text(workflow_skill),
            "reproduction_schema_readable": "reproduction provenance" in _read_resource_text(reproduction_schema),
            "analysis_run_schema_readable": "analysis bundle run provenance" in _read_resource_text(analysis_run_schema),
        }
    finally:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), 5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        stderr = (await proc.stderr.read()).decode("utf-8", errors="replace") if proc.stderr else ""
        if proc.returncode not in (0, -15, None) and stderr:
            print(stderr[-4000:], file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--timeout", type=float, default=180.0, help="per-request timeout in seconds")
    args = parser.parse_args()

    server = _load_server_config()
    command, command_args = _server_command(server)
    with tempfile.TemporaryDirectory(prefix="spedas-plugin-smoke-") as tmpdir:
        env = _server_env(server, Path(tmpdir))
        smoke = asyncio.run(_smoke(command, command_args, env, args.timeout))
        tools = smoke["tools"]
        resources = smoke["resources"]

    expected = _expected_tools()
    missing = [name for name in expected if name not in tools]
    missing_skill_resources = [uri for uri in EXPECTED_SKILL_RESOURCES if uri not in resources]
    missing_preset_resources = [uri for uri in EXPECTED_PRESET_RESOURCES if uri not in resources]
    skill_resources_ok = (
        not missing_skill_resources
        and smoke["skill_index_readable"]
        and smoke["workflow_skill_readable"]
    )
    preset_resources_ok = (
        not missing_preset_resources
        and smoke["reproduction_schema_readable"]
        and smoke["analysis_run_schema_readable"]
    )
    payload = {
        "ok": not missing and skill_resources_ok and preset_resources_ok,
        "tool_count": len(tools),
        "tools": tools,
        "resource_count": len(resources),
        "resources": resources,
        "expected_skill_resources": EXPECTED_SKILL_RESOURCES,
        "missing_skill_resources": missing_skill_resources,
        "expected_preset_resources": EXPECTED_PRESET_RESOURCES,
        "missing_preset_resources": missing_preset_resources,
        "skill_index_readable": smoke["skill_index_readable"],
        "workflow_skill_readable": smoke["workflow_skill_readable"],
        "reproduction_schema_readable": smoke["reproduction_schema_readable"],
        "analysis_run_schema_readable": smoke["analysis_run_schema_readable"],
        "expected_core_tools": expected,
        "missing_core_tools": missing,
        "datasource_tools_enabled": os.environ.get("SPEDAS_AGENT_KIT_DATASOURCE_TOOLS") == "1",
        "compat_tools_enabled": os.environ.get("SPEDAS_AGENT_KIT_COMPAT_TOOLS") == "1",
        "datasource_env_flag": "SPEDAS_AGENT_KIT_DATASOURCE_TOOLS=1",
        "compat_env_flag": "SPEDAS_AGENT_KIT_COMPAT_TOOLS=1",
        "command": [command, *command_args],
        "note": (
            "initialize + tools/list + resources/list/read for packaged skills and preset schemas; "
            "no private credentials, interactive UI, data fetch, or SPICE kernel download. Direct HAPI/FDSN tools require "
            "SPEDAS_AGENT_KIT_DATASOURCE_TOOLS=1 and legacy CDAWeb/PDS compat tools "
            "require SPEDAS_AGENT_KIT_COMPAT_TOOLS=1; both are absent from the "
            "default base surface by design."
        ),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"SPEDAS plugin MCP runtime smoke: {'OK' if payload['ok'] else 'FAIL'}")
        print(f"tool_count: {payload['tool_count']}")
        print(f"resource_count: {payload['resource_count']}")
        if missing:
            print("missing core tools: " + ", ".join(missing), file=sys.stderr)
        if missing_skill_resources:
            print("missing skill resources: " + ", ".join(missing_skill_resources), file=sys.stderr)
        if missing_preset_resources:
            print("missing preset resources: " + ", ".join(missing_preset_resources), file=sys.stderr)
        if not smoke["skill_index_readable"]:
            print("skill index resource was not readable", file=sys.stderr)
        if not smoke["workflow_skill_readable"]:
            print("spedas-workflow skill resource was not readable", file=sys.stderr)
        if not smoke["reproduction_schema_readable"]:
            print("reproduction provenance schema resource was not readable", file=sys.stderr)
        if not smoke["analysis_run_schema_readable"]:
            print("analysis bundle run schema resource was not readable", file=sys.stderr)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
