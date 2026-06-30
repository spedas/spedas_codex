# Artifact and provenance discipline

For each real data run, save a small run directory containing:

- `request.json` — science question, time range, mission/source, parameters, allowed side effects.
- `tool_calls.jsonl` or notes — MCP/PySPEDAS calls and arguments.
- `environment.txt` — package versions, Python version, CLI/runtime if relevant.
- `artifacts_manifest.json` — output paths, sizes, SHA-256 hashes, and descriptions.
- `provenance.md` — source datasets/files, caveats, rate limits, missing metadata, and validation status.

When the SPEDAS Agent Kit MCP is available, prefer the canonical machine-readable
provenance schema exposed as the MCP resource
`spedas-preset://schemas/reproduction_provenance`. Read that resource before
inventing a new run-provenance shape, and make schema-validation caveats explicit
when a runtime cannot access MCP resources directly.

Human-facing replies should summarize the science result and provide paths, not raw CDF/tplot/array content.
