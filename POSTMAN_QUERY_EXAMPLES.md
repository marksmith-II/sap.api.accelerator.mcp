# Postman Collection - Recommended Query Examples

This document provides specific OData queries you can add to your Postman collection to explore the SAP API Business Hub catalog. These queries demonstrate the full potential of the API and can be used to test and validate MCP tool implementations.

## Base URL
```
https://api.sap.com/odata/1.0/catalog.svc
```

## Query Format
All queries should include `$format=json` parameter to get JSON responses instead of XML.

---

## 1. Discovery Queries

### 1.1 Get All Content Packages (Enhanced)
**Request Name**: `Content Packages - Full Details`
```
GET /ContentPackages?$format=json&$select=TechnicalName,DisplayName,Version,Description
```
**Purpose**: Get all packages with key details
**Use Case**: Initial discovery of available packages

### 1.2 Search Packages by Name
**Request Name**: `Search Packages - S/4HANA`
```
GET /ContentPackages?$format=json&$filter=contains(DisplayName,'S/4HANA')
```
**Purpose**: Find packages containing "S/4HANA" in name
**Use Case**: Find specific package categories

### 1.3 Get Service Metadata
**Request Name**: `Service Metadata`
```
GET /$metadata?$format=json
```
**Purpose**: Get complete OData service schema
**Use Case**: Understand all available entity sets and properties

### 1.4 Get Service Root
**Request Name**: `Service Root - Entity Sets`
```
GET /?$format=json
```
**Purpose**: Discover available entity sets
**Use Case**: API exploration

---

## 2. Artifact Search Queries

### 2.1 Search All Artifacts by Keyword
**Request Name**: `Search Artifacts - Order`
```
GET /Artifacts?$format=json&$filter=contains(DisplayName,'Order') or contains(Description,'Order')&$top=20
```
**Purpose**: Find all artifacts related to "Order"
**Use Case**: Universal search across all packages

### 2.2 Search Artifacts in Package
**Request Name**: `Search Artifacts in Package - Project`
```
GET /ContentPackages('SAPS4HANACloud')/Artifacts?$format=json&$filter=contains(DisplayName,'Project')&$top=20
```
**Purpose**: Search within a specific package
**Use Case**: Focused search in known package

### 2.3 Filter by Artifact Type
**Request Name**: `All APIs Only`
```
GET /Artifacts?$format=json&$filter=Type eq 'API'&$top=50
```
**Purpose**: Get only API artifacts
**Use Case**: Filter by artifact category

### 2.4 Filter by Protocol Type
**Request Name**: `ODATA V4 APIs Only`
```
GET /Artifacts?$format=json&$filter=Type eq 'API' and SubType eq 'ODATAV4'&$top=50
```
**Purpose**: Find only OData V4 APIs
**Use Case**: Protocol-specific discovery

### 2.5 Filter by State
**Request Name**: `Active APIs Only`
```
GET /Artifacts?$format=json&$filter=Type eq 'API' and State eq 'ACTIVE'&$top=50
```
**Purpose**: Get only active APIs
**Use Case**: Exclude deprecated/inactive items

### 2.6 Combined Filter - Active OData V4 APIs
**Request Name**: `Active ODATA V4 APIs`
```
GET /Artifacts?$format=json&$filter=Type eq 'API' and SubType eq 'ODATAV4' and State eq 'ACTIVE'&$top=50
```
**Purpose**: Complex multi-criteria search
**Use Case**: Precise filtering

---

## 3. Package-Specific Queries

### 3.1 Get Package Details
**Request Name**: `Package Details - SAPS4HANACloud`
```
GET /ContentPackages('SAPS4HANACloud')?$format=json
```
**Purpose**: Get complete package information
**Use Case**: Package metadata

### 3.2 Get All Artifacts in Package
**Request Name**: `All Artifacts - SAPS4HANACloud`
```
GET /ContentPackages('SAPS4HANACloud')/Artifacts?$format=json&$select=Name,DisplayName,Type,SubType,Version,State&$top=100
```
**Purpose**: Get all artifacts with key fields
**Use Case**: Package overview

### 3.3 Count Artifacts in Package
**Request Name**: `Artifact Count - SAPS4HANACloud`
```
GET /ContentPackages('SAPS4HANACloud')/Artifacts/$count?$format=json
```
**Purpose**: Get total count of artifacts
**Use Case**: Package statistics

### 3.4 Filter Artifacts in Package by Type
**Request Name**: `APIs in Package - SAPS4HANACloud`
```
GET /ContentPackages('SAPS4HANACloud')/Artifacts?$format=json&$filter=Type eq 'API'&$select=Name,DisplayName,SubType,Version
```
**Purpose**: Get only APIs from package
**Use Case**: Type-specific package exploration

