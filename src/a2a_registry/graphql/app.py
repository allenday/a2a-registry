"""GraphQL application integration with FastAPI."""

import json
import logging
import time
from typing import Any

from fastapi import FastAPI, Request, WebSocket
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from .schema import GraphQLContextManager, PerformanceMonitor, QueryValidator, schema
from .services import AnalyticsService, RecommendationService, SecurityService
from .storage import ExtensionStorageBackend

logger = logging.getLogger(__name__)


class GraphQLApp:
    """GraphQL application wrapper for A2A Registry."""

    def __init__(
        self,
        extension_storage: ExtensionStorageBackend,
        agent_storage: Any,
        enable_subscriptions: bool = True,
        enable_playground: bool = True,
        debug: bool = False,
    ) -> None:
        self.extension_storage = extension_storage
        self.agent_storage = agent_storage
        self.enable_subscriptions = enable_subscriptions
        self.enable_playground = enable_playground
        self.debug = debug

        # Initialize services
        self.analytics_service = AnalyticsService(extension_storage)
        self.security_service = SecurityService()
        self.recommendation_service = RecommendationService(extension_storage)

        # Initialize GraphQL components
        self.context_manager = GraphQLContextManager(
            extension_storage=extension_storage,
            agent_storage=agent_storage,
            analytics_service=self.analytics_service,
            security_service=self.security_service,
        )

        self.query_validator = QueryValidator()
        self.performance_monitor = PerformanceMonitor()

        # Create GraphQL router
        self.router = self._create_router()

    def _create_router(self) -> GraphQLRouter:
        """Create Strawberry GraphQL router."""

        async def get_context(request: Request) -> dict[str, Any]:
            """Context factory for GraphQL requests."""

            # Extract query from request
            query = ""
            if request.method == "POST":
                try:
                    body = await request.body()
                    data = json.loads(body)
                    query = data.get("query", "")
                except Exception:
                    pass

            return await self.context_manager.create_context(request, query)

        async def process_result(
            result: Any, context: dict[str, Any], request: Request
        ) -> Any:
            """Process GraphQL result and add monitoring."""

            # Record performance metrics
            execution_time = getattr(context, "_execution_time", 0)
            security_context = context.get("security_context")

            if hasattr(context, "_query") and security_context:
                await self.performance_monitor.record_query_metrics(
                    context["_query"],
                    execution_time,
                    context.get("_field_count", 0),
                    security_context,
                )

            return result

        return GraphQLRouter(
            schema,
            context_getter=get_context,  # type: ignore
            graphiql=self.enable_playground,
            subscription_protocols=(
                [
                    GRAPHQL_TRANSPORT_WS_PROTOCOL,
                    GRAPHQL_WS_PROTOCOL,
                ]
                if self.enable_subscriptions
                else []
            ),
        )

    async def handle_websocket(self, websocket: WebSocket) -> None:
        """Handle WebSocket connections for subscriptions."""

        if not self.enable_subscriptions:
            await websocket.close(code=1003, reason="Subscriptions not enabled")
            return

        await websocket.accept()

        try:
            # Create context for WebSocket
            context = await self.context_manager.create_context(websocket, "")

            # Handle subscription lifecycle
            async for message in websocket.iter_text():
                try:
                    data = json.loads(message)

                    if data.get("type") == "connection_init":
                        await websocket.send_text(
                            json.dumps({"type": "connection_ack"})
                        )

                    elif data.get("type") == "start":
                        # Process subscription
                        query = data.get("payload", {}).get("query", "")

                        # Validate subscription query
                        validation_result = self.query_validator.validate_query(
                            query, context["security_context"]
                        )

                        if not validation_result["valid"]:
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "payload": validation_result["errors"],
                                    }
                                )
                            )
                            continue

                        # Execute subscription (simplified)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "data",
                                    "payload": {
                                        "data": {"message": "Subscription started"}
                                    },
                                }
                            )
                        )

                except json.JSONDecodeError:
                    await websocket.send_text(
                        json.dumps({"type": "error", "payload": ["Invalid JSON"]})
                    )

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await websocket.close()

    def add_to_app(self, app: FastAPI, path: str = "/graphql") -> None:
        """Add GraphQL router to FastAPI application."""

        # Add HTTP GraphQL endpoint
        app.include_router(self.router, prefix=path)

        # Add WebSocket endpoint for subscriptions
        if self.enable_subscriptions:

            @app.websocket(f"{path}/ws")
            async def websocket_endpoint(websocket: WebSocket) -> None:
                await self.handle_websocket(websocket)

        # Add GraphQL performance metrics endpoint
        @app.get(f"{path}/metrics")
        async def graphql_metrics() -> dict[str, Any]:
            """Get GraphQL performance metrics."""
            return self.performance_monitor.get_performance_stats()

        # Add GraphQL health check
        @app.get(f"{path}/health")
        async def graphql_health() -> dict[str, Any]:
            """GraphQL health check endpoint."""
            return {
                "status": "healthy",
                "service": "GraphQL API",
                "subscriptions_enabled": self.enable_subscriptions,
                "playground_enabled": self.enable_playground,
            }


