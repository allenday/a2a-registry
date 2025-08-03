# GraphQL Architecture for A2A Registry AgentExtension System

## Overview

The A2A Registry now includes a comprehensive GraphQL API for managing AgentExtensions, providing advanced querying capabilities, real-time subscriptions, and powerful analytics. This system operates alongside the existing JSON-RPC and REST APIs, specifically handling the new AgentExtension functionality.

## Architecture Components

### 1. Core Schema (`/src/a2a_registry/graphql/schema.graphql`)

The GraphQL schema defines:
- **AgentExtension**: Core extension entity with versioning, security metadata, and analytics
- **Extension Types**: authentication, schema, ml_model, business_rule, protocol_adapter, integration
- **Trust Levels**: community, verified, official, deprecated
- **Relationships**: Agent-Extension associations with usage tracking
- **Analytics**: Usage statistics, popularity metrics, compatibility reports

### 2. Type System (`/src/a2a_registry/graphql/types.py`)

Python type definitions using Strawberry GraphQL:
- **Enums**: ExtensionType, TrustLevel, ValidationStatus, SecurityScanResult
- **Core Types**: AgentExtension, ExtensionContent, ExtensionDependency
- **Relationships**: AgentExtensionRelation with usage tracking
- **Analytics**: UsageStatistics, ExtensionAnalytics, SecurityScan
- **Input Types**: Search, sorting, and mutation inputs
- **Connection Types**: Cursor-based pagination support

### 3. Resolvers (`/src/a2a_registry/graphql/resolvers.py`)

GraphQL resolvers implementing:
- **Query Resolvers**: Extension search, analytics, dependency resolution
- **Mutation Resolvers**: CRUD operations with validation and security
- **Field Resolvers**: Lazy-loaded relationships using DataLoaders
- **Authorization**: Field-level security with role-based permissions
- **Audit Logging**: Security event tracking for compliance

### 4. Security System (`/src/a2a_registry/graphql/security.py`)

Comprehensive security implementation:
- **Authentication**: JWT token validation with role extraction
- **Authorization**: Field-level permissions and resource-based access control
- **Rate Limiting**: Per-user and per-IP request throttling
- **Query Analysis**: Complexity and depth limiting to prevent DoS
- **Input Validation**: Content sanitization and security scanning
- **Audit Trail**: Complete action logging for security monitoring

### 5. Performance Optimization (`/src/a2a_registry/graphql/dataloaders.py`)

DataLoader implementations preventing N+1 queries:
- **ExtensionDataLoader**: Batch loading of extensions
- **DependencyDataLoader**: Batch dependency resolution
- **UsageStatsDataLoader**: Analytics data batching
- **SecurityScanDataLoader**: Security scan result batching
- **Caching**: Field-level and query-level caching strategies

### 6. Storage Backend (`/src/a2a_registry/graphql/storage.py`)

Abstract storage interface with in-memory implementation:
- **ExtensionStorageBackend**: Abstract interface for data persistence
- **InMemoryExtensionStorage**: Development/testing implementation
- **Batch Operations**: Optimized multi-record operations
- **Relationship Management**: Agent-Extension association tracking
- **Search Capabilities**: Full-text search and multi-criteria filtering

### 7. Supporting Services (`/src/a2a_registry/graphql/services.py`)

Business logic services:
- **AnalyticsService**: Usage statistics and popularity calculations
- **SecurityService**: Extension scanning and vulnerability detection
- **DependencyResolverService**: Dependency tree resolution with conflict detection
- **RecommendationService**: AI-driven extension recommendations
- **ValidationService**: Pre-publication validation and compliance checking

## Key Features

### Advanced Query Capabilities

1. **Multi-Dimensional Search**
   - Full-text search across names, descriptions, and tags
   - Type-based filtering (authentication, ML models, etc.)
   - Trust level filtering (community, verified, official)
   - Date range and popularity filtering
   - Dependency-based queries

2. **Relationship Queries**
   - Agent-Extension associations with usage tracking
   - Dependency tree resolution with conflict detection
   - Compatibility matrix queries
   - Cross-reference analysis

3. **Analytics and Metrics**
   - Real-time usage statistics
   - Popularity rankings and trends
   - Download and installation metrics
   - Security scan results and vulnerability tracking

### Security and Compliance

