import httpx
import asyncio
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from urllib.parse import quote

# Initialize FastMCP server
mcp = FastMCP("accelerator")

# Constants
SAP_CATALOG_BASE = "https://api.sap.com/odata/1.0/catalog.svc"
CONTENT_PACKAGES_URL = f"{SAP_CATALOG_BASE}/ContentPackages"
ARTIFACTS_URL = f"{SAP_CATALOG_BASE}/Artifacts"
USER_AGENT = "sap-api-accelerator-mcp/1.0"

async def make_sap_api_request(url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Make a request to the SAP OData API with proper error handling.

    This function automatically requests the JSON format and does not use an API key.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",  # Request JSON format
    }

    # Ensure $format=json is in the parameters
    if params is None:
        params = {}
    params["$format"] = "json"

    print(f"Making request to: {url} with params: {params}")

    async with httpx.AsyncClient() as client:
        try:
            # Set a long timeout (5 minutes) to handle slow API responses
            response = await client.get(url, headers=headers, params=params, timeout=300.0)
            
            # Raise an exception for 4xx or 5xx status codes
            response.raise_for_status()
            
            # Return the parsed JSON response
            return response.json()
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

def format_package_list_entry(entry: Dict[str, Any]) -> str:
    """
    Format an SAP ContentPackage entry into a readable string.
    This is for the list_sap_content_packages tool.
    """
    # Keys are based on the OData XML sample provided
    technical_name = entry.get('TechnicalName', 'UNKNOWN_ID')
    display_name = entry.get('DisplayName', 'Unknown Display Name')
    version = entry.get('Version', 'N/A')

    return f"""Display Name: {display_name}
Technical ID: {technical_name}
Version: {version}"""

def format_artifact_entry(entry: Dict[str, Any]) -> str:
    """
    Format an SAP Artifact entry into a readable string.
    This is for the get_sap_package_artifacts tool.
    """
    # Keys are based on the original Artifacts XML sample
    name = entry.get('Name', 'Unknown')
    display_name = entry.get('DisplayName', 'Unknown')
    description = entry.get('Description', 'No description')
    entry_type = entry.get('Type', 'Unknown')
    subtype = entry.get('SubType', 'N/A')
    version = entry.get('Version', 'N/A')
    state = entry.get('State', 'N/A')

    return f"""Name: {name} (Type: {entry_type}, SubType: {subtype}, Version: {version}, State: {state})
Display Name: {display_name}
Description: {description.strip()}"""

def format_artifact_detailed(entry: Dict[str, Any]) -> str:
    """
    Format an SAP Artifact entry with full details.
    """
    name = entry.get('Name', 'Unknown')
    display_name = entry.get('DisplayName', 'Unknown')
    description = entry.get('Description', 'No description')
    entry_type = entry.get('Type', 'Unknown')
    subtype = entry.get('SubType', 'N/A')
    version = entry.get('Version', 'N/A')
    state = entry.get('State', 'N/A')
    reg_id = entry.get('reg_id', 'N/A')
    created_at = entry.get('CreatedAt', 'N/A')
    modified_at = entry.get('ModifiedAt', 'N/A')
    
    return f"""Name: {name}
Display Name: {display_name}
Type: {entry_type}
SubType: {subtype}
Version: {version}
State: {state}
Registration ID: {reg_id}
Created At: {created_at}
Modified At: {modified_at}
Description: {description.strip()}"""

def escape_odata_string(value: str) -> str:
    """Escape single quotes for OData filter strings."""
    return value.replace("'", "''")

