"""Tests for vector generation functionality."""

import json
import pytest
import numpy as np
from unittest.mock import Mock, patch

from src.a2a_registry.vector_generator import VectorGenerator
from src.a2a_registry.proto.generated import registry_pb2


class TestVectorGenerator:
    """Test cases for VectorGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a VectorGenerator instance for testing."""
        with patch('src.a2a_registry.vector_generator.SentenceTransformer') as mock_transformer:
            # Mock the sentence transformer
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = np.random.rand(384)  # Random 384-dim vector
            mock_transformer.return_value = mock_model
            
            generator = VectorGenerator("test-model")
            generator.model = mock_model
            return generator
    
    @pytest.fixture
    def sample_agent_card(self):
        """Sample agent card for testing."""
        return {
            "name": "Steve Jobs",
            "description": "A transformative product visionary known for revolutionizing technology through an uncompromising commitment to design, simplicity, and user experience.",
            "url": "https://agents.polyhegel.ai/persona/steve_jobs",
            "version": "1.0.0",
            "protocol_version": "0.3.0",
            "capabilities": {
                "extensions": [
                    {
                        "description": "Persona characteristics and behavioral patterns for Steve Jobs",
                        "params": {
                            "core_principles": [
                                "Simplicity is the ultimate sophistication",
                                "Design drives user experience",
                                "Passion and vision trump conventional wisdom"
                            ],
                            "competency_scores": {
                                "strategic planning and long-term vision": 0.95,
                                "team leadership and inspiring others": 0.92,
                                "creative innovation and design thinking": 0.97
                            }
                        },
                        "uri": "https://polyhegel.ai/extensions/persona-characteristics/v1"
                    }
                ]
            },
            "skills": [
                {
                    "id": "steve_jobs_skill_1",
                    "name": "Radical product reimagination",
                    "description": "Steve Jobs can radical product reimagination",
                    "tags": ["product_innovation_and_strategic_leadership", "advisor"],
                    "examples": ["Help me with radical product reimagination"]
                },
                {
                    "id": "steve_jobs_skill_2", 
                    "name": "Synthesizing complex technological concepts",
                    "description": "Steve Jobs can synthesizing complex technological concepts",
                    "tags": ["technology_product_design", "consumer_electronics"],
                    "examples": ["Help me with synthesizing complex technological concepts"]
                }
            ]
        }
    
    def test_vector_generator_initialization(self):
        """Test VectorGenerator initialization."""
        with patch('src.a2a_registry.vector_generator.SentenceTransformer') as mock_transformer:
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 768
            mock_transformer.return_value = mock_model
            
            generator = VectorGenerator("all-mpnet-base-v2")
            
            assert generator.model_name == "all-mpnet-base-v2"
            assert generator.vector_dimensions == 768
            mock_transformer.assert_called_once_with("all-mpnet-base-v2")
    
    def test_extract_text_from_params(self, generator):
        """Test extraction of text from extension params."""
        params = {
            "core_principles": [
                "Simplicity is the ultimate sophistication",
                "Design drives user experience"
            ],
            "competency_scores": {
                "strategic planning": 0.95,
                "team leadership": 0.92
            },
            "decision_framework": "Intuitive design-driven approach",
            "active": True,
            "priority": 1
        }
        
        extracted_text = generator.extract_text_from_params(params)
        
        # Check that all text content is extracted
        assert "Simplicity is the ultimate sophistication" in extracted_text
        assert "Design drives user experience" in extracted_text
        assert "strategic planning" in extracted_text
        assert "team leadership" in extracted_text
        assert "Intuitive design-driven approach" in extracted_text
        assert "0.95" in extracted_text
        assert "0.92" in extracted_text
        assert "True" in extracted_text
        assert "1" in extracted_text
    
    def test_generate_agent_vectors(self, generator, sample_agent_card):
        """Test generation of vectors from agent card."""
        vectors = generator.generate_agent_vectors(sample_agent_card)
        
        # Should generate vectors for various fields
        field_paths = [v.field_path for v in vectors]
        
        # Check agent-level vectors
        assert "name" in field_paths
        assert "description" in field_paths
        
        # Check skill vectors
        assert "skills[0].name" in field_paths
        assert "skills[0].description" in field_paths
        assert "skills[0].tags" in field_paths
        assert "skills[0].examples" in field_paths
        assert "skills[0]" in field_paths  # Combined skill vector
        
        assert "skills[1].name" in field_paths
        assert "skills[1]" in field_paths  # Combined skill vector
        
        # Check extension vectors
        assert "extensions[0].description" in field_paths
        assert "extensions[0].params" in field_paths
        assert "extensions[0]" in field_paths  # Combined extension vector
        
        # Verify vector properties
        for vector in vectors:
            assert vector.agent_id == "https://agents.polyhegel.ai/persona/steve_jobs"
            assert len(vector.values) == 384  # Model dimension
            assert vector.field_content != ""
            assert vector.created_at.seconds > 0
            assert vector.metadata.fields["model"].string_value == "test-model"
            assert vector.metadata.fields["dimensions"].number_value == 384
    
    def test_generate_query_vector(self, generator):
        """Test generation of query vector."""
        query = "strategic planning and leadership"
        vector = generator.generate_query_vector(query)
        
        assert vector.agent_id == ""
        assert vector.field_path == "query"
        assert vector.field_content == query
        assert len(vector.values) == 384
        assert vector.metadata.fields["model"].string_value == "test-model"
    
    def test_calculate_similarity(self, generator):
        """Test similarity calculation between vectors."""
        # Create two test vectors
        vector1 = registry_pb2.Vector(values=[1.0, 0.0, 0.0])
        vector2 = registry_pb2.Vector(values=[1.0, 0.0, 0.0])  # Identical
        vector3 = registry_pb2.Vector(values=[0.0, 1.0, 0.0])  # Orthogonal
        
        # Test identical vectors
        similarity = generator.calculate_similarity(vector1, vector2)
        assert similarity == pytest.approx(1.0, rel=1e-6)
        
        # Test orthogonal vectors
        similarity = generator.calculate_similarity(vector1, vector3)
        assert similarity == pytest.approx(0.0, rel=1e-6)
        
        # Test partially similar vectors
        vector4 = registry_pb2.Vector(values=[0.8, 0.6, 0.0])
        similarity = generator.calculate_similarity(vector1, vector4)
        assert 0 < similarity < 1
    
    def test_search_similar_vectors(self, generator):
        """Test vector similarity search."""
        # Create query vector
        query_vector = registry_pb2.Vector(values=[1.0, 0.0, 0.0])
        
        # Create agent vectors with different similarities
        agent_vectors = [
            registry_pb2.Vector(values=[0.9, 0.1, 0.0], agent_id="agent1", field_path="test1"),
            registry_pb2.Vector(values=[0.0, 1.0, 0.0], agent_id="agent2", field_path="test2"),  # Orthogonal
            registry_pb2.Vector(values=[1.0, 0.0, 0.0], agent_id="agent3", field_path="test3"),  # Identical
            registry_pb2.Vector(values=[0.5, 0.5, 0.0], agent_id="agent4", field_path="test4"),
        ]
        
        # Search with threshold 0.7
        results = generator.search_similar_vectors(
            query_vector, agent_vectors, threshold=0.7, max_results=5
        )
        
        # Should return vectors above threshold, sorted by similarity
        assert len(results) >= 2  # At least the identical and highly similar ones
        
        # Check ordering (should be sorted by similarity descending)
        similarities = [score for _, score in results]
        assert similarities == sorted(similarities, reverse=True)
        
        # Check that all results meet threshold
        for _, score in results:
            assert score >= 0.7
    
    def test_competency_extraction(self, generator):
        """Test extraction of competency scores from extension params."""
        agent_card = {
            "url": "https://test.agent.com",
            "name": "Test Agent",
            "capabilities": {
                "extensions": [
                    {
                        "description": "Competency scores extension",
                        "params": {
                            "competency_scores": {
                                "strategic planning and long-term vision": 0.95,
                                "team leadership and inspiring others": 0.92,
                                "decisive decision making under pressure": 0.9,
                                "creative innovation and design thinking": 0.97
                            }
                        }
                    }
                ]
            }
        }
        
        vectors = generator.generate_agent_vectors(agent_card)
        
        # Find the extension params vector
        params_vector = None
        for vector in vectors:
            if vector.field_path == "extensions[0].params":
                params_vector = vector
                break
        
        assert params_vector is not None
        
        # Check that competency terms are in the content
        content = params_vector.field_content
        assert "strategic planning and long-term vision" in content
        assert "team leadership and inspiring others" in content
        assert "creative innovation and design thinking" in content
        assert "0.95" in content
        assert "0.92" in content
    
    def test_empty_agent_card(self, generator):
        """Test handling of empty or minimal agent card."""
        minimal_card = {
            "url": "https://test.agent.com"
        }
        
        vectors = generator.generate_agent_vectors(minimal_card)
        
        # Should return empty list or minimal vectors
        assert isinstance(vectors, list)
        # All vectors should have the correct agent_id
        for vector in vectors:
            assert vector.agent_id == "https://test.agent.com"
    
    def test_nested_params_extraction(self, generator):
        """Test extraction from deeply nested extension params."""
        complex_params = {
            "level1": {
                "level2": {
                    "level3": ["deep text content", "more deep content"],
                    "another_field": "some value"
                },
                "simple_field": "simple text"
            },
            "array_field": [
                {"nested": "array content"},
                "simple array item"
            ]
        }
        
        extracted_text = generator.extract_text_from_params(complex_params)
        
        assert "deep text content" in extracted_text
        assert "more deep content" in extracted_text
        assert "some value" in extracted_text
        assert "simple text" in extracted_text
        assert "array content" in extracted_text
        assert "simple array item" in extracted_text
    
    def test_vector_metadata(self, generator):
        """Test that vector metadata is properly set."""
        agent_card = {
            "url": "https://test.agent.com",
            "name": "Test Agent",
            "description": "A test agent for vector testing"
        }
        
        vectors = generator.generate_agent_vectors(agent_card)
        
        for vector in vectors:
            # Check metadata fields
            assert "model" in vector.metadata.fields
            assert "dimensions" in vector.metadata.fields
            assert "content_length" in vector.metadata.fields
            
            assert vector.metadata.fields["model"].string_value == "test-model"
            assert vector.metadata.fields["dimensions"].number_value == 384
            assert vector.metadata.fields["content_length"].number_value > 0