### 3.5 Sort Artifacts by Name
**Request Name**: `Artifacts Sorted - SAPS4HANACloud`
```
GET /ContentPackages('SAPS4HANACloud')/Artifacts?$format=json&$orderby=DisplayName&$top=50
```
**Purpose**: Alphabetically sorted artifacts
**Use Case**: Organized browsing

---

## 4. Artifact Detail Queries

### 4.1 Get Single Artifact Details
**Request Name**: `Artifact Details - CE_PROJECTDEMANDCATEGORY_0001`
```
GET /Artifacts(Name='CE_PROJECTDEMANDCATEGORY_0001',Type='API')?$format=json
```
**Purpose**: Get complete artifact information
**Use Case**: Detailed artifact inspection

### 4.2 Get Artifact Content/Definition
**Request Name**: `Artifact Content - CE_PROJECTDEMANDCATEGORY_0001`
```
GET /Artifacts(Name='CE_PROJECTDEMANDCATEGORY_0001',Type='API')/$value
```
**Purpose**: Download artifact definition/documentation
**Use Case**: Get API specification

### 4.3 Get Packages for Artifact
**Request Name**: `Artifact Packages - CE_PROJECTDEMANDCATEGORY_0001`
```
GET /Artifacts(Name='CE_PROJECTDEMANDCATEGORY_0001',Type='API')/ContentPackages?$format=json
```
**Purpose**: Find which packages contain this artifact
**Use Case**: Relationship navigation

---

## 5. Analytics & Statistics Queries

### 5.1 Recent Updates
**Request Name**: `Recently Modified Artifacts`
```
GET /Artifacts?$format=json&$orderby=ModifiedAt desc&$top=20&$select=Name,DisplayName,ModifiedAt,Version
```
**Purpose**: Find recently updated artifacts
**Use Case**: Track changes

### 5.2 New Artifacts
**Request Name**: `Recently Created Artifacts`
```
GET /Artifacts?$format=json&$orderby=CreatedAt desc&$top=20&$select=Name,DisplayName,CreatedAt,Version
```
**Purpose**: Find newly added artifacts
**Use Case**: Discover new APIs

### 5.3 Artifacts by Version
**Request Name**: `Latest Version APIs`
```
GET /Artifacts?$format=json&$filter=Type eq 'API'&$orderby=Version desc&$top=20
```
**Purpose**: Find APIs with latest versions
**Use Case**: Version tracking

### 5.4 Deprecated Artifacts
**Request Name**: `Deprecated APIs`
```
GET /Artifacts?$format=json&$filter=Type eq 'API' and State eq 'DEPRECATED'&$select=Name,DisplayName,Version
```
**Purpose**: Find deprecated APIs
**Use Case**: Migration planning

---

## 6. Advanced Filtering Queries

### 6.1 Multiple Keywords (OR)
**Request Name**: `Search - Order OR Invoice`
```
GET /Artifacts?$format=json&$filter=(contains(DisplayName,'Order') or contains(DisplayName,'Invoice'))&$top=30
```
**Purpose**: Search with multiple keywords (OR logic)
**Use Case**: Broader search

### 6.2 Multiple Keywords (AND)
**Request Name**: `Search - Project AND Demand`
```
GET /Artifacts?$format=json&$filter=contains(DisplayName,'Project') and contains(DisplayName,'Demand')&$top=30
```
**Purpose**: Search requiring all keywords (AND logic)
**Use Case**: Precise search

### 6.3 Version Comparison
**Request Name**: `APIs Version >= 1.5`
```
GET /Artifacts?$format=json&$filter=Type eq 'API' and Version ge '1.5.0'&$top=30
```
**Purpose**: Find APIs with version >= 1.5.0
**Use Case**: Version filtering

### 6.4 Date Range Filter
**Request Name**: `Artifacts Modified Last 30 Days`
```
GET /Artifacts?$format=json&$filter=ModifiedAt ge 2025-10-17T00:00:00Z&$orderby=ModifiedAt desc&$top=50
```
**Purpose**: Find artifacts modified in date range
**Use Case**: Recent activity tracking

---

## 7. Pagination Queries

### 7.1 First Page
**Request Name**: `Artifacts - Page 1`
```
GET /Artifacts?$format=json&$top=20&$skip=0&$select=Name,DisplayName,Type
```
**Purpose**: First 20 artifacts
**Use Case**: Pagination

### 7.2 Second Page
**Request Name**: `Artifacts - Page 2`
```
GET /Artifacts?$format=json&$top=20&$skip=20&$select=Name,DisplayName,Type
```
**Purpose**: Next 20 artifacts
**Use Case**: Pagination continuation

### 7.3 With Count
**Request Name**: `Artifacts with Count`
```
GET /Artifacts?$format=json&$top=20&$count=true&$select=Name,DisplayName
```
**Purpose**: Get results with total count
**Use Case**: Pagination with total

---

## 8. Sorting Queries

