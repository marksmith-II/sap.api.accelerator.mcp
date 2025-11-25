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

async def make_sap_api_request(url: str, params: Optional[Dict[str, Any]] = None, return_error: bool = False, accept_xml: bool = False) -> Optional[Any]:
    """
    Make a request to the SAP OData API with proper error handling.

    This function automatically requests the JSON format and does not use an API key.
    
    Args:
        url: The API endpoint URL
        params: Optional query parameters
        return_error: If True, returns error details as dict instead of None
        accept_xml: If True, accepts XML format (for $metadata requests)
    """
    headers = {
        "User-Agent": USER_AGENT,
    }
    
    if accept_xml:
        headers["Accept"] = "application/xml, application/atom+xml"
    else:
        headers["Accept"] = "application/json"
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
            
            # Return the parsed response
            if accept_xml:
                return response.text
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
    logger.info(f"Fetching details for artifact: {artifact_name} (Type: {artifact_type})")
    
    # The /Artifacts endpoint doesn't support direct lookups (405) or filtering
    # So we'll search through packages to find the artifact
    # Strategy: Get list of packages, then search their artifacts
    
    logger.info("Fetching packages to search for artifact...")
    packages_params = {
        "$format": "json",
        "$top": "1000",  # Get a large number of packages to ensure we find the artifact
        "$select": "TechnicalName,DisplayName"
    }
    
    packages_data = await make_sap_api_request(CONTENT_PACKAGES_URL, params=packages_params, return_error=True)
    
    if not packages_data or 'error' in packages_data:
        # If we can't get packages, try fetching artifacts directly (may work without filters)
        logger.warning("Could not fetch packages. Trying direct artifact fetch...")
        fetch_params = {
            "$format": "json",
            "$top": "10000",  # Try to fetch a very large number
            "$select": "Name,DisplayName,Type,SubType,Version,State,Description,reg_id,CreatedAt,ModifiedAt"
        }
        
        artifacts_data = await make_sap_api_request(ARTIFACTS_URL, params=fetch_params, return_error=True)
        
        if artifacts_data and 'error' not in artifacts_data:
            results = artifacts_data.get('value') or artifacts_data.get('d', {}).get('results', [])
            
            if results:
                # Search for exact match
                for artifact in results:
                    if (artifact.get('Name', '').upper() == artifact_name.upper() and 
                        artifact.get('Type', '').upper() == artifact_type.upper()):
                        logger.info(f"Found artifact '{artifact_name}' in direct fetch (searched {len(results)} artifacts)")
                        return format_artifact_detailed(artifact)
        
        return f"Unable to fetch artifact details for: {artifact_name} (Type: {artifact_type}). Could not access packages or artifacts list."
    
    # Get packages list
    packages = packages_data.get('value') or packages_data.get('d', {}).get('results', [])
    
    if not packages:
        return f"Unable to fetch artifact details for: {artifact_name} (Type: {artifact_type}). No packages available to search."
    
    logger.info(f"Searching for artifact in {len(packages)} packages using concurrent requests...")
    
    # Use concurrent requests with early termination
    # Limit concurrency to avoid overwhelming the API
    MAX_CONCURRENT = 20
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    found_artifact = None
    found_event = asyncio.Event()
    tasks = []
    
    async def search_package_artifacts(package: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Search for artifact in a single package. Returns artifact if found, None otherwise."""
        # Early termination check
        if found_event.is_set():
            return None
        
        package_id = package.get('TechnicalName', '')
        if not package_id:
            return None
        
        async with semaphore:
            # Double-check early termination after acquiring semaphore
            if found_event.is_set():
                return None
            
            # Log progress periodically
            if (index + 1) % 50 == 0 or index == 0:
                logger.info(f"Searching package {index+1}/{len(packages)}: {package_id}")
            
            # Fetch artifacts from this package
            package_artifacts_url = f"{CONTENT_PACKAGES_URL}('{escape_odata_string(package_id)}')/Artifacts"
            package_artifacts_params = {
                "$format": "json",
                "$top": "1000",  # Get all artifacts from this package
                "$select": "Name,DisplayName,Type,SubType,Version,State,Description,reg_id,CreatedAt,ModifiedAt"
            }
            
            package_artifacts_data = await make_sap_api_request(package_artifacts_url, params=package_artifacts_params, return_error=True)
            
            if package_artifacts_data and 'error' not in package_artifacts_data:
                package_artifacts = package_artifacts_data.get('value') or package_artifacts_data.get('d', {}).get('results', [])
                
                # Search for exact match (case-insensitive)
                for artifact in package_artifacts:
                    if found_event.is_set():
                        return None
                    
                    if (artifact.get('Name', '').upper() == artifact_name.upper() and 
                        artifact.get('Type', '').upper() == artifact_type.upper()):
                        logger.info(f"Found artifact '{artifact_name}' in package '{package_id}' (searched {index+1} packages)")
                        return artifact
            
            return None
    
    # Create tasks for all packages
    for i, package in enumerate(packages):
        task = asyncio.create_task(search_package_artifacts(package, i))
        tasks.append(task)
    
    # Wait for first result or all tasks to complete
    try:
        # Use as_completed to get results as they arrive
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                if result is not None:
                    # Found the artifact - signal early termination
                    found_event.set()
                    found_artifact = result
                    
                    # Cancel remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    
                    # Wait for cancellations to complete (with timeout)
                    if tasks:
                        await asyncio.wait(tasks, timeout=1.0, return_when=asyncio.ALL_COMPLETED)
                    break
            except asyncio.CancelledError:
                # Task was cancelled, continue to next
                continue
    except Exception as e:
        logger.warning(f"Error during concurrent search: {e}")
        # Cancel all remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for cancellations
        if tasks:
            await asyncio.wait(tasks, timeout=1.0, return_when=asyncio.ALL_COMPLETED)
    
    if found_artifact:
        return format_artifact_detailed(found_artifact)
    
    return f"Artifact not found: {artifact_name} (Type: {artifact_type}). Searched {len(packages)} packages but no exact match found. Verify the artifact name and type are correct."



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


def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()