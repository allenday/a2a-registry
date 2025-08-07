"""Vector-enhanced storage for A2A Registry with semantic search capabilities."""

import logging
from typing import Any

from fasta2a.schema import AgentCard

from .proto.generated.registry_pb2 import Vector  # type: ignore
from .storage import ExtensionInfo, StorageBackend
from .vector_generator import VectorGenerator
from .vector_store import FAISSVectorStore

logger = logging.getLogger(__name__)


class VectorEnhancedStorage(StorageBackend):
    """Storage wrapper that adds vector search capabilities to any storage backend."""

    def __init__(self, backend: StorageBackend, vector_model: str = "all-MiniLM-L6-v2"):
        """Initialize vector-enhanced storage.

        Args:
            backend: Underlying storage backend
            vector_model: Sentence transformer model name
        """
        self.backend = backend
        self.vector_generator = VectorGenerator(vector_model)
        self.vector_store = FAISSVectorStore(
            vector_dimensions=self.vector_generator.vector_dimensions or 384,
            persist_path="data/vectors/index",
        )
        logger.info(f"Initialized vector-enhanced storage with {vector_model}")

    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Register an agent and generate its vectors."""
        # Store in underlying backend
        success = await self.backend.register_agent(agent_card)
        if not success:
            return False

        # Generate and store vectors
        await self._update_agent_vectors(agent_card)
        return True

    async def get_agent(self, agent_id: str) -> AgentCard | None:
        """Get an agent by ID."""
        return await self.backend.get_agent(agent_id)

    async def list_agents(self) -> list[AgentCard]:
        """List all registered agents."""
        return await self.backend.list_agents()

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent and remove its vectors."""
        success = await self.backend.unregister_agent(agent_id)
        if success:
            self.vector_store.remove_agent_vectors(agent_id)
        return success

    async def search_agents(self, query: str) -> list[AgentCard]:
        """Search agents (default implementation uses keyword search)."""
        return await self.backend.search_agents(query)

    async def search_agents_keyword(self, query: str) -> list[AgentCard]:
        """Search agents using keyword-based search."""
        return await self.backend.search_agents(query)

    async def search_agents_vector(
        self, query: str, similarity_threshold: float = 0.5, max_results: int = 10
    ) -> list[tuple[AgentCard, float]]:
        """Search agents using vector similarity with information-theoretically sound aggregation.

        Args:
            query: Natural language search query
            similarity_threshold: Minimum similarity score
            max_results: Maximum number of results

        Returns:
            List of (agent_card, similarity_score) tuples
        """
        # Generate query vector
        query_vector = self.vector_generator.generate_query_vector(query)

        # Phase 1: Candidate generation - find all vectors above threshold
        # Use a larger k to capture more candidate vectors
        candidate_k = max_results * 10  # Expand search space for candidates
        similar_vectors = self.vector_store.search_similar_vectors(
            query_vector, k=candidate_k, similarity_threshold=similarity_threshold
        )

        # Phase 2: Agent profiling - collect all matches per agent
        agent_vector_matches: dict[str, list[tuple[Vector, float]]] = {}
        for agent_id, vector, score in similar_vectors:
            if agent_id not in agent_vector_matches:
                agent_vector_matches[agent_id] = []
            agent_vector_matches[agent_id].append((vector, score))

        # Phase 3: Information-theoretic composite scoring
        agent_composite_scores: dict[str, float] = {}
        for agent_id, matches in agent_vector_matches.items():
            if not matches:
                continue
                
            # Extract scores for this agent
            scores = [score for _vector, score in matches]
            
            # Composite scoring strategy: weighted combination
            # - Top score (strongest signal): 60% weight
            # - Mean of top 3 scores (consistency): 30% weight  
            # - Coverage bonus (number of matches): 10% weight
            
            max_score = max(scores)
            top_3_mean = sum(sorted(scores, reverse=True)[:3]) / min(3, len(scores))
            coverage_bonus = min(len(scores) / 5.0, 1.0)  # Normalize to [0, 1]
            
            composite_score = (
                0.6 * max_score + 
                0.3 * top_3_mean + 
                0.1 * coverage_bonus
            )
            
            agent_composite_scores[agent_id] = composite_score

        # Phase 4: Rank and return results
        results = []
        for agent_id, score in sorted(
            agent_composite_scores.items(), key=lambda x: x[1], reverse=True
        )[:max_results]:
            agent_card = await self.get_agent(agent_id)
            if agent_card:
                results.append((agent_card, score))

        return results

    async def search_agents_hybrid(
        self,
        query: str = "",
        skills: list[str] | None = None,
        search_mode: str = "SEARCH_MODE_VECTOR",
        similarity_threshold: float = 0.5,
        max_results: int = 10,
    ) -> list[tuple[AgentCard, float | None]]:
        """Search agents using hybrid approach per proto spec.

        Args:
            query: Search query string or semantic query
            skills: Optional list of required skills
            search_mode: "SEARCH_MODE_KEYWORD" or "SEARCH_MODE_VECTOR"
            similarity_threshold: For vector search
            max_results: Maximum number of results

        Returns:
            List of (agent_card, similarity_score) tuples
        """
        if search_mode == "SEARCH_MODE_VECTOR" and query:
            # Vector-only search
            results = await self.search_agents_vector(
                query, similarity_threshold, max_results
            )

            # Apply skill filtering if specified
            if skills:
                filtered_results: list[tuple[AgentCard, float | None]] = []
                for agent_card, score in results:
                    agent_skills = [
                        skill.get("id", "") for skill in agent_card.get("skills", [])
                    ]
                    if any(skill in agent_skills for skill in skills):
                        filtered_results.append((agent_card, score))
                return filtered_results

            # Cast to match return type
            results_cast: list[tuple[AgentCard, float | None]] = [
                (agent, score) for agent, score in results
            ]
            return results_cast

        else:
            # Keyword-only search
            agents = await self.search_agents_keyword(query)

            # Apply skill filtering if specified
            if skills:
                filtered_agents = []
                for agent in agents:
                    agent_skills = [
                        skill.get("id", "") for skill in agent.get("skills", [])
                    ]
                    if any(skill in agent_skills for skill in skills):
                        filtered_agents.append(agent)
                agents = filtered_agents

            # Return without similarity scores for keyword search
            return [(agent, None) for agent in agents[:max_results]]

    async def get_agent_vectors(self, agent_id: str) -> list[Vector]:
        """Get all vectors for an agent."""
        return self.vector_store.get_agent_vectors(agent_id)

    async def update_agent_vectors(self, agent_id: str, vectors: list[Vector]) -> bool:
        """Update vectors for an agent directly."""
        try:
            self.vector_store.add_agent_vectors(agent_id, vectors)
            return True
        except Exception as e:
            logger.error(f"Failed to update vectors for agent {agent_id}: {e}")
            return False

    async def _update_agent_vectors(self, agent_card: AgentCard) -> None:
        """Generate and update vectors for an agent card."""
        try:
            # Use same ID strategy as backend storage (name)
            agent_id = agent_card.get("name", "")
            if not agent_id:
                logger.warning("Agent card missing name, cannot generate vectors")
                return

            # Generate vectors from agent card
            vectors = self.vector_generator.generate_agent_vectors(
                dict(agent_card), agent_id
            )

            # Store vectors
            self.vector_store.add_agent_vectors(agent_id, vectors)

            logger.debug(f"Generated {len(vectors)} vectors for agent {agent_id}")

        except Exception as e:
            logger.error(f"Failed to generate vectors for agent: {e}")

    async def list_extensions(
        self,
        uri_pattern: str | None = None,
        declaring_agents: list[str] | None = None,
        trust_levels: list[str] | None = None,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> tuple[list, str | None, int]:
        """List extensions (delegated to backend)."""
        return await self.backend.list_extensions(
            uri_pattern=uri_pattern,
            declaring_agents=declaring_agents,
            trust_levels=trust_levels,
            page_size=page_size,
            page_token=page_token,
        )

    def get_vector_stats(self) -> dict:
        """Get vector store statistics."""
        return self.vector_store.get_stats()

    def save_vectors(self) -> None:
        """Persist vectors to disk."""
        self.vector_store.save_index()

    # Extension-related methods (delegated to backend)
    async def store_extension(self, extension_info: ExtensionInfo) -> bool:
        """Store extension information."""
        return await self.backend.store_extension(extension_info)

    async def get_extension(self, uri: str) -> ExtensionInfo | None:
        """Get extension information by URI."""
        return await self.backend.get_extension(uri)

    async def get_agent_extensions(self, agent_id: str) -> list[ExtensionInfo]:
        """Get all extensions used by a specific agent."""
        return await self.backend.get_agent_extensions(agent_id)

    async def update_agent_extensions(
        self, agent_id: str, extensions: list[dict]
    ) -> bool:
        """Update extensions for an agent."""
        return await self.backend.update_agent_extensions(agent_id, extensions)

    async def remove_agent_from_extensions(self, agent_id: str) -> bool:
        """Remove agent from all extension declarations."""
        return await self.backend.remove_agent_from_extensions(agent_id)

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to the underlying backend."""
        return getattr(self.backend, name)
