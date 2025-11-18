# Postman Queries to Add to MCP Collection

This document lists the recommended queries to add to your Postman collection. These queries correspond to the MCP tools we've implemented.

## Quick Add Guide

You can add these queries manually in Postman, or use the Postman API. Here are the top 15 queries organized by category:

### 1. Discovery Queries

#### Search Artifacts - Order
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts?$format=json&$filter=contains(DisplayName,'Order') or contains(Description,'Order')&$top=20
```

#### All APIs Only
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts?$format=json&$filter=Type eq 'API'&$top=50
```

#### Active ODATA V4 APIs
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts?$format=json&$filter=Type eq 'API' and SubType eq 'ODATAV4' and State eq 'ACTIVE'&$top=50
```

### 2. Package Queries

#### Package Details - SAPS4HANACloud
```
GET https://api.sap.com/odata/1.0/catalog.svc/ContentPackages('SAPS4HANACloud')?$format=json
```

#### All Artifacts - SAPS4HANACloud (with select)
```
GET https://api.sap.com/odata/1.0/catalog.svc/ContentPackages('SAPS4HANACloud')/Artifacts?$format=json&$select=Name,DisplayName,Type,SubType,Version,State&$top=100
```

#### Artifact Count - SAPS4HANACloud
```
GET https://api.sap.com/odata/1.0/catalog.svc/ContentPackages('SAPS4HANACloud')/Artifacts/$count?$format=json
```

### 3. Artifact Detail Queries

#### Artifact Details - CE_PROJECTDEMANDCATEGORY_0001
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts(Name='CE_PROJECTDEMANDCATEGORY_0001',Type='API')?$format=json
```

#### Artifact Packages - CE_PROJECTDEMANDCATEGORY_0001
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts(Name='CE_PROJECTDEMANDCATEGORY_0001',Type='API')/ContentPackages?$format=json
```

### 4. Analytics Queries

#### Recently Modified Artifacts
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts?$format=json&$orderby=ModifiedAt desc&$top=20&$select=Name,DisplayName,ModifiedAt,Version
```

#### Recently Created Artifacts
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts?$format=json&$orderby=CreatedAt desc&$top=20&$select=Name,DisplayName,CreatedAt,Version
```

#### Deprecated APIs
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts?$format=json&$filter=Type eq 'API' and State eq 'DEPRECATED'&$select=Name,DisplayName,Version
```

### 5. Protocol-Specific Queries

#### ODATA V4 APIs Only
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts?$format=json&$filter=Type eq 'API' and SubType eq 'ODATAV4'&$top=50
```

#### SOAP APIs Only
```
GET https://api.sap.com/odata/1.0/catalog.svc/Artifacts?$format=json&$filter=Type eq 'API' and SubType eq 'SOAP'&$top=50
```

### 6. Service Metadata

#### Service Metadata
```
GET https://api.sap.com/odata/1.0/catalog.svc/$metadata?$format=json
```

#### Service Root
```
GET https://api.sap.com/odata/1.0/catalog.svc/?$format=json
```

## How to Add These Queries

1. Open your MCP collection in Postman
2. Create folders: "Discovery", "Package Queries", "Artifact Details", "Analytics", "Protocol-Specific"
3. For each query above:
   - Click "Add Request"
   - Paste the URL
   - Set method to GET
   - Name it according to the comment above
   - Save to appropriate folder

## MCP Tool Mapping

These queries map to the following MCP tools:

- `search_sap_artifacts` → Search Artifacts queries
- `get_sap_package_info` → Package Details queries
- `get_sap_artifact_details` → Artifact Details queries
- `find_sap_apis_by_protocol` → Protocol-Specific queries
- `find_recent_sap_artifacts` → Analytics queries
- `find_deprecated_sap_apis` → Deprecated APIs query

