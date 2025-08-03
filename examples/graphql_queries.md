# GraphQL API Examples for A2A Registry AgentExtension System

This document provides comprehensive examples of GraphQL queries, mutations, and subscriptions for the AgentExtension system.

## Authentication

All requests require a JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Core Queries

### 1. Get Extension by ID

```graphql
query GetExtension($id: ID!) {
  extension(id: $id) {
    id
    name
    version
    description
    type
    trustLevel
    validationStatus
    status
    author
    downloadCount
    createdAt
    updatedAt
    content {
      format
      data
      documentation
    }
    dependencies {
      extensionId
      version
      optional
      extension {
        name
        version
      }
    }
    usageStats {
      totalDownloads
      weeklyDownloads
      activeInstallations
      popularityRank
      averageRating
    }
  }
}
```

**Variables:**
```json
{
  "id": "ext-uuid-1234"
}  
```

### 2. Advanced Extension Search

```graphql
query SearchExtensions(
  $search: ExtensionSearchInput
  $sort: ExtensionSortInput
  $first: Int
  $after: String
) {
  extensions(
    search: $search
    sort: $sort
    first: $first
    after: $after
  ) {
    edges {
      cursor
      node {
        id
        name
        version
        type
        trustLevel
        validationStatus
        downloadCount
        description
        tags
        author
        createdAt
        usageStats {
          totalDownloads
          activeInstallations
          popularityRank
        }
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
      totalCount
    }
  }
}
```

**Variables:**
```json
{
  "search": {
    "query": "authentication",
    "types": ["AUTHENTICATION", "SECURITY"],
    "trustLevels": ["VERIFIED", "OFFICIAL"],
    "minDownloads": 100,
    "hasValidSignature": true
  },
  "sort": {
    "field": "DOWNLOAD_COUNT", 
    "direction": "DESC"
  },
  "first": 20
}
```

### 3. Dependency Resolution

```graphql
query ResolveDependencies($extensionId: ID!, $version: String) {
  resolveDependencies(extensionId: $extensionId, version: $version) {
    extension {
      id
      name
      version
    }
    dependencies {
      extension {
        id
        name
        version
        type
      }
      requiredVersion
      children {
        extension {
          name
          version
        }
        requiredVersion
      }
    }
    conflicts {
      dependency
      requiredVersions
      resolution
    }
  }
}
```

### 4. Analytics Dashboard

```graphql
query ExtensionAnalytics($timeRange: String) {
  extensionAnalytics(timeRange: $timeRange) {
    totalExtensions
    totalDownloads
    extensionsByType {
      type
      count
    }
    extensionsByTrustLevel {
      trustLevel
      count
    }
    topExtensions {
      id
      name
      downloadCount
      type
      trustLevel
    }
    trendingExtensions {
      id
      name
      downloadCount
      createdAt
    }
  }
}
```

### 5. Agent-Extension Relationships

```graphql
query AgentExtensions($agentId: ID!) {
  agentExtensions(agentId: $agentId) {
    extensionId
    installedVersion
    installedAt
    lastUsed
    usageCount
    status
    configuration
    extension {
      name
      type
      description
      validationStatus
      trustLevel
    }
  }
}
```

### 6. Security Information

```graphql
query SecurityScan($extensionId: ID!) {
  securityScan(extensionId: $extensionId) {
    extensionId
    scanType
    result
    scanDate
    scanner
    vulnerabilities {
      id
      severity
      description
      cveId
      fixedIn  
    }
  }
}
```

### 7. Compatibility Check

```graphql
query CheckCompatibility($extensionId: ID!, $agentId: ID!) {
  checkCompatibility(extensionId: $extensionId, agentId: $agentId) {
    platform
    version
    tested
    issues
  }
}
```

### 8. Full-Text Search

```graphql
query SearchExtensions($query: String!, $limit: Int) {
  searchExtensions(query: $query, limit: $limit) {
    id
    name
    description
    type
    trustLevel
    downloadCount
    tags
    author
  }
}
```

### 9. Recommendations

```graphql
query RecommendExtensions($agentId: ID!, $limit: Int) {
  recommendExtensions(agentId: $agentId, limit: $limit) {
    id
    name
    description
    type
    downloadCount
    trustLevel
    usageStats {
      popularityRank
      averageRating
    }
  }
}
```

## Mutations

### 1. Create Extension

```graphql
mutation CreateExtension($input: CreateExtensionInput!) {
  createExtension(input: $input) {
    success
    extension {
      id
      name
      version
      type
      status
      createdAt
    }
    errors
  }
}
```

**Variables:**
```json
{
  "input": {
    "name": "Advanced Authentication Extension",
    "description": "Multi-factor authentication extension with biometric support",
    "type": "AUTHENTICATION",
    "content": {
      "format": "json",
      "data": {
        "entrypoint": "auth_extension.main",
        "config_schema": {
          "type": "object",
          "properties": {
            "mfa_enabled": {"type": "boolean"},
            "biometric_types": {"type": "array"}
          }
        }
      },
      "documentation": "# Authentication Extension\n\nProvides advanced authentication capabilities..."
    },
    "tags": ["auth", "security", "mfa", "biometric"],
    "license": "MIT",
    "homepage": "https://github.com/example/auth-extension",
    "repository": "https://github.com/example/auth-extension.git",
    "dependencies": [
      {
        "extensionId": "base-security-ext-123",
        "version": "^2.0.0",
        "optional": false
      }
    ]
  }
}
```

### 2. Update Extension

```graphql
mutation UpdateExtension($id: ID!, $input: UpdateExtensionInput!) {
  updateExtension(id: $id, input: $input) {
    success
    extension {
      id
      name
      version
      updatedAt
      updatedBy
    }
    errors
  }
}
```

