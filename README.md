# SAP API Accelerator MCP

An MCP (Model Context Protocol) server that surfaces curated SAP Business Accelerator Hub data as MCP tools. The server talks directly to SAP's public OData catalog, making it easy to discover, search, and explore SAP APIs and artifacts without leaving your MCP-compatible client.

## Purpose of This MCP Server

- Provide AI assistants and MCP tooling with comprehensive read-only access to SAP's vast API catalog.
- Offer powerful search and discovery tools for finding SAP APIs, packages, and artifacts.
- Enable intelligent exploration of SAP's API ecosystem with filtering, analytics, and relationship navigation.
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

The server provides **12 powerful tools** for exploring SAP's API catalog:

### Core Discovery Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `list_sap_content_packages` | `search_term` (optional), `max_results` (default: 100) | Lists all content packages with optional search filtering. Enhanced with OData filtering and result limiting. |
| `get_sap_package_artifacts` | `package_id`, `artifact_type` (optional), `subtype` (optional), `state` (optional), `max_results` (default: 100) | Gets artifacts for a specific package with advanced filtering by type, subtype, and state. |
| `search_sap_artifacts` | `query`, `artifact_type` (optional), `subtype` (optional), `state` (default: ACTIVE), `package_id` (optional), `max_results` (default: 50) | **Universal search tool** - Search artifacts across all packages or within a specific package. Most versatile tool. |
| `get_sap_package_info` | `package_id` | Get detailed information about a specific content package. |
| `get_sap_artifact_details` | `artifact_name`, `artifact_type` (default: API) | Get complete details for a specific artifact including all metadata. |

### Advanced Search & Filter Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `list_sap_artifacts_by_type` | `artifact_type`, `subtype` (optional), `package_id` (optional), `max_results` (default: 50) | List artifacts filtered by type, optionally by subtype and package. |
| `find_sap_apis_by_protocol` | `protocol`, `package_id` (optional), `state` (default: ACTIVE), `max_results` (default: 50) | Find APIs by protocol type (ODATAV4, ODATA, SOAP, REST). |
| `find_recent_sap_artifacts` | `sort_by` (default: modified), `days` (optional), `max_results` (default: 20) | Find recently updated or newly created artifacts. |
| `count_sap_artifacts` | `package_id` (optional), `artifact_type` (optional), `state` (optional) | Get count of artifacts with optional filters for statistics. |
| `find_deprecated_sap_apis` | `package_id` (optional), `max_results` (default: 50) | Find deprecated APIs that may need migration planning. |

### Relationship & Navigation Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `get_artifact_packages` | `artifact_name`, `artifact_type` (default: API) | Find which packages contain a specific artifact. |
| `get_sap_service_metadata` | _None_ | Get OData service metadata/schema for the SAP catalog service. |

All tools normalize OData v2/v4 responses, force JSON output (`$format=json`), and include defensive error handling so failures are reported rather than crashing the MCP session.

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

## Use Case Examples

### Example 1: Find APIs for Order Management
```
search_sap_artifacts(query="Order", artifact_type="API", subtype="ODATAV4", state="ACTIVE")
```
This searches for active OData V4 APIs related to "Order" across all packages.

### Example 2: Explore a Specific Package
```
get_sap_package_info(package_id="SAPS4HANACloud")
get_sap_package_artifacts(package_id="SAPS4HANACloud", artifact_type="API", max_results=50)
```
First get package info, then list all APIs in that package.

### Example 3: Find Recently Updated APIs
```
find_recent_sap_artifacts(sort_by="modified", days=30, max_results=20)
```
Get APIs modified in the last 30 days.

### Example 4: Protocol-Specific Discovery
```
find_sap_apis_by_protocol(protocol="ODATAV4", state="ACTIVE", max_results=100)
```
Find all active OData V4 APIs.

### Example 5: Get Detailed Artifact Information
```
get_sap_artifact_details(artifact_name="CE_PROJECTDEMANDCATEGORY_0001", artifact_type="API")
get_artifact_packages(artifact_name="CE_PROJECTDEMANDCATEGORY_0001", artifact_type="API")
```
Get complete details for an artifact and find which packages contain it.

### Example 6: Migration Planning
```
find_deprecated_sap_apis(max_results=50)
```
Find deprecated APIs that may need migration.

### Example 7: Package Statistics
```
count_sap_artifacts(package_id="SAPS4HANACloud", artifact_type="API")
```
Get count of APIs in a package.

### Example 8: Comprehensive Search
```
search_sap_artifacts(
    query="Invoice",
    artifact_type="API",
    subtype="ODATAV4",
    state="ACTIVE",
    max_results=25
)
```
Multi-criteria search combining keyword, type, protocol, and state filters.

## Tips & Best Practices

- **Use `search_sap_artifacts`** as your primary search tool - it's the most versatile and supports all common filters.
- **Set `max_results`** appropriately - default values are conservative to avoid timeouts. Increase for comprehensive searches.
- **Filter by `state="ACTIVE"`** to exclude deprecated APIs unless you're specifically looking for them.
- **Use `get_sap_artifact_details`** after finding interesting artifacts to get complete metadata.
- **Combine tools** - start with search, then drill down with detail tools.
- Because the SAP endpoints are public, no API key is required, but the server still sends a custom `User-Agent` so rate limiting can be monitored.
- Pair this server with any MCP host (Anthropic Claude Desktop, MCP CLI, custom LLM sandboxes) to let assistants browse SAP content.

## Tool Priority Guide

**Start with these tools:**
1. `search_sap_artifacts` - Universal search
2. `get_sap_package_info` - Package discovery
3. `get_sap_artifact_details` - Detailed information

**For specific needs:**
- Protocol filtering → `find_sap_apis_by_protocol`
- Recent updates → `find_recent_sap_artifacts`
- Migration planning → `find_deprecated_sap_apis`
- Statistics → `count_sap_artifacts`
- Relationships → `get_artifact_packages`

## Performance Considerations

- Large result sets may take time - use `max_results` to limit responses
- The SAP API may be slow for complex queries - be patient
- Use `$select` in queries (already implemented) to reduce payload size
- Consider caching results for frequently accessed data

## Related Documentation

- See `SAP_API_MCP_ANALYSIS.md` for comprehensive analysis and roadmap
- See `POSTMAN_QUERY_EXAMPLES.md` for OData query patterns
- See `POSTMAN_QUERIES_TO_ADD.md` for queries to add to your Postman collection

