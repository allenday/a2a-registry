"""Vector generation module for A2A Registry agent cards and extensions."""

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np
from google.protobuf import struct_pb2, timestamp_pb2
from sentence_transformers import SentenceTransformer

from .proto.generated import registry_pb2

logger = logging.getLogger(__name__)


class VectorGenerator:
    """Generate embedding vectors from agent card content with provenance tracking."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector generator.

        Args:
            model_name: Name of the sentence transformer model to use.
                       Options: 'all-MiniLM-L6-v2' (fast, 384 dims),
                               'all-mpnet-base-v2' (better quality, 768 dims)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.vector_dimensions = self.model.get_sentence_embedding_dimension()
        logger.info(
            f"Initialized VectorGenerator with model {model_name} ({self.vector_dimensions} dimensions)"
        )

    def extract_text_from_params(self, params: dict[str, Any]) -> str:
        """Recursively extract meaningful text from extension params.

        Args:
            params: Extension parameters dict

        Returns:
            Concatenated text from all string and array values
        """
        texts = []

        def _extract_recursive(obj: Any, path: str = "") -> None:
            if isinstance(obj, str):
                # Add string values
                texts.append(obj)
            elif isinstance(obj, list):
                # Process list items
                for i, item in enumerate(obj):
                    _extract_recursive(item, f"{path}[{i}]")
            elif isinstance(obj, dict):
                # Process dictionary values
                for key, value in obj.items():
                    # Include the key as text (useful for competencies)
                    if isinstance(key, str):
                        texts.append(key)
                    new_path = f"{path}.{key}" if path else key
                    _extract_recursive(value, new_path)
            elif isinstance(obj, (int, float, bool)):
                # Convert numbers and booleans to strings
                texts.append(str(obj))

        _extract_recursive(params)
        return " ".join(texts)

    def generate_agent_vectors(
        self, agent_card: dict[str, Any]
    ) -> list[registry_pb2.Vector]:
        """Generate vectors for all searchable fields in an agent card.

        Args:
            agent_card: Agent card dictionary

        Returns:
            List of Vector proto messages with provenance
        """
        vectors = []
        agent_id = agent_card.get("url", "")

        # Agent-level fields
        if "name" in agent_card:
            vectors.append(self._create_vector(agent_id, "name", agent_card["name"]))

        if "description" in agent_card:
            vectors.append(
                self._create_vector(agent_id, "description", agent_card["description"])
            )

        # Skills
        skills = agent_card.get("skills", [])
        for i, skill in enumerate(skills):
            skill_texts = []

            if "name" in skill:
                skill_texts.append(skill["name"])
                vectors.append(
                    self._create_vector(agent_id, f"skills[{i}].name", skill["name"])
                )

            if "description" in skill:
                skill_texts.append(skill["description"])
                vectors.append(
                    self._create_vector(
                        agent_id, f"skills[{i}].description", skill["description"]
                    )
                )

            if "tags" in skill and isinstance(skill["tags"], list):
                tags_text = " ".join(skill["tags"])
                skill_texts.append(tags_text)
                vectors.append(
                    self._create_vector(agent_id, f"skills[{i}].tags", tags_text)
                )

            if "examples" in skill and isinstance(skill["examples"], list):
                examples_text = " ".join(skill["examples"])
                skill_texts.append(examples_text)
                vectors.append(
                    self._create_vector(
                        agent_id, f"skills[{i}].examples", examples_text
                    )
                )

            # Combined skill vector
            if skill_texts:
                combined_text = " ".join(skill_texts)
                vectors.append(
                    self._create_vector(agent_id, f"skills[{i}]", combined_text)
                )

        # Extensions
        capabilities = agent_card.get("capabilities", {})
        extensions = capabilities.get("extensions", [])

        for i, extension in enumerate(extensions):
            extension_texts = []

            if "description" in extension:
                extension_texts.append(extension["description"])
                vectors.append(
                    self._create_vector(
                        agent_id,
                        f"extensions[{i}].description",
                        extension["description"],
                    )
                )

            # Extract text from params
            if "params" in extension and isinstance(extension["params"], dict):
                params_text = self.extract_text_from_params(extension["params"])
                if params_text.strip():
                    extension_texts.append(params_text)
                    vectors.append(
                        self._create_vector(
                            agent_id, f"extensions[{i}].params", params_text
                        )
                    )

            # Combined extension vector
            if extension_texts:
                combined_text = " ".join(extension_texts)
                vectors.append(
                    self._create_vector(agent_id, f"extensions[{i}]", combined_text)
                )

        return vectors

    def generate_query_vector(self, query: str) -> registry_pb2.Vector:
        """Generate a vector for a search query.

        Args:
            query: Search query text

        Returns:
            Vector proto message for the query
        """
        return self._create_vector("", "query", query)

    def calculate_similarity(
        self, vector1: registry_pb2.Vector, vector2: registry_pb2.Vector
    ) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vector1: First vector
            vector2: Second vector

        Returns:
            Similarity score between 0 and 1
        """
        v1 = np.array(vector1.values)
        v2 = np.array(vector2.values)

        # Cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    def search_similar_vectors(
        self,
        query_vector: registry_pb2.Vector,
        agent_vectors: list[registry_pb2.Vector],
        threshold: float = 0.7,
        max_results: int = 10,
    ) -> list[tuple[registry_pb2.Vector, float]]:
        """Search for similar vectors using cosine similarity.

        Args:
            query_vector: Query vector to search for
            agent_vectors: List of agent vectors to search in
            threshold: Minimum similarity threshold
            max_results: Maximum number of results to return

        Returns:
            List of (vector, similarity_score) tuples, sorted by similarity
        """
        results = []

        for vector in agent_vectors:
            similarity = self.calculate_similarity(query_vector, vector)
            if similarity >= threshold:
                results.append((vector, similarity))

        # Sort by similarity (descending) and limit results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def _create_vector(
        self, agent_id: str, field_path: str, content: str
    ) -> registry_pb2.Vector:
        """Create a Vector proto message from text content.

        Args:
            agent_id: Agent identifier (URL)
            field_path: Path to the field in the agent card
            content: Text content to vectorize

        Returns:
            Vector proto message
        """
        # Generate embedding
        embedding = self.model.encode(content, convert_to_numpy=True)

        # Create timestamp
        now = datetime.now(timezone.utc)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(now)

        # Create metadata
        metadata = struct_pb2.Struct()
        metadata.update(
            {
                "model": self.model_name,
                "dimensions": self.vector_dimensions,
                "content_length": len(content),
            }
        )

        # Create vector
        vector = registry_pb2.Vector(
            values=embedding.tolist(),
            agent_id=agent_id,
            field_path=field_path,
            field_content=content,
            created_at=timestamp,
            metadata=metadata,
        )

        return vector