@pytest.fixture
def real_generator():
    """Create a real VectorGenerator for integration tests."""
    try:
        return VectorGenerator("all-MiniLM-L6-v2")
    except Exception:
        pytest.skip("SentenceTransformers not available for integration tests")


class TestVectorGeneratorIntegration:
    """Integration tests with real sentence transformers."""
    
    def test_real_vector_generation(self, real_generator):
        """Test with real sentence transformer model."""
        agent_card = {
            "url": "https://test.agent.com",
            "name": "Strategic Planning Agent",
            "description": "An agent specialized in strategic planning and long-term vision",
            "skills": [
                {
                    "name": "Strategic Planning",
                    "description": "Create comprehensive strategic plans",
                    "tags": ["planning", "strategy", "vision"],
                    "examples": ["Help me create a 5-year strategic plan"]
                }
            ]
        }
        
        vectors = real_generator.generate_agent_vectors(agent_card)
        
        # Should generate multiple vectors
        assert len(vectors) > 0
        
        # All vectors should have proper dimensions
        for vector in vectors:
            assert len(vector.values) == real_generator.vector_dimensions
            assert all(isinstance(v, float) for v in vector.values)
    
    def test_real_similarity_search(self, real_generator):
        """Test similarity search with real embeddings."""
        # Generate query vector
        query_vector = real_generator.generate_query_vector(
            "strategic planning and long-term vision"
        )
        
        # Generate agent vectors
        agent_card = {
            "url": "https://test.agent.com",
            "name": "Strategic Planning Agent",
            "description": "An agent for strategic planning and vision",
            "skills": [
                {
                    "name": "Strategic Planning",
                    "description": "Expert in strategic planning",
                    "tags": ["planning", "strategy"]
                },
                {
                    "name": "Data Analysis", 
                    "description": "Analyze data and metrics",
                    "tags": ["data", "analytics"]
                }
            ]
        }
        
        agent_vectors = real_generator.generate_agent_vectors(agent_card)
        
        # Search for similar vectors
        results = real_generator.search_similar_vectors(
            query_vector, agent_vectors, threshold=0.3, max_results=5
        )
        
        # Should find some similar vectors
        assert len(results) > 0
        
        # Results should be ordered by similarity
        similarities = [score for _, score in results]
        assert similarities == sorted(similarities, reverse=True)
        
        # Strategic planning related vectors should have higher similarity
        strategic_results = [
            (vector, score) for vector, score in results
            if "strategic" in vector.field_content.lower() or "planning" in vector.field_content.lower()
        ]
        
        if strategic_results:
            avg_strategic_similarity = sum(score for _, score in strategic_results) / len(strategic_results)
            assert avg_strategic_similarity > 0.5  # Should be reasonably similar