### 8.1 Sort by Display Name
**Request Name**: `Artifacts Sorted by Name`
```
GET /Artifacts?$format=json&$orderby=DisplayName&$top=50
```
**Purpose**: Alphabetical sorting
**Use Case**: Organized listing

### 8.2 Sort by Version (Descending)
**Request Name**: `Artifacts Sorted by Version`
```
GET /Artifacts?$format=json&$orderby=Version desc&$top=50
```
**Purpose**: Latest versions first
**Use Case**: Version priority

### 8.3 Multi-Column Sort
**Request Name**: `Artifacts Sorted by Type and Name`
```
GET /Artifacts?$format=json&$orderby=Type,DisplayName&$top=50
```
**Purpose**: Sort by multiple columns
**Use Case**: Grouped and sorted results

---

## 9. Field Selection Queries

### 9.1 Minimal Fields
**Request Name**: `Artifacts - Minimal`
```
GET /Artifacts?$format=json&$select=Name,DisplayName&$top=50
```
**Purpose**: Only essential fields
**Use Case**: Fast listing

### 9.2 Key Fields
**Request Name**: `Artifacts - Key Fields`
```
GET /Artifacts?$format=json&$select=Name,DisplayName,Type,SubType,Version,State&$top=50
```
**Purpose**: Most important fields
**Use Case**: Summary view

### 9.3 All Fields (Default)
**Request Name**: `Artifacts - Full Details`
```
GET /Artifacts?$format=json&$top=10
```
**Purpose**: Complete artifact information
**Use Case**: Detailed inspection

---

## 10. Relationship Navigation Queries

### 10.1 Expand Artifacts in Package
**Request Name**: `Package with Artifacts Expanded`
```
GET /ContentPackages('SAPS4HANACloud')?$format=json&$expand=Artifacts($select=Name,DisplayName,Type)
```
**Purpose**: Get package with nested artifacts
**Use Case**: One-query package overview

### 10.2 Expand Packages for Artifact
**Request Name**: `Artifact with Packages Expanded`
```
GET /Artifacts(Name='CE_PROJECTDEMANDCATEGORY_0001',Type='API')?$format=json&$expand=ContentPackages
```
**Purpose**: Get artifact with associated packages
**Use Case**: Relationship exploration

---

## Implementation Notes

### Query Building Tips
1. **Always include `$format=json`** for JSON responses
2. **Use `$select`** to reduce payload size for large result sets
3. **Use `$top`** to limit results and avoid timeouts
4. **Combine filters with `and`** for multiple criteria
5. **Use `or`** for alternative conditions
6. **Escape special characters** in filter values (single quotes, etc.)

### Performance Considerations
- Start with `$top=20` or `$top=50` for initial testing
- Use `$select` to request only needed fields
- Add `$count=true` only when needed (adds overhead)
- Avoid `$expand` on large collections

### Error Handling
- Invalid filter syntax returns 400 Bad Request
- Non-existent entities return 404 Not Found
- Large result sets may timeout - use `$top` and pagination
- Special characters in filters may need URL encoding

---

## Recommended Postman Collection Structure

### Folder: 1. Discovery
- Service Root
- Service Metadata
- Content Packages - Full Details
- Search Packages - S/4HANA

### Folder: 2. Artifact Search
- Search Artifacts - Order
- All APIs Only
- ODATA V4 APIs Only
- Active APIs Only
- Active ODATA V4 APIs

### Folder: 3. Package Queries
- Package Details - SAPS4HANACloud
- All Artifacts - SAPS4HANACloud
- Artifact Count - SAPS4HANACloud
- APIs in Package - SAPS4HANACloud

### Folder: 4. Artifact Details
- Artifact Details - CE_PROJECTDEMANDCATEGORY_0001
- Artifact Content - CE_PROJECTDEMANDCATEGORY_0001
- Artifact Packages - CE_PROJECTDEMANDCATEGORY_0001

### Folder: 5. Analytics
- Recently Modified Artifacts
- Recently Created Artifacts
- Deprecated APIs
- APIs Version >= 1.5

### Folder: 6. Advanced
- Search - Order OR Invoice
- Search - Project AND Demand
- Artifacts - Page 1
- Artifacts - Page 2
- Artifacts Sorted by Name

---

## Testing Checklist

When implementing MCP tools, test these queries to validate:
- [ ] Basic search functionality
- [ ] Filter combinations
- [ ] Pagination
- [ ] Sorting
- [ ] Field selection
- [ ] Error handling
- [ ] Large result sets
- [ ] Special characters in search terms
- [ ] Date range filtering
- [ ] Relationship navigation

---

## Next Steps

1. **Add these queries to your Postman collection** - Organize them in folders
2. **Test each query** - Verify responses and understand data structure
3. **Identify patterns** - Note which queries are most useful
4. **Prioritize MCP tools** - Based on query usage and value
5. **Implement tools** - Start with high-value queries
6. **Iterate** - Add more queries as needs arise