@mcp.tool()
async def list_sap_content_packages(search_term: Optional[str] = None, max_results: int = 100) -> str:
    """
    Fetches a list of Content Packages from the SAP Business Accelerator Hub.
    
    Args:
        search_term: Optional keyword to filter packages (e.g., "S/4HANA", "Integration", "Public Edition").
                     Searches both the Display Name and Technical ID.
        max_results: Maximum number of results to return (default: 100).
    """
    
    print(f"Querying SAP API for Content Packages. Filter: {search_term if search_term else 'None'}")
    # Use $select to only get the fields we need.
    # This is the key to getting all items without a timeout.
    params = {
        "$select": "TechnicalName,DisplayName,Version",
        "$top": str(max_results)
    }
    
    # Add OData filter if search_term provided
    if search_term:
        safe_term = escape_odata_string(search_term)
        params["$filter"] = f"contains(DisplayName,'{safe_term}') or contains(TechnicalName,'{safe_term}')"
    
    data = await make_sap_api_request(CONTENT_PACKAGES_URL, params=params)
    
    if not data:
        return "Unable to fetch content packages."

    results: Optional[List[Dict[str, Any]]] = None
    if 'd' in data and 'results' in data['d']:
        results = data['d']['results']  # OData v2
    elif 'value' in data:
        results = data['value']  # OData v4
    
    if not results:
        return "No content packages found or response format was unexpected."

    print(f"Found {len(results)} entries matching filter.")
    # Format each entry and join with a clear separator
    formatted_entries = [format_package_list_entry(entry) for entry in results]
    
    return f"Found {len(results)} content package(s):\n\n" + "\n\n----------------------------------------\n\n".join(formatted_entries)


@mcp.tool()
async def get_sap_package_artifacts(
    package_id: str, 
    artifact_type: Optional[str] = None,
    subtype: Optional[str] = None,
    state: Optional[str] = None,
    max_results: int = 100
) -> str:
    """
    Get artifacts (details) for a specific Content Package.

    Args:
        package_id: The Technical ID of the package (e.g., 'SAPS4HANACloud').
        artifact_type: Optional filter for the type of artifact (e.g., "API", "IntegrationFlow", "ValueMapping").
        subtype: Optional filter for the subtype/protocol (e.g., "ODATAV4", "SOAP", "REST").
        state: Optional filter for the state (e.g., "ACTIVE", "DEPRECATED").
        max_results: Maximum number of results to return (default: 100).
    """
    print(f"Querying SAP API for artifacts in package: {package_id}. Filters - Type: {artifact_type}, SubType: {subtype}, State: {state}")
    
    # Construct the URL to get artifacts for a specific package
    url = f"{CONTENT_PACKAGES_URL}('{package_id}')/Artifacts"
    
    # Build filter clause
    filters = []
    if artifact_type:
        safe_type = escape_odata_string(artifact_type)
        filters.append(f"Type eq '{safe_type}'")
    if subtype:
        safe_subtype = escape_odata_string(subtype)
        filters.append(f"SubType eq '{safe_subtype}'")
    if state:
        safe_state = escape_odata_string(state)
        filters.append(f"State eq '{safe_state}'")
    
    params = {
        "$select": "Name,DisplayName,Type,SubType,Version,State,Description",
        "$top": str(max_results)
    }
    
    if filters:
        params["$filter"] = " and ".join(filters)
    
    data = await make_sap_api_request(url, params=params)

    if not data:
        return f"Unable to fetch artifacts for package ID: {package_id}"

    results: Optional[List[Dict[str, Any]]] = None
    if 'd' in data and 'results' in data['d']:
        results = data['d']['results']  # OData v2
    elif 'value' in data:
        results = data['value']  # OData v4
    
    if not results:
        return f"No artifacts found for package: {package_id}"

    print(f"Found {len(results)} artifacts.")
    # Format each entry and join with a clear separator
    formatted_entries = [format_artifact_entry(entry) for entry in results]
    
    return f"Found {len(results)} artifact(s) in package '{package_id}':\n\n" + "\n\n----------------------------------------\n\n".join(formatted_entries)