### 3. Publish Extension

```graphql
mutation PublishExtension($id: ID!) {
  publishExtension(id: $id) {
    success
    extension {
      id
      name
      status
      publishedAt
      validationStatus
    }
    errors
  }
}
```

### 4. Install Extension on Agent

```graphql
mutation InstallExtension(
  $agentId: ID!
  $extensionId: ID!
  $version: String
  $configuration: JSON
) {
  installExtension(
    agentId: $agentId
    extensionId: $extensionId
    version: $version
    configuration: $configuration
  )
}
```

**Variables:**
```json
{
  "agentId": "agent-123",
  "extensionId": "ext-456", 
  "version": "1.2.0",
  "configuration": {
    "api_key": "encrypted-key-value",
    "timeout": 30,
    "retries": 3
  }
}
```

### 5. Delete Extension

```graphql
mutation DeleteExtension($id: ID!) {
  deleteExtension(id: $id) {
    success
    errors
  }
}
```

## Subscriptions

### 1. Extension Updates

```graphql
subscription ExtensionUpdated($extensionId: ID) {
  extensionUpdated(extensionId: $extensionId) {
    extension {
      id
      name
      status
      validationStatus
      updatedAt
    }
    changeType
  }
}
```

### 2. Security Alerts

```graphql  
subscription SecurityAlert($extensionId: ID) {
  securityAlert(extensionId: $extensionId) {
    extensionId
    alertType
    severity
    message
    scanResult {
      result
      vulnerabilities {
        severity
        description
      }
    }
  }
}
```

### 3. Real-time Usage Metrics

```graphql
subscription UsageMetrics($extensionId: ID!) {
  usageMetrics(extensionId: $extensionId) {
    totalDownloads
    weeklyDownloads
    activeInstallations
    popularityRank
  }
}
```

## Complex Multi-Operation Queries

### 1. Extension Dashboard

```graphql
query ExtensionDashboard($extensionId: ID!) {
  extension(id: $extensionId) {
    id
    name
    version
    description
    type
    trustLevel
    validationStatus
    status
    downloadCount
    createdAt
    updatedAt
    
    # Content and metadata
    content {
      format
      documentation
    }
    tags
    author
    license
    
    # Usage analytics
    usageStats {
      totalDownloads
      weeklyDownloads
      monthlyDownloads
      activeInstallations
      popularityRank
      averageRating
      reviewCount
    }
    
    # Dependencies
    dependencies {
      extensionId
      version
      optional
      extension {
        name
        version
        trustLevel
      }
    }
    
    # Agents using this extension
    agents {
      agentId
      installedVersion
      installedAt
      lastUsed
      usageCount
      status
    }
    
    # Compatibility info
    compatibility {
      platform
      version
      tested
      issues
    }
  }
  
  # Security scan
  securityScan(extensionId: $extensionId) {
    result
    scanDate
    vulnerabilities {
      severity
      description
    }
  }
  
  # Dependency tree
  resolveDependencies(extensionId: $extensionId) {
    conflicts {
      dependency
      requiredVersions
      resolution
    }
  }
}
```

### 2. Agent Extension Management

```graphql
query AgentExtensionManagement($agentId: ID!) {
  # Current extensions
  agentExtensions(agentId: $agentId) {
    extensionId
    installedVersion
    installedAt
    lastUsed
    usageCount
    status
    configuration
    extension {
      name
      type
      description
      trustLevel
      validationStatus
      
      # Check for updates
      version
      updatedAt
      
      # Security status
      # Note: Would need to resolve via extension query
    }
  }
  
  # Recommendations
  recommendExtensions(agentId: $agentId, limit: 5) {
    id
    name
    description
    type
    downloadCount
    trustLevel
    usageStats {
      popularityRank
      averageRating
    }
  }
  
  # Agent info from existing system
  agent(id: $agentId) {
    name
    description
    version
    capabilities
    skills {
      id
      name
    }
  }
}
```

## Error Handling

GraphQL errors are returned in the standard format:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Access denied: insufficient permissions",
      "extensions": {
        "code": "PERMISSION_DENIED",
        "field": "extension"
      },
      "path": ["extension"]
    }
  ]
}
```

## Rate Limiting

- 1000 requests per minute per authenticated user
- 100 requests per minute for unauthenticated users  
- Complex queries (analytics, dependency resolution) have additional limits

## Security Features

- **Field-level Authorization**: Different fields require different permissions
- **Query Complexity Analysis**: Prevents expensive queries from overwhelming the system
- **Input Sanitization**: All inputs are validated and sanitized
- **Audit Logging**: All mutations and sensitive queries are logged
- **Rate Limiting**: Prevents abuse and ensures fair usage

## Best Practices

1. **Use Fragments** for repeated field selections:
```graphql
fragment ExtensionBasic on AgentExtension {
  id
  name
  version
  type
  trustLevel
  downloadCount
}

query GetMultipleExtensions {
  popular: extensions(sort: {field: DOWNLOAD_COUNT, direction: DESC}, first: 5) {
    edges {
      node {
        ...ExtensionBasic
      }
    }
  }
  
  recent: extensions(sort: {field: CREATED_AT, direction: DESC}, first: 5) {
    edges {
      node {
        ...ExtensionBasic
      }
    }
  }
}
```

2. **Use Variables** for dynamic queries instead of string concatenation

3. **Request Only Needed Fields** to optimize performance

4. **Use Pagination** for large result sets

5. **Handle Errors Gracefully** by checking both data and errors in responses

6. **Use Subscriptions Sparingly** - they maintain persistent connections

This GraphQL API provides powerful querying capabilities while maintaining security and performance through proper authorization, pagination, and complexity analysis.