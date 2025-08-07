"""FAISS-based vector store for agent registry semantic search."""

import logging
import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from .proto.generated.registry_pb2 import Vector  # type: ignore

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """In-memory vector store using FAISS for similarity search."""

    def __init__(self, vector_dimensions: int = 384, persist_path: str | None = None):
        """Initialize FAISS vector store.

        Args:
            vector_dimensions: Dimension of vectors (should match VectorGenerator model)
            persist_path: Optional path to persist/load index from disk
        """
        self.vector_dimensions = vector_dimensions
        self.persist_path = persist_path

        # FAISS index for similarity search
        self.index = faiss.IndexFlatIP(
            vector_dimensions
        )  # Inner product (cosine similarity)

        # Metadata storage (agent_id -> vector list mapping)
        self.agent_vectors: dict[str, list[Vector]] = {}
        self.vector_id_to_agent: dict[int, str] = {}  # FAISS index ID -> agent_id
        self.next_vector_id = 0

        # Load persisted index if available
        if persist_path and Path(persist_path).exists():
            self.load_index()

        logger.info(
            f"Initialized FAISS vector store with {vector_dimensions} dimensions"
        )

    def add_agent_vectors(self, agent_id: str, vectors: list[Vector]) -> None:
        """Add or update vectors for an agent.

        Args:
            agent_id: Unique agent identifier
            vectors: List of vector proto messages
        """
        # Remove existing vectors for this agent
        self.remove_agent_vectors(agent_id)

        if not vectors:
            return

        # Convert vectors to numpy array
        vector_matrix = np.array([v.values for v in vectors], dtype=np.float32)

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vector_matrix)

        # Add to FAISS index
        start_id = self.next_vector_id
        self.index.add(vector_matrix)

        # Update metadata mappings
        self.agent_vectors[agent_id] = vectors
        for i, _vector in enumerate(vectors):
            vector_id = start_id + i
            self.vector_id_to_agent[vector_id] = agent_id

        self.next_vector_id += len(vectors)

        logger.debug(f"Added {len(vectors)} vectors for agent {agent_id}")

    def remove_agent_vectors(self, agent_id: str) -> None:
        """Remove all vectors for an agent.

        Args:
            agent_id: Unique agent identifier
        """
        if agent_id not in self.agent_vectors:
            return

        # FAISS doesn't support efficient deletion, so we rebuild the index
        # This is acceptable for in-memory use with moderate data sizes
        vectors_to_keep = []
        new_agent_vectors = {}
        new_vector_id_mapping = {}
        new_vector_id = 0

        for aid, agent_vecs in self.agent_vectors.items():
            if aid != agent_id:
                vectors_to_keep.extend([v.values for v in agent_vecs])
                new_agent_vectors[aid] = agent_vecs

                for _ in agent_vecs:
                    new_vector_id_mapping[new_vector_id] = aid
                    new_vector_id += 1

        # Rebuild index
        self.index = faiss.IndexFlatIP(self.vector_dimensions)
        if vectors_to_keep:
            vector_matrix = np.array(vectors_to_keep, dtype=np.float32)
            faiss.normalize_L2(vector_matrix)
            self.index.add(vector_matrix)

        # Update metadata
        self.agent_vectors = new_agent_vectors
        self.vector_id_to_agent = new_vector_id_mapping
        self.next_vector_id = new_vector_id

        logger.debug(f"Removed vectors for agent {agent_id}")

    def search_similar_vectors(
        self,
        query_vector: Vector,
        k: int = 10,
        similarity_threshold: float = 0.7,
    ) -> list[tuple[str, Vector, float]]:
        """Search for similar vectors.

        Args:
            query_vector: Query vector proto message
            k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of (agent_id, vector, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            return []

        # Prepare query vector
        query = np.array([query_vector.values], dtype=np.float32)
        faiss.normalize_L2(query)

        # Search FAISS index
        similarities, indices = self.index.search(query, min(k, self.index.ntotal))

        results = []
        for _i, (similarity, vector_idx) in enumerate(
            zip(similarities[0], indices[0], strict=False)
        ):
            if similarity < similarity_threshold:
                continue

            agent_id = self.vector_id_to_agent.get(vector_idx)
            if not agent_id:
                continue

            # Get agent vectors
            agent_vectors = self.agent_vectors.get(agent_id, [])
            if not agent_vectors:
                continue

            # Find the specific vector that matched - simplified logic
            try:
                start_idx = self._get_agent_vector_start_idx(agent_id)
                local_vector_idx = vector_idx - start_idx

                if 0 <= local_vector_idx < len(agent_vectors):
                    matched_vector = agent_vectors[local_vector_idx]
                    # Ensure similarity is a proper float
                    similarity_score = float(similarity)
                    results.append((agent_id, matched_vector, similarity_score))
                else:
                    # Fallback: use first vector if index calculation fails
                    logger.warning(
                        f"Vector index calculation failed for agent {agent_id}, using first vector"
                    )
                    matched_vector = agent_vectors[0]
                    similarity_score = float(similarity)
                    results.append((agent_id, matched_vector, similarity_score))
            except Exception as e:
                logger.error(f"Error processing vector match for agent {agent_id}: {e}")
                continue

        return results

    def get_agent_vectors(self, agent_id: str) -> list[Vector]:
        """Get all vectors for an agent.

        Args:
            agent_id: Unique agent identifier

        Returns:
            List of vector proto messages
        """
        return self.agent_vectors.get(agent_id, [])

    def _get_agent_vector_start_idx(self, agent_id: str) -> int:
        """Get the starting FAISS index for an agent's vectors."""
        start_idx = 0
        for aid, vectors in self.agent_vectors.items():
            if aid == agent_id:
                break
            start_idx += len(vectors)
        return start_idx

    def save_index(self) -> None:
        """Persist index and metadata to disk."""
        if not self.persist_path:
            return

        persist_dir = Path(self.persist_path).parent
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, f"{self.persist_path}.faiss")

        # Save metadata
        metadata = {
            "agent_vectors": self.agent_vectors,
            "vector_id_to_agent": self.vector_id_to_agent,
            "next_vector_id": self.next_vector_id,
            "vector_dimensions": self.vector_dimensions,
        }

        with open(f"{self.persist_path}.meta", "wb") as f:
            pickle.dump(metadata, f)

        logger.info(f"Saved vector index to {self.persist_path}")

    def load_index(self) -> None:
        """Load index and metadata from disk."""
        if not self.persist_path:
            return

        try:
            # Load FAISS index
            self.index = faiss.read_index(f"{self.persist_path}.faiss")

            # Load metadata
            with open(f"{self.persist_path}.meta", "rb") as f:
                metadata = pickle.load(f)

            self.agent_vectors = metadata["agent_vectors"]
            self.vector_id_to_agent = metadata["vector_id_to_agent"]
            self.next_vector_id = metadata["next_vector_id"]
            self.vector_dimensions = metadata["vector_dimensions"]

            logger.info(f"Loaded vector index from {self.persist_path}")

        except Exception as e:
            logger.warning(f"Failed to load vector index: {e}")
            # Initialize empty index
            self.index = faiss.IndexFlatIP(self.vector_dimensions)
            self.agent_vectors = {}
            self.vector_id_to_agent = {}
            self.next_vector_id = 0

    def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_vectors": self.index.ntotal,
            "total_agents": len(self.agent_vectors),
            "vector_dimensions": self.vector_dimensions,
            "memory_usage_mb": self.index.ntotal
            * self.vector_dimensions
            * 4
            / (1024 * 1024),  # float32
        }