@mcp.tool()
async def search_sap_artifacts(
    query: str,
    artifact_type: Optional[str] = None,
    subtype: Optional[str] = None,
    state: Optional[str] = "ACTIVE",
    package_id: Optional[str] = None,
    max_results: int = 50
) -> str:
    """
    Search for SAP artifacts across all packages or within a specific package.
    This is the most versatile search tool - it can replace many specific search tools.
    
    Args:
        query: Search term to find in DisplayName and Description.
        artifact_type: Optional filter by Type (e.g., 'API', 'IntegrationFlow').
        subtype: Optional filter by SubType/protocol (e.g., 'ODATAV4', 'SOAP', 'REST').
        state: Optional filter by State (e.g., 'ACTIVE', 'DEPRECATED'). Default: 'ACTIVE'.
        package_id: Optional limit search to specific package.
        max_results: Maximum number of results to return (default: 50).
    """
    # Build base URL
    if package_id:
        base_url = f"{CONTENT_PACKAGES_URL}('{package_id}')/Artifacts"
    else:
        base_url = ARTIFACTS_URL
    
    # Build filter clause
    filters = []
    if query:
        safe_query = escape_odata_string(query)
        filters.append(f"(contains(DisplayName,'{safe_query}') or contains(Description,'{safe_query}'))")
    if artifact_type:
        safe_type = escape_odata_string(artifact_type)
        filters.append(f"Type eq '{safe_type}'")
    if subtype:
        safe_subtype = escape_odata_string(subtype)
        filters.append(f"SubType eq '{safe_subtype}'")
    if state:
        safe_state = escape_odata_string(state)
        filters.append(f"State eq '{safe_state}'")
    
    params = {
        "$format": "json",
        "$top": str(max_results),
        "$select": "Name,DisplayName,Type,SubType,Version,State,Description"
    }
    
    if filters:
        params["$filter"] = " and ".join(filters)
    
    print(f"Searching SAP artifacts: query='{query}', filters={params.get('$filter', 'None')}")
    data = await make_sap_api_request(base_url, params=params)
    
    if not data:
        return f"Unable to search artifacts. Query: {query}"
    
    results = data.get('value') or data.get('d', {}).get('results', [])
    
    if not results:
        return f"No artifacts found matching: {query}"
    
    formatted = [format_artifact_entry(entry) for entry in results]
    
    return f"Found {len(results)} artifact(s) matching '{query}':\n\n" + "\n\n---\n\n".join(formatted)


@mcp.tool()
async def get_sap_artifact_details(artifact_name: str, artifact_type: str = "API") -> str:
    """
    Get complete details for a specific artifact.
    
    Args:
        artifact_name: Technical name of the artifact (e.g., 'CE_PROJECTDEMANDCATEGORY_0001').
        artifact_type: Type of artifact (default: 'API').
    """
    url = f"{ARTIFACTS_URL}(Name='{escape_odata_string(artifact_name)}',Type='{escape_odata_string(artifact_type)}')"
    
    print(f"Fetching details for artifact: {artifact_name} (Type: {artifact_type})")
    data = await make_sap_api_request(url)
    
    if not data:
        return f"Unable to fetch details for artifact: {artifact_name}"
    
    # Handle both OData v2 and v4 response formats
    artifact = data.get('d') or data
    
    if not artifact:
        return f"Artifact not found: {artifact_name} (Type: {artifact_type})"
    
    return format_artifact_detailed(artifact)


@mcp.tool()
async def list_sap_artifacts_by_type(
    artifact_type: str,
    subtype: Optional[str] = None,
    package_id: Optional[str] = None,
    max_results: int = 50
) -> str:
    """
    List artifacts filtered by type, optionally by subtype and package.
    
    Args:
        artifact_type: Type to filter (e.g., 'API', 'IntegrationFlow').
        subtype: Optional SubType filter (e.g., 'ODATAV4', 'SOAP').
        package_id: Optional package filter.
        max_results: Maximum number of results (default: 50).
    """
    if package_id:
        base_url = f"{CONTENT_PACKAGES_URL}('{package_id}')/Artifacts"
    else:
        base_url = ARTIFACTS_URL
    
    filters = [f"Type eq '{escape_odata_string(artifact_type)}'"]
    if subtype:
        filters.append(f"SubType eq '{escape_odata_string(subtype)}'")
    
    params = {
        "$format": "json",
        "$filter": " and ".join(filters),
        "$top": str(max_results),
        "$select": "Name,DisplayName,Type,SubType,Version,State,Description"
    }
    
    print(f"Listing artifacts by type: {artifact_type}, subtype: {subtype}")
    data = await make_sap_api_request(base_url, params=params)
    
    if not data:
        return f"Unable to fetch artifacts of type: {artifact_type}"
    
    results = data.get('value') or data.get('d', {}).get('results', [])
    
    if not results:
        return f"No artifacts found of type: {artifact_type}"
    
    formatted = [format_artifact_entry(entry) for entry in results]
    
    return f"Found {len(results)} artifact(s) of type '{artifact_type}':\n\n" + "\n\n---\n\n".join(formatted)