1. **Authentication and Authorization**
   - JWT-based authentication with role extraction
   - Field-level authorization (read/write/admin permissions)
   - Resource-based access control (own vs. others' extensions)
   - Anonymous access to public data only

2. **Security Scanning**
   - Automated security scans for published extensions
   - Vulnerability database integration
   - Signature verification for trusted extensions
   - Content validation and sanitization

3. **Audit and Compliance**
   - Complete audit trail for all mutations
   - Security event logging
   - Access pattern monitoring
   - GDPR-compliant data handling

### Performance and Scalability

1. **Query Optimization**
   - DataLoader pattern prevents N+1 queries
   - Field-level caching with TTL
   - Query complexity analysis and limiting
   - Cursor-based pagination for large datasets

2. **Rate Limiting and DoS Protection**
   - Per-user rate limiting (1000 req/min authenticated)
   - IP-based limiting for anonymous users
   - Query depth and complexity limits
   - Expensive operation throttling

3. **Caching Strategy**
   - Query-level caching for analytics
   - Field-level caching for expensive operations
   - Redis integration for distributed caching
   - Cache invalidation on data updates

### Real-Time Features

1. **GraphQL Subscriptions**
   - Extension update notifications
   - Security alert broadcasts
   - Real-time usage metrics
   - Agent-extension relationship changes

2. **WebSocket Support**
   - Persistent connections for subscriptions
   - Event filtering and routing
   - Connection lifecycle management
   - Authentication for subscription channels

## Integration with Existing System

### Coexistence with JSON-RPC and REST

The GraphQL API operates alongside existing protocols:
- **JSON-RPC**: Primary A2A protocol transport (unchanged)
- **REST**: Convenience API for basic operations (unchanged)  
- **GraphQL**: Advanced querying for AgentExtension system (new)

### Data Model Integration

- **AgentCard**: Integrated from existing fasta2a schema
- **Extension Storage**: New storage backend for AgentExtensions
- **Shared Services**: Common utilities and logging
- **Unified Configuration**: Environment-based configuration

### API Endpoints

- **GraphQL Endpoint**: `POST /graphql`
- **GraphQL Playground**: `GET /graphql` (development)
- **WebSocket Subscriptions**: `WS /graphql/ws`
- **Health Check**: `GET /graphql/health`
- **Performance Metrics**: `GET /graphql/metrics`

## Security Model

### Permission System

```
Roles and Permissions:
- user: Read-only access to public extensions
- developer: Create/update own extensions, read all
- publisher: Publish extensions, advanced features
- admin: Full access including trust level management

Field-Level Security:
- extension.content: Requires read permission
- extension.signature: Admin only
- extension.validationStatus: Publisher or admin
- analytics: Authenticated users only
```

### Query Complexity Analysis

```
Complexity Scoring:
- Basic field: 1 point
- Relationship field: 10 points  
- Search operation: 50 points
- Analytics query: 100 points
- Dependency resolution: 30 points

Limits:
- Anonymous users: 100 points max
- Authenticated users: 1000 points max
- Max query depth: 15 levels
```

### Rate Limiting

```
Rate Limits:
- Anonymous: 100 requests/minute
- Authenticated: 1000 requests/minute
- Premium: 5000 requests/minute
- Admin: Unlimited

Special Limits:
- Analytics queries: 10/minute
- Search operations: 60/minute
- Mutations: 100/minute
```

## Development and Testing

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Start server with GraphQL
a2a-registry serve --reload

# Access GraphQL Playground
open http://localhost:8000/graphql
```

### Testing Queries

Use the GraphQL Playground at `/graphql` to:
- Explore the schema documentation
- Test queries and mutations interactively
- Debug subscription connections
- Analyze query performance

### Example Development Workflow

1. **Schema Design**: Update `schema.graphql` with new types
2. **Python Types**: Update `types.py` with Strawberry definitions
3. **Resolvers**: Implement business logic in `resolvers.py`
4. **Storage**: Add storage methods in `storage.py`
5. **Testing**: Use Playground to test queries
6. **Security**: Add authorization checks
7. **Performance**: Profile with DataLoaders

## Production Deployment

### Environment Configuration

```bash
# GraphQL Configuration
GRAPHQL_SUBSCRIPTIONS=true
GRAPHQL_PLAYGROUND=false  # Disable in production
GRAPHQL_INTROSPECTION=false  # Disable in production
GRAPHQL_DEPTH_LIMIT=10
GRAPHQL_COMPLEXITY_LIMIT=500
GRAPHQL_RATE_LIMIT=1000

# Security Configuration  
JWT_SECRET=your-production-secret
REDIS_URL=redis://localhost:6379

# Storage Configuration
STORAGE_TYPE=postgresql  # Use production database
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Performance Monitoring

- **Query Performance**: Track execution times and complexity
- **Cache Hit Rates**: Monitor caching effectiveness
- **Error Rates**: Track authentication and authorization failures
- **Rate Limit Violations**: Monitor abuse patterns
- **Resource Usage**: CPU, memory, and database load

### Security Considerations

1. **Production Security**
   - Disable GraphQL Playground and introspection
   - Use strong JWT secrets with rotation
   - Implement proper HTTPS/TLS
   - Rate limiting and DDoS protection

2. **Data Protection**
   - Encrypt sensitive extension content
   - Audit log retention and rotation
   - GDPR compliance for user data
   - Backup and disaster recovery

3. **Monitoring and Alerting**
   - Security scan failures
   - Unusual query patterns
   - Rate limit violations
   - Performance degradation

## Future Enhancements

### Planned Features

1. **Federation Support**
   - Apollo Federation compatibility
   - Multi-service graph composition
   - Cross-service relationships

2. **Advanced Analytics**
   - Machine learning recommendations
   - Usage pattern analysis
   - Predictive security scanning

3. **Enterprise Features**
   - Private extension registries
   - Organization-level permissions
   - Custom validation rules
   - SLA monitoring

### Scalability Improvements

1. **Database Integration**
   - PostgreSQL backend implementation
   - Database query optimization
   - Connection pooling and clustering

2. **Caching Enhancements**
   - Redis cluster support
   - Distributed cache invalidation
   - Edge caching integration

3. **Performance Optimization**
   - Query batching and merging
   - Automatic persisted queries
   - CDN integration for static content

This GraphQL architecture provides a powerful, secure, and scalable foundation for the AgentExtension system while maintaining compatibility with existing A2A Registry functionality.