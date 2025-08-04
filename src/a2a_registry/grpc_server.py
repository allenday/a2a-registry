"""gRPC server implementation for A2A Registry with vector search capabilities."""

import logging
from typing import Any

import grpc
import grpc.aio
from google.protobuf import empty_pb2, timestamp_pb2

from .proto.generated import a2a_pb2, registry_pb2, registry_pb2_grpc
from .storage import storage

logger = logging.getLogger(__name__)


class A2ARegistryServicer(registry_pb2_grpc.A2ARegistryServiceServicer):
    """gRPC servicer implementation for A2A Registry Service."""

    def __init__(self) -> None:
        """Initialize the servicer."""
        self.storage = storage

    def _convert_agent_card_to_registry_card(
        self, agent_card: dict, include_vectors: bool = False
    ) -> registry_pb2.RegistryAgentCard:
        """Convert AgentCard dict to RegistryAgentCard proto."""
        # Create registry metadata
        registry_metadata = registry_pb2.RegistryMetadata(
            registered_at=timestamp_pb2.Timestamp(),
            last_updated=timestamp_pb2.Timestamp(),
            domain_verified=False,
            signature_verified=False,
            trust_level=registry_pb2.TRUST_LEVEL_UNVERIFIED,
        )

        # Create the registry agent card
        registry_card = registry_pb2.RegistryAgentCard(
            agent_card=agent_card,  # This will be converted by protobuf
            registry_metadata=registry_metadata,
        )

        # Add vectors if requested (placeholder for now)
        if include_vectors:
            # TODO: Implement vector generation and storage
            pass

        return registry_card

    def _convert_extension_info_to_proto(
        self, extension_info: Any
    ) -> registry_pb2.ExtensionInfo:
        """Convert ExtensionInfo to proto ExtensionInfo."""
        # Convert datetime to timestamp
        first_declared_at = timestamp_pb2.Timestamp()
        if extension_info.first_declared_at:
            first_declared_at.FromDatetime(extension_info.first_declared_at)

        # Convert trust level string to enum
        trust_level = registry_pb2.TRUST_LEVEL_UNVERIFIED
        if extension_info.trust_level == "TRUST_LEVEL_VERIFIED":
            trust_level = registry_pb2.TRUST_LEVEL_VERIFIED
        elif extension_info.trust_level == "TRUST_LEVEL_COMMUNITY":
            trust_level = registry_pb2.TRUST_LEVEL_COMMUNITY
        elif extension_info.trust_level == "TRUST_LEVEL_OFFICIAL":
            trust_level = registry_pb2.TRUST_LEVEL_OFFICIAL

        return registry_pb2.ExtensionInfo(
            extension=a2a_pb2.AgentExtension(
                uri=extension_info.uri,
                description=extension_info.description,
                required=extension_info.required,
                params=extension_info.params,
            ),
            first_declared_by_agent=extension_info.first_declared_by_agent,
            first_declared_at=first_declared_at,
            trust_level=trust_level,
            declaring_agents=list(extension_info.declaring_agents),
            usage_count=extension_info.usage_count,
        )

    async def GetAgentCard(
        self,
        request: registry_pb2.GetAgentCardRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.GetAgentCardResponse:
        """Get an agent card by ID."""
        try:
            agent_card = await self.storage.get_agent(request.agent_id)
            if agent_card:
                registry_card = self._convert_agent_card_to_registry_card(
                    agent_card, request.include_vectors
                )
                return registry_pb2.GetAgentCardResponse(
                    registry_agent_card=registry_card, found=True
                )
            else:
                return registry_pb2.GetAgentCardResponse(found=False)
        except Exception as e:
            logger.error(f"Error getting agent card: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.GetAgentCardResponse(found=False)

    async def StoreAgentCard(
        self,
        request: registry_pb2.StoreAgentCardRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.StoreAgentCardResponse:
        """Store an agent card in the registry."""
        try:
            # Convert proto agent card to dict
            agent_card_dict = request.registry_agent_card.agent_card

            # Register the agent
            success = await self.storage.register_agent(agent_card_dict)

            if success:
                # Update vectors if requested
                if request.update_vectors:
                    # TODO: Implement vector generation and storage
                    pass

                return registry_pb2.StoreAgentCardResponse(
                    success=True,
                    message="Agent registered successfully",
                    stored_card=request.registry_agent_card,
                )
            else:
                return registry_pb2.StoreAgentCardResponse(
                    success=False, message="Failed to register agent"
                )
        except Exception as e:
            logger.error(f"Error storing agent card: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.StoreAgentCardResponse(
                success=False, message=f"Internal error: {str(e)}"
            )

    async def SearchAgents(
        self,
        request: registry_pb2.SearchAgentsRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.SearchAgentsResponse:
        """Search for agents using various criteria."""
        try:
            criteria = request.criteria

            # Handle different search modes
            if criteria.search_mode == registry_pb2.SEARCH_MODE_VECTOR:
                # Vector search
                if criteria.semantic_query:
                    # TODO: Implement vector search
                    # For now, fall back to keyword search
                    agents = await self.storage.search_agents(criteria.semantic_query)
                elif criteria.query_vector:
                    # TODO: Implement vector search with pre-computed vector
                    agents = []
                else:
                    agents = []
            else:
                # Keyword search
                if criteria.semantic_query:
                    agents = await self.storage.search_agents(criteria.semantic_query)
                else:
                    # Basic search with other criteria
                    agents = await self.storage.list_agents()

            # Convert to registry cards
            registry_agents = []
            similarity_scores = []

            for agent in agents:
                registry_card = self._convert_agent_card_to_registry_card(agent)
                registry_agents.append(registry_card)

                # TODO: Calculate similarity scores for vector search
                if criteria.search_mode == registry_pb2.SEARCH_MODE_VECTOR:
                    similarity_scores.append(1.0)  # Placeholder

            return registry_pb2.SearchAgentsResponse(
                agents=registry_agents,
                next_page_token="",  # TODO: Implement pagination
                total_count=len(registry_agents),
                similarity_scores=similarity_scores,
            )
        except Exception as e:
            logger.error(f"Error searching agents: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.SearchAgentsResponse(
                agents=[], next_page_token="", total_count=0, similarity_scores=[]
            )

    async def DeleteAgentCard(
        self,
        request: registry_pb2.DeleteAgentCardRequest,
        context: grpc.aio.ServicerContext,
    ) -> empty_pb2.Empty:
        """Delete an agent card from the registry."""
        try:
            success = await self.storage.unregister_agent(request.agent_id)
            if success:
                return empty_pb2.Empty()
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Agent not found")
                return empty_pb2.Empty()
        except Exception as e:
            logger.error(f"Error deleting agent card: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return empty_pb2.Empty()

    async def ListAllAgents(
        self,
        request: registry_pb2.ListAllAgentsRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.ListAllAgentsResponse:
        """List all agents in the registry."""
        try:
            agents = await self.storage.list_agents()

            # Convert to registry cards
            registry_agents = []
            for agent in agents:
                registry_card = self._convert_agent_card_to_registry_card(
                    agent, request.include_vectors
                )
                registry_agents.append(registry_card)

            return registry_pb2.ListAllAgentsResponse(
                agents=registry_agents,
                next_page_token="",  # TODO: Implement pagination
                total_count=len(registry_agents),
            )
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.ListAllAgentsResponse(
                agents=[], next_page_token="", total_count=0
            )

    async def UpdateAgentStatus(
        self,
        request: registry_pb2.UpdateAgentStatusRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.UpdateAgentStatusResponse:
        """Update agent status."""
        try:
            # TODO: Implement status update
            # For now, just return success
            agent_card = await self.storage.get_agent(request.agent_id)
            if agent_card:
                registry_card = self._convert_agent_card_to_registry_card(agent_card)
                return registry_pb2.UpdateAgentStatusResponse(
                    success=True,
                    message="Status updated successfully",
                    updated_card=registry_card,
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Agent not found")
                return registry_pb2.UpdateAgentStatusResponse(
                    success=False, message="Agent not found"
                )
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.UpdateAgentStatusResponse(
                success=False, message=f"Internal error: {str(e)}"
            )

    async def GetExtensionInfo(
        self,
        request: registry_pb2.GetExtensionInfoRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.GetExtensionInfoResponse:
        """Get extension information."""
        try:
            extension_info = await self.storage.get_extension(request.uri)
            if extension_info:
                proto_extension = self._convert_extension_info_to_proto(extension_info)
                return registry_pb2.GetExtensionInfoResponse(
                    extension_info=proto_extension, found=True
                )
            else:
                return registry_pb2.GetExtensionInfoResponse(found=False)
        except Exception as e:
            logger.error(f"Error getting extension info: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.GetExtensionInfoResponse(found=False)

    async def ListExtensions(
        self,
        request: registry_pb2.ListExtensionsRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.ListExtensionsResponse:
        """List extensions with optional filtering."""
        try:
            # Convert trust levels from proto to strings
            trust_levels = []
            for level in request.trust_levels:
                if level == registry_pb2.TRUST_LEVEL_VERIFIED:
                    trust_levels.append("TRUST_LEVEL_VERIFIED")
                elif level == registry_pb2.TRUST_LEVEL_COMMUNITY:
                    trust_levels.append("TRUST_LEVEL_COMMUNITY")
                elif level == registry_pb2.TRUST_LEVEL_OFFICIAL:
                    trust_levels.append("TRUST_LEVEL_OFFICIAL")
                else:
                    trust_levels.append("TRUST_LEVEL_UNVERIFIED")

            extensions, next_token, total_count = await self.storage.list_extensions(
                uri_pattern=request.uri_pattern,
                declaring_agents=list(request.declaring_agents),
                trust_levels=trust_levels if trust_levels else None,
                page_size=request.page_size,
                page_token=request.page_token,
            )

            # Convert to proto extensions
            proto_extensions = []
            similarity_scores = []

            for ext in extensions:
                proto_ext = self._convert_extension_info_to_proto(ext)
                proto_extensions.append(proto_ext)

                # TODO: Calculate similarity scores for vector search
                if request.search_mode == registry_pb2.SEARCH_MODE_VECTOR:
                    similarity_scores.append(1.0)  # Placeholder

            return registry_pb2.ListExtensionsResponse(
                extensions=proto_extensions,
                next_page_token=next_token or "",
                total_count=total_count,
                similarity_scores=similarity_scores,
            )
        except Exception as e:
            logger.error(f"Error listing extensions: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.ListExtensionsResponse(
                extensions=[], next_page_token="", total_count=0, similarity_scores=[]
            )

    async def GetAgentExtensions(
        self,
        request: registry_pb2.GetAgentExtensionsRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.GetAgentExtensionsResponse:
        """Get extensions for a specific agent."""
        try:
            extensions = await self.storage.get_agent_extensions(request.agent_id)

            # Convert to proto extensions
            proto_extensions = []
            for ext in extensions:
                proto_ext = self._convert_extension_info_to_proto(ext)
                proto_extensions.append(proto_ext)

            return registry_pb2.GetAgentExtensionsResponse(
                extensions=proto_extensions, agent_id=request.agent_id
            )
        except Exception as e:
            logger.error(f"Error getting agent extensions: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.GetAgentExtensionsResponse(
                extensions=[], agent_id=request.agent_id
            )

    async def UpdateAgentVectors(
        self,
        request: registry_pb2.UpdateAgentVectorsRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.UpdateAgentVectorsResponse:
        """Update vectors for an agent."""
        try:
            # TODO: Implement vector storage
            # For now, just return success
            logger.info(f"Updating vectors for agent {request.agent_id}")
            return registry_pb2.UpdateAgentVectorsResponse(
                success=True, message="Vectors updated successfully"
            )
        except Exception as e:
            logger.error(f"Error updating agent vectors: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.UpdateAgentVectorsResponse(
                success=False, message=f"Internal error: {str(e)}"
            )

    async def PingAgent(
        self, request: registry_pb2.PingAgentRequest, context: grpc.aio.ServicerContext
    ) -> registry_pb2.PingAgentResponse:
        """Ping an agent to check if it's responsive."""
        try:
            # TODO: Implement actual ping logic
            # For now, just check if agent exists
            agent_card = await self.storage.get_agent(request.agent_id)

            if agent_card:
                return registry_pb2.PingAgentResponse(
                    responsive=True,
                    response_time_ms=0,  # Placeholder
                    status="available",
                    timestamp=timestamp_pb2.Timestamp(),
                )
            else:
                return registry_pb2.PingAgentResponse(
                    responsive=False,
                    response_time_ms=0,
                    status="not_found",
                    timestamp=timestamp_pb2.Timestamp(),
                )
        except Exception as e:
            logger.error(f"Error pinging agent: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return registry_pb2.PingAgentResponse(
                responsive=False,
                response_time_ms=0,
                status="error",
                timestamp=timestamp_pb2.Timestamp(),
            )


def create_grpc_server() -> grpc.aio.Server:
    """Create and configure the gRPC server."""
    server = grpc.aio.server()

    # Add the servicer
    servicer = A2ARegistryServicer()
    registry_pb2_grpc.add_A2ARegistryServiceServicer_to_server(servicer, server)

    return server