@mcp.tool()
async def get_sap_package_info(package_id: str) -> str:
    """
    Get detailed information about a content package.
    
    Args:
        package_id: Technical ID of the package (e.g., 'SAPS4HANACloud').
    """
    url = f"{CONTENT_PACKAGES_URL}('{escape_odata_string(package_id)}')"
    
    print(f"Fetching package info: {package_id}")
    data = await make_sap_api_request(url)
    
    if not data:
        return f"Unable to fetch package information for: {package_id}"
    
    package = data.get('d') or data
    
    if not package:
        return f"Package not found: {package_id}"
    
    technical_name = package.get('TechnicalName', 'N/A')
    display_name = package.get('DisplayName', 'N/A')
    version = package.get('Version', 'N/A')
    description = package.get('Description', 'No description')
    
    return f"""Package Information:
Display Name: {display_name}
Technical ID: {technical_name}
Version: {version}
Description: {description.strip()}"""


@mcp.tool()
async def find_sap_apis_by_protocol(
    protocol: str,
    package_id: Optional[str] = None,
    state: Optional[str] = "ACTIVE",
    max_results: int = 50
) -> str:
    """
    Find APIs by protocol type (ODATAV4, ODATA, SOAP, REST).
    
    Args:
        protocol: Protocol type (e.g., 'ODATAV4', 'ODATA', 'SOAP', 'REST').
        package_id: Optional package filter.
        state: Optional state filter (default: 'ACTIVE').
        max_results: Maximum results (default: 50).
    """
    if package_id:
        base_url = f"{CONTENT_PACKAGES_URL}('{package_id}')/Artifacts"
    else:
        base_url = ARTIFACTS_URL
    
    filters = [
        "Type eq 'API'",
        f"SubType eq '{escape_odata_string(protocol)}'"
    ]
    if state:
        filters.append(f"State eq '{escape_odata_string(state)}'")
    
    params = {
        "$format": "json",
        "$filter": " and ".join(filters),
        "$top": str(max_results),
        "$select": "Name,DisplayName,Type,SubType,Version,State,Description"
    }
    
    print(f"Finding APIs by protocol: {protocol}")
    data = await make_sap_api_request(base_url, params=params)
    
    if not data:
        return f"Unable to find APIs with protocol: {protocol}"
    
    results = data.get('value') or data.get('d', {}).get('results', [])
    
    if not results:
        return f"No APIs found with protocol: {protocol}"
    
    formatted = [format_artifact_entry(entry) for entry in results]
    
    return f"Found {len(results)} API(s) with protocol '{protocol}':\n\n" + "\n\n---\n\n".join(formatted)


@mcp.tool()
async def find_recent_sap_artifacts(
    sort_by: str = "modified",
    days: Optional[int] = None,
    max_results: int = 20
) -> str:
    """
    Find recently updated or newly created artifacts.
    
    Args:
        sort_by: Sort by 'modified' or 'created' (default: 'modified').
        days: Optional number of days to look back.
        max_results: Maximum results (default: 20).
    """
    base_url = ARTIFACTS_URL
    
    order_by = "ModifiedAt desc" if sort_by == "modified" else "CreatedAt desc"
    
    params = {
        "$format": "json",
        "$orderby": order_by,
        "$top": str(max_results),
        "$select": "Name,DisplayName,Type,SubType,Version,State,ModifiedAt,CreatedAt,Description"
    }
    
    # Add date filter if days specified
    if days:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        date_field = "ModifiedAt" if sort_by == "modified" else "CreatedAt"
        params["$filter"] = f"{date_field} ge {cutoff_date}"
    
    print(f"Finding recent artifacts: sort_by={sort_by}, days={days}")
    data = await make_sap_api_request(base_url, params=params)
    
    if not data:
        return "Unable to fetch recent artifacts"
    
    results = data.get('value') or data.get('d', {}).get('results', [])
    
    if not results:
        return "No recent artifacts found"
    
    formatted = [format_artifact_entry(entry) for entry in results]
    
    return f"Found {len(results)} recent artifact(s) (sorted by {sort_by}):\n\n" + "\n\n---\n\n".join(formatted)


