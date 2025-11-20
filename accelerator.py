import httpx
import asyncio
import sys
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from urllib.parse import quote

# Configure logging to both file and stderr
LOG_DIR = Path.home() / ".sap-api-accelerator-mcp"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "accelerator.log"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("accelerator")

# Constants
SAP_CATALOG_BASE = "https://api.sap.com/odata/1.0/catalog.svc"
CONTENT_PACKAGES_URL = f"{SAP_CATALOG_BASE}/ContentPackages"
ARTIFACTS_URL = f"{SAP_CATALOG_BASE}/Artifacts"
USER_AGENT = "sap-api-accelerator-mcp/1.0"

async def make_sap_api_request(url: str, params: Optional[Dict[str, Any]] = None, return_error: bool = False) -> Optional[Dict[str, Any]]:
    """
    Make a request to the SAP OData API with proper error handling.

    This function automatically requests the JSON format and does not use an API key.
    
    Args:
        url: The API endpoint URL
        params: Optional query parameters
        return_error: If True, returns error details as dict instead of None
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",  # Request JSON format
    }

    # Ensure $format=json is in the parameters
    if params is None:
        params = {}
    params["$format"] = "json"

    logger.info(f"Making request to: {url} with params: {params}")

    async with httpx.AsyncClient() as client:
        try:
            # Set a long timeout (5 minutes) to handle slow API responses
            response = await client.get(url, headers=headers, params=params, timeout=300.0)
            
            # Raise an exception for 4xx or 5xx status codes
            response.raise_for_status()
            
            # Return the parsed JSON response
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200] if e.response.text else 'No error details'}"
            logger.error(f"HTTP error occurred: {e}")
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text[:500] if e.response.text else 'No response body'}")
            if return_error:
                return {"error": error_msg, "status_code": e.response.status_code, "url": str(e.request.url)}
            return None
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"An error occurred while requesting {e.request.url!r}: {e}")
            if return_error:
                return {"error": error_msg, "url": str(e.request.url) if hasattr(e, 'request') else url}
            return None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"An unexpected error occurred: {e}")
            if return_error:
                return {"error": error_msg}
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
    
    logger.info(f"Querying SAP API for Content Packages. Filter: {search_term if search_term else 'None'}")
    # Use $select to only get the fields we need.
    # This is the key to getting all items without a timeout.
    params = {
        "$select": "TechnicalName,DisplayName,Version",
        "$top": str(max_results * 10 if search_term else max_results)  # Fetch more if filtering client-side
    }
    
    # Try OData filter if search_term provided
    # Use substringof for OData v2 compatibility (SAP API uses OData v2)
    if search_term:
        safe_term = escape_odata_string(search_term)
        params["$filter"] = f"(substringof('{safe_term}',DisplayName) eq true or substringof('{safe_term}',TechnicalName) eq true)"
    
    data = await make_sap_api_request(CONTENT_PACKAGES_URL, params=params, return_error=True)
    
    if not data:
        return "Unable to fetch content packages. Please check the server logs for detailed error information."
    
    # Check if we got an error response (filter might not be supported)
    if 'error' in data:
        error_details = data.get('error', 'Unknown error')
        status_code = data.get('status_code', 'N/A')
        
        # If filter failed, try fetching all and filtering client-side
        if status_code == 400 and search_term:
            logger.warning(f"OData filter not supported. Fetching all packages and filtering client-side...")
            
            # Fetch without filter
            fetch_params = {
                "$select": "TechnicalName,DisplayName,Version",
                "$top": str(max_results * 10)  # Fetch more to account for client-side filtering
            }
            
            data = await make_sap_api_request(CONTENT_PACKAGES_URL, params=fetch_params, return_error=True)
            
            if not data or 'error' in data:
                return f"Unable to fetch content packages. Error: {data.get('error', 'Unknown error') if data else 'No response'}"
            
            # Filter client-side
            results: Optional[List[Dict[str, Any]]] = None
            if 'd' in data and 'results' in data['d']:
                results = data['d']['results']  # OData v2
            elif 'value' in data:
                results = data['value']  # OData v4
            
            if results:
                search_lower = search_term.lower()
                results = [
                    r for r in results 
                    if search_lower in r.get('DisplayName', '').lower() or search_lower in r.get('TechnicalName', '').lower()
                ]
                results = results[:max_results]  # Limit to max_results
        else:
            return f"Unable to fetch content packages. Error: {error_details} (Status: {status_code})"
    else:
        # Normal response processing
        results: Optional[List[Dict[str, Any]]] = None
        if 'd' in data and 'results' in data['d']:
            results = data['d']['results']  # OData v2
        elif 'value' in data:
            results = data['value']  # OData v4
    
    if not results:
        if search_term:
            return f"No content packages found matching '{search_term}'. Try searching without a filter to see all available packages."
        return "No content packages found or response format was unexpected."

    logger.info(f"Found {len(results)} entries matching filter.")
    # Format each entry and join with a clear separator
    formatted_entries = [format_package_list_entry(entry) for entry in results]
    
    return f"Found {len(results)} content package(s):\n\n" + "\n\n----------------------------------------\n\n".join(formatted_entries)


@mcp.tool()
async def get_sap_artifact_details(artifact_name: str, artifact_type: str = "API") -> str:
    """
    Get complete details for a specific artifact.
    
    Args:
        artifact_name: Technical name of the artifact (e.g., 'CE_PROJECTDEMANDCATEGORY_0001').
        artifact_type: Type of artifact (default: 'API').
    """
    url = f"{ARTIFACTS_URL}(Name='{escape_odata_string(artifact_name)}',Type='{escape_odata_string(artifact_type)}')"
    
    logger.info(f"Fetching details for artifact: {artifact_name} (Type: {artifact_type})")
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
    
    logger.info(f"Listing artifacts by type: {artifact_type}, subtype: {subtype}")
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
    
    logger.info(f"Fetching package info: {package_id}")
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
    
    logger.info(f"Finding deprecated APIs in package: {package_id or 'all'}")
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
    
    logger.info(f"Finding packages for artifact: {artifact_name}")
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
    
    logger.info("Fetching service metadata")
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