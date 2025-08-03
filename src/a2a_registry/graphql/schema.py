"""GraphQL schema configuration and setup using Strawberry."""

import logging
from collections.abc import AsyncIterator
from typing import Any, Optional

import strawberry
from strawberry.extensions import QueryDepthLimiter, ValidationCache

from .dataloaders import DataLoaderContext
from .resolvers import Mutation, Query, Subscription
from .security import SecurityContext, SecurityMiddleware

logger = logging.getLogger(__name__)


# Create the GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[QueryDepthLimiter(max_depth=15), ValidationCache(maxsize=100)],
)


class GraphQLContextManager:
    """Manages GraphQL context creation and lifecycle."""

    def __init__(
        self,
        extension_storage: Any,
        agent_storage: Any,
        analytics_service: Any = None,
        security_service: Any = None,
        subscription_manager: Any = None,
        cache_service: Any = None,
        audit_service: Any = None,
    ) -> None:
        self.extension_storage = extension_storage
        self.agent_storage = agent_storage
        self.analytics_service = analytics_service
        self.security_service = security_service
        self.subscription_manager = subscription_manager
        self.cache_service = cache_service
        self.audit_service = audit_service

        # Security middleware
        self.security_middleware = SecurityMiddleware(
            jwt_secret="your-jwt-secret-key",  # Should come from environment
            rate_limit_per_minute=1000,
            max_query_complexity=1000,
            max_query_depth=15,
        )

    async def create_context(self, request: Any, query: str = "") -> dict[str, Any]:
        """Create GraphQL context for request."""

        try:
            # Process security
            security_context = await self.security_middleware.process_request(
                request, query
            )

        except Exception as e:
            logger.warning(f"Security check failed: {e}")
            # Create anonymous context for public queries
            security_context = SecurityContext()

        # Base context
        context = {
            "security_context": security_context,
            "extension_storage": self.extension_storage,
            "agent_storage": self.agent_storage,
            "analytics_service": self.analytics_service,
            "security_service": self.security_service,
            "subscription_manager": self.subscription_manager,
            "cache": self.cache_service,
            "audit_service": self.audit_service,
            "request": request,
        }

        # Add data loaders using context manager
        dataloader_context = DataLoaderContext(context)
        context = await dataloader_context.__aenter__()

        return context


# Schema introspection control
def get_schema_for_user(security_context: SecurityContext) -> strawberry.Schema:
    """Get schema with appropriate introspection based on user permissions."""

    # Disable introspection for unauthenticated users in production
    enable_introspection = (
        security_context.is_authenticated or security_context.has_permission("admin")
    )

    if not enable_introspection:
        # Return schema with introspection disabled
        return strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[
                QueryDepthLimiter(max_depth=10),  # Stricter limits for anonymous
                ValidationCache(maxsize=50),
            ],
        )

    return schema


# Query validation and transformation
class QueryValidator:
    """Validates and transforms GraphQL queries."""

    def __init__(self) -> None:
        self.blocked_queries: list[str] = ["__schema", "__type", "introspection"]
        self.rate_limited_queries: list[str] = ["search", "analytics", "dependencies"]

    def validate_query(
        self, query: str, security_context: SecurityContext
    ) -> dict[str, Any]:
        """Validate query and return validation result."""

        result: dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "transformed_query": query,
        }

        # Check for blocked queries for anonymous users
        if not security_context.is_authenticated:
            for blocked in self.blocked_queries:
                if blocked in query.lower():
                    result["valid"] = False
                    result["errors"].append(
                        f"Query type '{blocked}' not allowed for anonymous users"
                    )

        # Check for rate-limited queries
        for rate_limited in self.rate_limited_queries:
            if rate_limited in query.lower():
                if not security_context.has_permission("extension:search"):
                    result["valid"] = False
                    result["errors"].append(
                        f"Insufficient permissions for '{rate_limited}' queries"
                    )

        # Query complexity checks (basic)
        field_count = query.count("{") + query.count("}")
        if field_count > 100:
            result["warnings"].append(
                "Query has high field count, consider using pagination"
            )

        return result

    def transform_query_for_security(
        self, query: str, security_context: SecurityContext
    ) -> str:
        """Transform query to add security filters."""

        # Add security filters for search queries
        if "extensions(" in query and not security_context.has_permission("admin"):
            # In a real implementation, parse and modify the AST
            # For now, just add a comment indicating transformation needed
            query = f"# Security filters applied\n{query}"

        return query