def create_graphql_app(
    extension_storage: ExtensionStorageBackend, agent_storage: Any, **kwargs: Any
) -> GraphQLApp:
    """Factory function to create GraphQL application."""

    return GraphQLApp(
        extension_storage=extension_storage, agent_storage=agent_storage, **kwargs
    )


# Middleware for request preprocessing
class GraphQLMiddleware(BaseHTTPMiddleware):
    """Middleware for GraphQL request processing."""

    async def dispatch(self, request: StarletteRequest, call_next: Any) -> Response:
        """Process GraphQL requests with timing."""

        if request.url.path.startswith("/graphql"):
            # Add request timing
            start_time = time.time()
            response = await call_next(request)
            execution_time = time.time() - start_time
            response.headers["x-graphql-execution-time"] = f"{execution_time:.3f}"
            return response  # type: ignore

        return await call_next(request)  # type: ignore


# Error handlers
async def graphql_error_handler(request: Request, exc: Exception) -> Response:
    """Handle GraphQL-specific errors."""
    from starlette.responses import JSONResponse

    logger.error(f"GraphQL error: {exc}")

    if isinstance(exc, ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    elif isinstance(exc, PermissionError):
        return JSONResponse(status_code=403, content={"detail": "Access denied"})
    else:
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )


# Configuration
class GraphQLConfig:
    """Configuration for GraphQL setup."""

    def __init__(self) -> None:
        self.enable_subscriptions = True
        self.enable_playground = True
        self.enable_introspection = True
        self.query_depth_limit = 15
        self.query_complexity_limit = 1000
        self.rate_limit_per_minute = 1000
        self.jwt_secret = "your-jwt-secret"
        self.debug = False

    @classmethod
    def from_env(cls) -> "GraphQLConfig":
        """Create configuration from environment variables."""
        import os

        config = cls()
        config.enable_subscriptions = (
            os.getenv("GRAPHQL_SUBSCRIPTIONS", "true").lower() == "true"
        )
        config.enable_playground = (
            os.getenv("GRAPHQL_PLAYGROUND", "true").lower() == "true"
        )
        config.enable_introspection = (
            os.getenv("GRAPHQL_INTROSPECTION", "true").lower() == "true"
        )
        config.query_depth_limit = int(os.getenv("GRAPHQL_DEPTH_LIMIT", "15"))
        config.query_complexity_limit = int(
            os.getenv("GRAPHQL_COMPLEXITY_LIMIT", "1000")
        )
        config.rate_limit_per_minute = int(os.getenv("GRAPHQL_RATE_LIMIT", "1000"))
        config.jwt_secret = os.getenv("JWT_SECRET", "your-jwt-secret")
        config.debug = os.getenv("DEBUG", "false").lower() == "true"

        return config


# Example usage and integration
def setup_graphql_with_fastapi(
    app: FastAPI, extension_storage: Any, agent_storage: Any
) -> GraphQLApp:
    """Set up GraphQL with FastAPI application."""

    # Load configuration
    config = GraphQLConfig.from_env()

    # Create GraphQL app
    graphql_app = create_graphql_app(
        extension_storage=extension_storage,
        agent_storage=agent_storage,
        enable_subscriptions=config.enable_subscriptions,
        enable_playground=config.enable_playground,
        debug=config.debug,
    )

    # Add to FastAPI
    graphql_app.add_to_app(app, path="/graphql")

    # Add middleware
    app.add_middleware(GraphQLMiddleware)

    # Add error handlers
    app.add_exception_handler(ValueError, graphql_error_handler)
    app.add_exception_handler(PermissionError, graphql_error_handler)

    logger.info("GraphQL API configured successfully")
    logger.info("GraphQL endpoint: /graphql")
    logger.info(
        f"GraphQL playground: {'enabled' if config.enable_playground else 'disabled'}"
    )
    logger.info(
        f"GraphQL subscriptions: {'enabled' if config.enable_subscriptions else 'disabled'}"
    )

    return graphql_app