@mcp.tool()
async def count_sap_artifacts(
    package_id: Optional[str] = None,
    artifact_type: Optional[str] = None,
    state: Optional[str] = None
) -> str:
    """
    Get count of artifacts with optional filters.
    
    Args:
        package_id: Optional package filter.
        artifact_type: Optional type filter.
        state: Optional state filter.
    """
    if package_id:
        base_url = f"{CONTENT_PACKAGES_URL}('{package_id}')/Artifacts/$count"
    else:
        base_url = f"{ARTIFACTS_URL}/$count"
    
    # For count endpoint, we need to use filter in URL if package_id not provided
    if not package_id:
        filters = []
        if artifact_type:
            filters.append(f"Type eq '{escape_odata_string(artifact_type)}'")
        if state:
            filters.append(f"State eq '{escape_odata_string(state)}'")
        
        if filters:
            # Use filter endpoint instead of count endpoint
            params = {
                "$format": "json",
                "$filter": " and ".join(filters),
                "$count": "true",
                "$top": "1"
            }
            data = await make_sap_api_request(ARTIFACTS_URL, params=params)
            if data:
                count = data.get('@odata.count') or data.get('d', {}).get('__count', 'Unknown')
                return f"Count: {count} artifact(s)"
    else:
        # For package-specific count, use count endpoint
        params = {"$format": "json"}
        data = await make_sap_api_request(base_url, params=params)
        if data:
            # Count endpoint returns just the number
            count = data if isinstance(data, (int, str)) else data.get('value', data)
            return f"Count: {count} artifact(s) in package '{package_id}'"
    
    return "Unable to get artifact count"


@mcp.tool()
async def find_deprecated_sap_apis(
    package_id: Optional[str] = None,
    max_results: int = 50
) -> str:
    """
    Find deprecated APIs that may need migration.
    
    Args:
        package_id: Optional package filter.
        max_results: Maximum results (default: 50).
    """
    if package_id:
        base_url = f"{CONTENT_PACKAGES_URL}('{package_id}')/Artifacts"
    else:
        base_url = ARTIFACTS_URL
    
    filters = [
        "Type eq 'API'",
        "State eq 'DEPRECATED'"
    ]
    
    params = {
        "$format": "json",
        "$filter": " and ".join(filters),
        "$top": str(max_results),
        "$select": "Name,DisplayName,Type,SubType,Version,State,Description"
    }
    
    print(f"Finding deprecated APIs in package: {package_id or 'all'}")
    data = await make_sap_api_request(base_url, params=params)
    
    if not data:
        return "Unable to find deprecated APIs"
    
    results = data.get('value') or data.get('d', {}).get('results', [])
    
    if not results:
        return "No deprecated APIs found"
    
    formatted = [format_artifact_entry(entry) for entry in results]
    
    return f"Found {len(results)} deprecated API(s):\n\n" + "\n\n---\n\n".join(formatted)


@mcp.tool()
async def get_artifact_packages(artifact_name: str, artifact_type: str = "API") -> str:
    """
    Find which packages contain a specific artifact.
    
    Args:
        artifact_name: Technical name of the artifact.
        artifact_type: Type of artifact (default: 'API').
    """
    url = f"{ARTIFACTS_URL}(Name='{escape_odata_string(artifact_name)}',Type='{escape_odata_string(artifact_type)}')/ContentPackages"
    
    print(f"Finding packages for artifact: {artifact_name}")
    data = await make_sap_api_request(url)
    
    if not data:
        return f"Unable to find packages for artifact: {artifact_name}"
    
    results = data.get('value') or data.get('d', {}).get('results', [])
    
    if not results:
        return f"Artifact '{artifact_name}' not found in any packages"
    
    formatted = []
    for entry in results:
        technical_name = entry.get('TechnicalName', 'N/A')
        display_name = entry.get('DisplayName', 'N/A')
        formatted.append(f"Display Name: {display_name}\nTechnical ID: {technical_name}")
    
    return f"Artifact '{artifact_name}' found in {len(results)} package(s):\n\n" + "\n\n---\n\n".join(formatted)


@mcp.tool()
async def get_sap_service_metadata() -> str:
    """
    Get OData service metadata/schema for the SAP catalog service.
    This provides information about available entity sets, properties, and relationships.
    """
    url = f"{SAP_CATALOG_BASE}/$metadata"
    
    print("Fetching service metadata")
    # Metadata is typically XML, but we'll try JSON first
    params = {"$format": "json"}
    data = await make_sap_api_request(url, params=params)
    
    if not data:
        return "Unable to fetch service metadata. Note: Metadata may only be available in XML format."
    
    # Try to extract useful information
    if isinstance(data, dict):
        return f"Service metadata retrieved. Available entity sets and properties: {str(data)[:500]}..."
    else:
        return f"Service metadata: {str(data)[:1000]}..."


def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()