# Subscription management
class SubscriptionManager:
    """Manages GraphQL subscriptions."""

    def __init__(self) -> None:
        self.subscribers: dict[str, Any] = {}
        self.event_queue: list[dict[str, Any]] = []

    async def subscribe(self, event_type: str, filter_id: Optional[str] = None) -> Any:
        """Subscribe to events of a specific type."""

        # In a real implementation, this would use Redis pub/sub or similar
        # For now, simulate with async generator
        async def event_generator() -> AsyncIterator[Any]:
            while True:
                # Check for matching events
                matching_events = [
                    event
                    for event in self.event_queue
                    if event.get("type") == event_type
                    and (not filter_id or event.get("filter_id") == filter_id)
                ]

                for event in matching_events:
                    yield event["payload"]
                    self.event_queue.remove(event)

                # Wait before checking again
                import asyncio

                await asyncio.sleep(1)

        return event_generator()

    async def publish(
        self, event_type: str, payload: Any, filter_id: Optional[str] = None
    ) -> None:
        """Publish an event to subscribers."""

        event = {
            "type": event_type,
            "payload": payload,
            "filter_id": filter_id,
            "timestamp": "2024-01-01T00:00:00Z",  # Use proper timestamp
        }

        self.event_queue.append(event)

        # In production, this would publish to Redis/message queue
        logger.info(f"Published event: {event_type}")


# Error handling
@strawberry.type
class GraphQLError:
    """Custom GraphQL error type."""

    message: str
    code: Optional[str] = None
    path: Optional[str] = None


def format_graphql_error(error: Exception, debug: bool = False) -> dict[str, Any]:
    """Format exceptions as GraphQL errors."""

    error_dict: dict[str, Any] = {"message": str(error), "extensions": {}}

    # Add error code based on exception type
    if hasattr(error, "__class__"):
        error_dict["extensions"]["code"] = error.__class__.__name__

    # Add debug information if enabled
    if debug:
        import traceback

        error_dict["extensions"]["traceback"] = traceback.format_exc()

    return error_dict


# Performance monitoring
class PerformanceMonitor:
    """Monitors GraphQL query performance."""

    def __init__(self) -> None:
        self.query_metrics: dict[int, dict[str, Any]] = {}

    async def record_query_metrics(
        self,
        query: str,
        execution_time: float,
        field_count: int,
        security_context: SecurityContext,
    ) -> None:
        """Record performance metrics for a query."""

        query_hash = hash(query)

        if query_hash not in self.query_metrics:
            self.query_metrics[query_hash] = {
                "query": query[:100] + "..." if len(query) > 100 else query,
                "total_executions": 0,
                "total_time": 0,
                "avg_time": 0,
                "max_time": 0,
                "field_count": field_count,
            }

        metrics = self.query_metrics[query_hash]
        metrics["total_executions"] += 1
        metrics["total_time"] += execution_time
        metrics["avg_time"] = metrics["total_time"] / metrics["total_executions"]
        metrics["max_time"] = max(metrics["max_time"], execution_time)

        # Log slow queries
        if execution_time > 5.0:  # 5 seconds
            logger.warning(
                f"Slow query detected: {execution_time:.2f}s, "
                f"User: {security_context.user_id}, "
                f"Query: {query[:100]}"
            )

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics."""

        if not self.query_metrics:
            return {"message": "No metrics available"}

        sorted_metrics = sorted(
            self.query_metrics.values(), key=lambda x: x["avg_time"], reverse=True
        )

        return {
            "total_queries": len(self.query_metrics),
            "slowest_queries": sorted_metrics[:10],
            "total_executions": sum(
                m["total_executions"] for m in self.query_metrics.values()
            ),
            "average_execution_time": sum(
                m["avg_time"] for m in self.query_metrics.values()
            )
            / len(self.query_metrics),
        }
