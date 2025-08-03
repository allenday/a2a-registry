"""A2A Registry server using FastAPI and FastA2A schemas with dual transport support."""

import logging
from typing import Any, Optional
from urllib.parse import unquote

from fasta2a.schema import AgentCard  # type: ignore
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from jsonrpcserver import async_dispatch
from pydantic import BaseModel

# Import JSON-RPC methods to register them with the dispatcher
# This import is needed for side effects - it registers the @method decorated functions
from . import (
    __version__,
    jsonrpc_server,  # noqa: F401
)
from .config import config
from .storage import storage

GRAPHQL_AVAILABLE = False

logger = logging.getLogger(__name__)


class RegisterAgentRequest(BaseModel):
    """Request to register an agent."""

    agent_card: dict[str, Any]


class AgentSearchRequest(BaseModel):
    """Request to search for agents."""

    query: str


def create_app() -> FastAPI:
    """Create FastAPI application for A2A Registry."""
    app = FastAPI(
        title="A2A Registry",
        description="Agent-to-Agent Registry Service with GraphQL",
        version=__version__,
    )

    # Try to initialize GraphQL extension storage and setup GraphQL API if available
    try:
        from .graphql.app import setup_graphql_with_fastapi
        from .graphql.storage import InMemoryExtensionStorage

        extension_storage = InMemoryExtensionStorage()
        setup_graphql_with_fastapi(app, extension_storage, storage)
        GRAPHQL_AVAILABLE = True
        logger.info("GraphQL support enabled")
    except Exception as e:
        logger.info(f"GraphQL support disabled - only REST API available: {e}")
        GRAPHQL_AVAILABLE = False

    @app.post("/agents", response_model=dict[str, Any])
    async def register_agent(request: RegisterAgentRequest) -> dict[str, Any]:
        """Register an agent in the registry."""
        try:
            # AgentCard is a TypedDict, so we can use the dict directly
            # but we should validate required fields
            agent_card_dict = request.agent_card

            # Validate required fields for AgentCard
            required_fields = [
                "name",
                "description",
                "url",
                "version",
                "protocol_version",
            ]
            for field in required_fields:
                if field not in agent_card_dict:
                    raise ValueError(f"Missing required field: {field}")

            # Set default transport to JSONRPC per A2A specification
            if "preferred_transport" not in agent_card_dict:
                agent_card_dict["preferred_transport"] = "JSONRPC"

            # Cast to AgentCard type for type safety
            agent_card: AgentCard = agent_card_dict  # type: ignore
            success = await storage.register_agent(agent_card)

            if success:
                # Extract and update agent extensions
                agent_id = agent_card["name"]
                extensions = []

                # Get extensions from agent card capabilities
                capabilities = agent_card.get("capabilities", {})
                if isinstance(capabilities, dict):
                    agent_extensions = capabilities.get("extensions", [])
                    if isinstance(agent_extensions, list):
                        extensions = [
                            {
                                "uri": ext.get("uri", ""),
                                "description": ext.get("description", ""),
                                "required": ext.get("required", False),
                                "params": ext.get("params", {}),
                            }
                            for ext in agent_extensions
                            if isinstance(ext, dict) and ext.get("uri")
                        ]

                # Update agent extensions in storage
                await storage.update_agent_extensions(agent_id, extensions)

                return {
                    "success": True,
                    "agent_id": agent_id,
                    "message": "Agent registered successfully",
                    "extensions_processed": len(extensions),
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to register agent")

        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.get("/agents/{agent_id}", response_model=dict[str, Any])
    async def get_agent(agent_id: str) -> dict[str, Any]:
        """Get an agent by ID."""
        agent_card = await storage.get_agent(agent_id)
        if agent_card:
            return {"agent_card": dict(agent_card)}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")

    @app.get("/agents", response_model=dict[str, Any])
    async def list_agents() -> dict[str, Any]:
        """List all registered agents."""
        agents = await storage.list_agents()
        return {"agents": [dict(agent) for agent in agents], "count": len(agents)}

    @app.delete("/agents/{agent_id}", response_model=dict[str, Any])
    async def unregister_agent(agent_id: str) -> dict[str, Any]:
        """Unregister an agent."""
        # First remove agent from extensions
        extensions_removed = await storage.remove_agent_from_extensions(agent_id)

        # Then remove the agent
        success = await storage.unregister_agent(agent_id)
        if success:
            return {
                "success": True,
                "message": "Agent unregistered successfully",
                "extensions_cleaned": extensions_removed,
            }
        else:
            raise HTTPException(status_code=404, detail="Agent not found")

    @app.post("/agents/search", response_model=dict[str, Any])
    async def search_agents(request: AgentSearchRequest) -> dict[str, Any]:
        """Search for agents."""
        agents = await storage.search_agents(request.query)
        return {
            "agents": [dict(agent) for agent in agents],
            "count": len(agents),
            "query": request.query,
        }

    # Extension discovery endpoints
    @app.get("/extensions", response_model=dict[str, Any])
    async def list_extensions(
        uri_pattern: Optional[str] = Query(
            None, description="Filter extensions by URI pattern"
        ),
        declaring_agents: Optional[list[str]] = Query(
            None, description="Filter by declaring agents"
        ),
        trust_levels: Optional[list[str]] = Query(
            None, description="Filter by trust levels"
        ),
        page_size: int = Query(
            100, description="Number of extensions per page", ge=1, le=1000
        ),
        page_token: Optional[str] = Query(
            None, description="Page token for pagination"
        ),
    ) -> dict[str, Any]:
        """List all extensions with provenance information."""
        try:
            extensions, next_page_token, total_count = await storage.list_extensions(
                uri_pattern=uri_pattern,
                declaring_agents=declaring_agents,
                trust_levels=trust_levels,
                page_size=page_size,
                page_token=page_token,
            )

            return {
                "extensions": [ext.to_dict() for ext in extensions],
                "count": len(extensions),
                "total_count": total_count,
                "next_page_token": next_page_token,
                "dev_mode": config.dev_mode,
            }
        except Exception as e:
            logger.error(f"Error listing extensions: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/extensions/{uri:path}", response_model=dict[str, Any])
    async def get_extension_info(uri: str) -> dict[str, Any]:
        """Get specific extension information by URI."""
        try:
            # URL decode the URI
            decoded_uri = unquote(uri)
            extension_info = await storage.get_extension(decoded_uri)

            if extension_info:
                return {
                    "extension_info": extension_info.to_dict(),
                    "found": True,
                }
            else:
                raise HTTPException(status_code=404, detail="Extension not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting extension info for {uri}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/agents/{agent_id}/extensions", response_model=dict[str, Any])
    async def get_agent_extensions(agent_id: str) -> dict[str, Any]:
        """Get all extensions used by a specific agent."""
        try:
            # Verify agent exists
            agent_card = await storage.get_agent(agent_id)
            if not agent_card:
                raise HTTPException(status_code=404, detail="Agent not found")

            extensions = await storage.get_agent_extensions(agent_id)

            return {
                "agent_id": agent_id,
                "extensions": [ext.to_dict() for ext in extensions],
                "count": len(extensions),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting extensions for agent {agent_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "A2A Registry"}

    @app.post("/jsonrpc")
    async def jsonrpc_endpoint(request: Request) -> JSONResponse:
        """JSON-RPC endpoint - primary A2A protocol transport."""
        # Import here to avoid circular imports

        # Get request body
        data = await request.body()

        # Dispatch to JSON-RPC handlers
        response = await async_dispatch(data.decode())

        # The response from jsonrpcserver is a string, parse it to return proper JSON
        import json

        response_data = json.loads(response) if isinstance(response, str) else response

        return JSONResponse(content=response_data, media_type="application/json")

    @app.get("/")
    async def root() -> dict[str, Any]:
        """Root endpoint with service information."""
        protocols = {
            "primary": {
                "transport": "JSONRPC",
                "endpoint": "/jsonrpc",
                "description": "JSON-RPC 2.0 endpoint (A2A default)",
            },
            "secondary": {
                "transport": "HTTP+JSON",
                "endpoints": {
                    "register": "POST /agents",
                    "get": "GET /agents/{id}",
                    "list": "GET /agents",
                    "search": "POST /agents/search",
                    "unregister": "DELETE /agents/{id}",
                    "list_extensions": "GET /extensions",
                    "get_extension": "GET /extensions/{uri}",
                    "agent_extensions": "GET /agents/{id}/extensions",
                },
                "description": "REST API endpoints (convenience)",
            },
        }

        if GRAPHQL_AVAILABLE:
            protocols["graphql"] = {
                "transport": "GraphQL",
                "endpoint": "/graphql",
                "playground": "/graphql",
                "websocket": "/graphql/ws",
                "description": "GraphQL API for AgentExtension system with advanced querying, subscriptions, and analytics",
            }

        return {
            "service": "A2A Registry",
            "version": __version__,
            "description": "Agent-to-Agent Registry Service with dual transport support"
            + (" + GraphQL" if GRAPHQL_AVAILABLE else ""),
            "protocols": protocols,
            "mode": {
                "development": config.dev_mode,
                "extension_verification": config.require_extension_verification,
                "domain_verification": config.require_domain_verification,
                "signature_verification": config.require_signature_verification,
            },
            "health_check": "/health",
            "documentation": "/docs",
        }

    return app
