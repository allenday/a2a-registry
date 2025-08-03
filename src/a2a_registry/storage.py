"""Storage module for A2A Registry."""

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from fasta2a.schema import AgentCard  # type: ignore

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Register an agent in the registry."""
        pass

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get an agent by ID."""
        pass

    @abstractmethod
    async def list_agents(self) -> list[AgentCard]:
        """List all registered agents."""
        pass

    @abstractmethod
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        pass

    @abstractmethod
    async def search_agents(self, query: str) -> list[AgentCard]:
        """Search agents by name, description, or capabilities."""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage for agent registry."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentCard] = {}

    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Register an agent in the registry."""
        agent_id = agent_card.get("name")
        if not agent_id:
            return False
        self._agents[agent_id] = agent_card
        logger.info(f"Registered agent: {agent_id}")
        return True

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    async def list_agents(self) -> list[AgentCard]:
        """List all registered agents."""
        return list(self._agents.values())

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False

    async def search_agents(self, query: str) -> list[AgentCard]:
        """Search agents by name, description, or capabilities."""
        results = []
        query_lower = query.lower()

        for agent in self._agents.values():
            # Search in name, description, and skills
            if (
                query_lower in agent.get("name", "").lower()
                or query_lower in agent.get("description", "").lower()
                or any(
                    query_lower in skill.get("id", "").lower()
                    for skill in agent.get("skills", [])
                )
            ):
                results.append(agent)

        return results


class FileStorage(StorageBackend):
    """File-based persistent storage for agent registry."""

    def __init__(self, data_dir: str = "/data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.agents_file = self.data_dir / "agents.json"
        self._agents: dict[str, AgentCard] = {}
        self._load_agents()

    def _load_agents(self) -> None:
        """Load agents from file."""
        try:
            if self.agents_file.exists():
                with open(self.agents_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._agents = {k: v for k, v in data.items()}
                logger.info(f"Loaded {len(self._agents)} agents from {self.agents_file}")
        except Exception as e:
            logger.warning(f"Failed to load agents from file: {e}")
            self._agents = {}

    def _save_agents(self) -> None:
        """Save agents to file."""
        try:
            with open(self.agents_file, "w", encoding="utf-8") as f:
                json.dump(self._agents, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self._agents)} agents to {self.agents_file}")
        except Exception as e:
            logger.error(f"Failed to save agents to file: {e}")

    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Register an agent in the registry."""
        agent_id = agent_card.get("name")
        if not agent_id:
            return False
        self._agents[agent_id] = agent_card
        self._save_agents()
        logger.info(f"Registered agent: {agent_id}")
        return True

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    async def list_agents(self) -> list[AgentCard]:
        """List all registered agents."""
        return list(self._agents.values())

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            self._save_agents()
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False

    async def search_agents(self, query: str) -> list[AgentCard]:
        """Search agents by name, description, or capabilities."""
        results = []
        query_lower = query.lower()

        for agent in self._agents.values():
            # Search in name, description, and skills
            if (
                query_lower in agent.get("name", "").lower()
                or query_lower in agent.get("description", "").lower()
                or any(
                    query_lower in skill.get("id", "").lower()
                    for skill in agent.get("skills", [])
                )
            ):
                results.append(agent)

        return results


def get_storage_backend() -> StorageBackend:
    """Get the appropriate storage backend based on environment configuration."""
    storage_type = os.getenv("STORAGE_TYPE", "memory").lower()
    data_dir = os.getenv("STORAGE_DATA_DIR", "/data")
    
    if storage_type == "file":
        logger.info(f"Using file storage backend with data directory: {data_dir}")
        return FileStorage(data_dir)
    else:
        logger.info("Using in-memory storage backend")
        return InMemoryStorage()


# Global storage instance
storage = get_storage_backend()
