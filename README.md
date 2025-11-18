# SAP API Accelerator MCP

An MCP (Model Context Protocol) server that surfaces curated SAP Business Accelerator Hub data as MCP tools. The server talks directly to SAP’s public OData catalog, making it easy to list every content package and drill into the artifacts that belong to a specific package without leaving your MCP-compatible client.

## Purpose of This MCP Server

- Provide AI assistants and MCP tooling with read-only access to SAP’s catalog.
- Offer predictable, low-latency helpers for common discovery workflows (list packages, inspect artifacts).
- Demonstrate how to wrap a public OData API with the `mcp.server.fastmcp.FastMCP` helper so it can be inspected, tested, and shipped with any MCP host.

## Prerequisites

- **Python** 3.12 or newer.
- **uv** (recommended) or `pip` + a virtual environment.
- Outbound HTTPS access to `https://api.sap.com/odata/1.0/catalog.svc`.
- (Optional) **Node.js 18+** if you want to use the MCPJam Inspector via `npx`.

## Requirements & Dependencies

All Python requirements are defined in `pyproject.toml`:

- `httpx` – async HTTP client used for SAP API calls.
- `mcp[cli]` – brings in `FastMCP`, CLI helpers, and MCP protocol types.

Install them in editable mode so local code changes are picked up immediately:

```bash
cd sap-api-accelerator-mcp
uv pip install -e .
# or: python -m pip install -e .
```

## Available MCP Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `list_sap_content_packages` | _None_ | Calls `ContentPackages` with `$select=TechnicalName,DisplayName,Version` and returns every package in a friendly text block. |
| `get_sap_package_artifacts` | `package_id` (TechnicalName) | Requests `ContentPackages('<ID>')/Artifacts` and prints each artifact’s name, type, version, and description for the selected package. |

Both tools normalize OData v2/v4 responses, force JSON output (`$format=json`), and include defensive error handling so failures are reported rather than crashing the MCP session.

## How to Run the MCP Server

```bash
cd sap-api-accelerator-mcp
uv run accelerator.py
# or
python accelerator.py
```

The script registers both tools with `FastMCP` and starts an MCP stdio server (the default transport). Any MCP-compatible client can now spawn this process and call the tools.

## Testing with MCPJam Inspector

MCPJam Inspector offers a browser UI for exercising MCP servers without wiring up an LLM. Typical workflow:

1. **Launch the inspector**
   ```bash
   npx @mcpjam/inspector@latest
   ```
   The CLI prints a URL such as `http://localhost:6274`. Open it in your browser.

2. **Add the SAP accelerator server**
   - Click **Add Server** → **Custom / stdio**.
   - Command: `uv run accelerator.py` (or `python accelerator.py`).
   - Provide a friendly name (e.g., “SAP Accelerator”) and save. The status should flip to **Connected**.

3. **Exercise the tools**
   - Open the **Tools** tab, choose `list_sap_content_packages`, and click **Execute** to confirm catalog access.
   - Pick `get_sap_package_artifacts`, supply a `TechnicalName` from the previous response, and execute again to view the artifact breakdown.

4. **Inspect traffic / troubleshoot**
   - Use the **Messages** view to see raw MCP JSON exchange.
   - If a call fails, MCPJam surfaces the stderr logs (the server prints every SAP request it makes) to help diagnose connectivity or parameter issues.

## Tips & Next Steps

- Because the SAP endpoints are public, no API key is required, but the server still sends a custom `User-Agent` so rate limiting can be monitored.
- Extend `accelerator.py` with additional MCP tools (search, filter, etc.) by decorating new async functions with `@mcp.tool()`.
- Pair this server with any MCP host (Anthropic Claude Desktop, MCP CLI, custom LLM sandboxes) to let assistants browse SAP content.

