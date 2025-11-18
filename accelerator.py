import httpx
import asyncio
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, Optional, List

# Initialize FastMCP server
mcp = FastMCP("accelerator")

# Constants
SAP_CATALOG_BASE = "https://api.sap.com/odata/1.0/catalog.svc"
CONTENT_PACKAGES_URL = f"{SAP_CATALOG_BASE}/ContentPackages"
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
    version = entry.get('Version', 'N/A')

    return f"""Name: {name} (Type: {entry_type}, Version: {version})
Display Name: {display_name}
Description: {description.strip()}"""

@mcp.tool()
async def list_sap_content_packages(search_term: str = None) -> str:
    """
    Fetches a list of Content Packages from the SAP Business Accelerator Hub.
    
    Args:
        search_term: Optional keyword to filter packages (e.g., "S/4HANA", "Integration", "Public Edition").
                     Searches both the Display Name and Technical ID.
    """
    
    print(f"Querying SAP API for Content Packages. Filter: {search_term if search_term else 'None'}")
    # Use $select to only get the fields we need.
    # This is the key to getting all items without a timeout.
    params = {
        "$select": "TechnicalName,DisplayName,Version"
    }
    
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

    # --- FILTERING LOGIC ---
    if search_term:
        term = search_term.lower()
        # Filter results where the term appears in DisplayName OR TechnicalName
        results = [
            entry for entry in results 
            if term in entry.get('DisplayName', '').lower() 
            or term in entry.get('TechnicalName', '').lower()
        ]
        
        if not results:
            return f"No content packages found matching the search term: '{search_term}'"

    print(f"Found {len(results)} entries matching filter.")
    # Format each entry and join with a clear separator
    formatted_entries = [format_package_list_entry(entry) for entry in results]
    
    return "\n\n----------------------------------------\n\n".join(formatted_entries)


@mcp.tool()
async def get_sap_package_artifacts(package_id: str, artifact_type: str = None) -> str:
    """
    Get artifacts (details) for a specific Content Package.

    Args:
        package_id: The Technical ID of the package (e.g., 'TSC_InvoiceToCashOilAndGasMbp405').
        artifact_type: Optional filter for the type of artifact (e.g., "IntegrationFlow", "ValueMapping", "Script").
    """
    print(f"Querying SAP API for artifacts in package: {package_id}. Filter Type: {artifact_type if artifact_type else 'None'}")
    
    # Construct the URL to get artifacts for a specific package
    url = f"{CONTENT_PACKAGES_URL}('{package_id}')/Artifacts"
    
    # We don't need $select here, as we want all artifact details
    data = await make_sap_api_request(url)

    if not data:
        return f"Unable to fetch artifacts for package ID: {package_id}"

    results: Optional[List[Dict[str, Any]]] = None
    if 'd' in data and 'results' in data['d']:
        results = data['d']['results']  # OData v2
    elif 'value' in data:
        results = data['value']  # OData v4
    
    if not results:
        return f"No artifacts found for package: {package_id}"

    # --- FILTERING LOGIC ---
    if artifact_type:
        term = artifact_type.lower()
        results = [
            entry for entry in results
            if term in entry.get('Type', '').lower()
        ]
        
        if not results:
            return f"No artifacts found in package '{package_id}' matching type: '{artifact_type}'"

    print(f"Found {len(results)} artifacts.")
    # Format each entry and join with a clear separator
    formatted_entries = [format_artifact_entry(entry) for entry in results]
    
    return "\n\n----------------------------------------\n\n".join(formatted_entries)

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()