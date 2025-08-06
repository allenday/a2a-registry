"""Integration tests for vector search functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.a2a_registry.vector_enhanced_storage import VectorEnhancedStorage
from src.a2a_registry.storage import InMemoryStorage
from src.a2a_registry.vector_store import FAISSVectorStore
from src.a2a_registry.vector_generator import VectorGenerator


class TestVectorSearchIntegration:
    """Test vector search integration."""

    @pytest.fixture
    def sample_agent_card(self):
        """Sample agent card for testing."""
        return {
            "url": "https://example.com/strategic-planner",
            "name": "Strategic Planning Assistant", 
            "description": "AI agent for strategic planning and long-term vision",
            "version": "1.0.0",
            "protocol_version": "0.1.0",
            "skills": [
                {
                    "id": "strategic_planning",
                    "name": "Strategic Planning",
                    "description": "Develop strategic plans for organizations",
                    "tags": ["planning", "strategy"],
                    "examples": ["Create roadmaps", "Analyze markets"]
                }
            ],
            "capabilities": {
                "extensions": [
                    {
                        "description": "Strategic planning extension",
                        "params": {
                            "methodologies": ["OKRs", "SWOT analysis"],
                            "core_principles": ["data-driven decisions"]
                        }
                    }
                ]
            }
        }

    @pytest.mark.asyncio
    async def test_vector_enhanced_storage_initialization(self):
        """Test that vector-enhanced storage initializes correctly."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        assert storage.backend == backend
        assert isinstance(storage.vector_generator, VectorGenerator)
        assert isinstance(storage.vector_store, FAISSVectorStore)

    @pytest.mark.asyncio  
    async def test_agent_registration_generates_vectors(self, sample_agent_card):
        """Test that registering an agent generates vectors."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        # Register agent
        success = await storage.register_agent(sample_agent_card)
        assert success
        
        # Check vectors were generated
        agent_id = sample_agent_card["name"]
        vectors = await storage.get_agent_vectors(agent_id)
        assert len(vectors) > 0
        
        # Verify vector properties
        for vector in vectors:
            assert vector.agent_id == agent_id
            assert len(vector.values) > 0
            assert vector.field_path != ""
            assert vector.field_content != ""

    @pytest.mark.asyncio
    async def test_vector_search_functionality(self, sample_agent_card):
        """Test vector similarity search."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        # Register agent
        await storage.register_agent(sample_agent_card)
        
        # Test vector search
        results = await storage.search_agents_vector(
            "I need help with strategic planning",
            similarity_threshold=0.1,  # Low threshold for testing
            max_results=10
        )
        
        assert len(results) > 0
        agent, score = results[0]
        assert agent["name"] == "Strategic Planning Assistant"
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_hybrid_search_modes(self, sample_agent_card):
        """Test different search modes."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        await storage.register_agent(sample_agent_card)
        
        # Test vector mode
        vector_results = await storage.search_agents_hybrid(
            query="strategic planning",
            search_mode="SEARCH_MODE_VECTOR",
            similarity_threshold=0.1
        )
        assert len(vector_results) > 0
        assert vector_results[0][1] is not None  # Has similarity score
        
        # Test keyword mode  
        keyword_results = await storage.search_agents_hybrid(
            query="Strategic",
            search_mode="SEARCH_MODE_KEYWORD"
        )
        assert len(keyword_results) > 0
        assert keyword_results[0][1] is None  # No similarity score

    @pytest.mark.asyncio
    async def test_skill_filtering(self, sample_agent_card):
        """Test search with skill filtering."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        await storage.register_agent(sample_agent_card)
        
        # Search with matching skill
        results = await storage.search_agents_hybrid(
            query="planning",
            skills=["strategic_planning"],
            search_mode="SEARCH_MODE_KEYWORD"
        )
        assert len(results) == 1
        
        # Search with non-matching skill
        results = await storage.search_agents_hybrid(
            query="planning", 
            skills=["nonexistent_skill"],
            search_mode="SEARCH_MODE_KEYWORD"
        )
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_vector_operations(self, sample_agent_card):
        """Test vector CRUD operations."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        agent_id = sample_agent_card["name"]
        
        # Register agent to generate vectors
        await storage.register_agent(sample_agent_card)
        
        # Get vectors
        vectors = await storage.get_agent_vectors(agent_id)
        assert len(vectors) > 0
        
        # Update vectors
        new_vectors = vectors[:1]  # Keep only first vector
        success = await storage.update_agent_vectors(agent_id, new_vectors)
        assert success
        
        # Verify update
        updated_vectors = await storage.get_agent_vectors(agent_id)
        assert len(updated_vectors) == 1

    @pytest.mark.asyncio
    async def test_unregister_removes_vectors(self, sample_agent_card):
        """Test that unregistering an agent removes its vectors."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        agent_id = sample_agent_card["name"]
        
        # Register and verify vectors exist
        await storage.register_agent(sample_agent_card)
        vectors = await storage.get_agent_vectors(agent_id)
        assert len(vectors) > 0
        
        # Unregister agent
        success = await storage.unregister_agent(agent_id)
        assert success
        
        # Verify vectors removed
        vectors = await storage.get_agent_vectors(agent_id)
        assert len(vectors) == 0

    def test_vector_stats(self):
        """Test vector store statistics."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        stats = storage.get_vector_stats()
        assert "total_vectors" in stats
        assert "total_agents" in stats
        assert "vector_dimensions" in stats
        assert stats["vector_dimensions"] == 384  # Default model dimension

    @pytest.mark.asyncio
    async def test_extension_params_indexed(self):
        """Test that extension parameters are properly indexed."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        # Agent with specific extension params
        agent_card = {
            "url": "https://example.com/test-agent",
            "name": "Test Agent",
            "description": "Test description",
            "version": "1.0.0",
            "protocol_version": "0.1.0",
            "capabilities": {
                "extensions": [
                    {
                        "description": "Test extension",
                        "params": {
                            "special_capability": "quantum_computing",
                            "expertise_areas": ["machine_learning", "data_analysis"]
                        }
                    }
                ]
            }
        }
        
        await storage.register_agent(agent_card)
        
        # Search for content that should be in extension params
        results = await storage.search_agents_vector(
            "quantum computing",
            similarity_threshold=0.1,
            max_results=5
        )
        
        assert len(results) > 0
        found_agent = results[0][0]
        assert found_agent["name"] == "Test Agent"


class TestVectorSearchFailures:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_empty_query_vector_search(self):
        """Test vector search with empty query."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        results = await storage.search_agents_vector("", similarity_threshold=0.7)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_no_agents_registered(self):
        """Test search when no agents are registered."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        results = await storage.search_agents_vector(
            "test query", 
            similarity_threshold=0.7
        )
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_high_similarity_threshold(self, sample_agent_card):
        """Test search with very high similarity threshold."""
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        await storage.register_agent(sample_agent_card)
        
        # Very high threshold should return no results
        results = await storage.search_agents_vector(
            "completely unrelated query about cooking",
            similarity_threshold=0.99,
            max_results=10
        )
        assert len(results) == 0

    @pytest.fixture
    def sample_agent_card(self):
        """Sample agent card for testing."""
        return {
            "url": "https://example.com/test-agent",
            "name": "Test Agent", 
            "description": "Test agent for testing purposes",
            "version": "1.0.0",
            "protocol_version": "0.1.0",
            "skills": [
                {
                    "id": "testing",
                    "name": "Testing",
                    "description": "Software testing capabilities"
                }
            ]
        }