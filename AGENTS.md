# SPEDAS Codex operating instructions

Use this repository as a thin Codex wrapper around the official `spedas_mcp` MCP.
Do not reimplement CDAWeb/PDS/SPICE logic here.

When a user asks for SPEDAS work:

1. Start with `spedas_overview`.
2. Use science workflow tools to choose source types and plans.
3. Use unified data-layer tools (`browse_data_sources`, `load_data_source`,
   `browse_data_parameters`, `fetch_data_product`, `manage_data_cache`).
4. Use geometry tools (`get_ephemeris`, `compute_distance`, `transform_coordinates`) for SPICE positions/frames; set `allow_kernel_download=True` only after explicit opt-in.
5. Treat HAPI/FDSN tools as optional backend entrypoints; they may report unavailable unless the server extras are installed.
6. Keep real fetches narrow and artifact-first.
7. Classify failures as MCP/tool bug, backend data gap, external-service limit,
   or documentation gap.

Prefer compact, source-labeled answers with file paths/provenance for artifacts.
