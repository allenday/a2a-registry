"""Storage module for A2A Registry."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fasta2a.schema import AgentCard  # type: ignore

from .config import config

logger = logging.getLogger(__name__)


class ExtensionInfo:
    """Information about an agent extension with provenance tracking."""

    def __init__(
        self,
        uri: str,
        description: str = "",
        required: bool = False,
        params: Optional[dict] = None,
        first_declared_by_agent: str = "",
        first_declared_at: Optional[datetime] = None,
        trust_level: str = "TRUST_LEVEL_UNVERIFIED",
    ):
        self.uri = uri
        self.description = description
        self.required = required
        self.params = params or {}
        self.first_declared_by_agent = first_declared_by_agent
        self.first_declared_at = first_declared_at or datetime.now(timezone.utc)
        self.trust_level = trust_level
        self.declaring_agents: set[str] = set()
        if first_declared_by_agent:
            self.declaring_agents.add(first_declared_by_agent)

    @property
    def usage_count(self) -> int:
        """Number of agents using this extension."""
        return len(self.declaring_agents)

    def add_declaring_agent(self, agent_id: str) -> None:
        """Add an agent to the list of agents using this extension."""
        self.declaring_agents.add(agent_id)

    def remove_declaring_agent(self, agent_id: str) -> None:
        """Remove an agent from the list of agents using this extension."""
        self.declaring_agents.discard(agent_id)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "uri": self.uri,
            "description": self.description,
            "required": self.required,
            "params": self.params,
            "first_declared_by_agent": self.first_declared_by_agent,
            "first_declared_at": self.first_declared_at.isoformat(),
            "trust_level": self.trust_level,
            "declaring_agents": list(self.declaring_agents),
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExtensionInfo":
        """Create from dictionary representation."""
        ext_info = cls(
            uri=data["uri"],
            description=data.get("description", ""),
            required=data.get("required", False),
            params=data.get("params", {}),
            first_declared_by_agent=data.get("first_declared_by_agent", ""),
            first_declared_at=datetime.fromisoformat(data["first_declared_at"]),
            trust_level=data.get("trust_level", "TRUST_LEVEL_UNVERIFIED"),
        )
        ext_info.declaring_agents = set(data.get("declaring_agents", []))
        return ext_info


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

    # Extension-related abstract methods
    @abstractmethod
    async def store_extension(self, extension_info: ExtensionInfo) -> bool:
        """Store extension information."""
        pass

    @abstractmethod
    async def get_extension(self, uri: str) -> Optional[ExtensionInfo]:
        """Get extension information by URI."""
        pass

    @abstractmethod
    async def list_extensions(
        self,
        uri_pattern: Optional[str] = None,
        declaring_agents: Optional[list[str]] = None,
        trust_levels: Optional[list[str]] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
    ) -> tuple[list[ExtensionInfo], Optional[str], int]:
        """List extensions with optional filtering and pagination."""
        pass

    @abstractmethod
    async def get_agent_extensions(self, agent_id: str) -> list[ExtensionInfo]:
        """Get all extensions used by a specific agent."""
        pass

    @abstractmethod
    async def update_agent_extensions(
        self, agent_id: str, extensions: list[dict]
    ) -> bool:
        """Update extensions for an agent."""
        pass

    @abstractmethod
    async def remove_agent_from_extensions(self, agent_id: str) -> bool:
        """Remove agent from all extension declarations."""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage for agent registry."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentCard] = {}
        self._extensions: dict[str, ExtensionInfo] = {}

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

    # Extension-related methods
    async def store_extension(self, extension_info: ExtensionInfo) -> bool:
        """Store extension information."""
        self._extensions[extension_info.uri] = extension_info
        logger.info(f"Stored extension: {extension_info.uri}")
        return True

    async def get_extension(self, uri: str) -> Optional[ExtensionInfo]:
        """Get extension information by URI."""
        return self._extensions.get(uri)

    async def list_extensions(
        self,
        uri_pattern: Optional[str] = None,
        declaring_agents: Optional[list[str]] = None,
        trust_levels: Optional[list[str]] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
    ) -> tuple[list[ExtensionInfo], Optional[str], int]:
        """List extensions with optional filtering and pagination."""
        extensions = list(self._extensions.values())

        # Apply filters
        if uri_pattern:
            extensions = [
                ext for ext in extensions if uri_pattern.lower() in ext.uri.lower()
            ]

        if declaring_agents:
            extensions = [
                ext
                for ext in extensions
                if any(agent in ext.declaring_agents for agent in declaring_agents)
            ]

        if trust_levels:
            extensions = [ext for ext in extensions if ext.trust_level in trust_levels]

        # Simple pagination (in production, use more sophisticated approach)
        total_count = len(extensions)
        start_idx = 0
        if page_token:
            try:
                start_idx = int(page_token)
            except ValueError:
                start_idx = 0

        end_idx = start_idx + page_size
        page_extensions = extensions[start_idx:end_idx]

        next_page_token = None
        if end_idx < total_count:
            next_page_token = str(end_idx)

        return page_extensions, next_page_token, total_count

    async def get_agent_extensions(self, agent_id: str) -> list[ExtensionInfo]:
        """Get all extensions used by a specific agent."""
        return [
            ext for ext in self._extensions.values() if agent_id in ext.declaring_agents
        ]

    async def update_agent_extensions(
        self, agent_id: str, extensions: list[dict]
    ) -> bool:
        """Update extensions for an agent."""
        # Remove agent from all current extensions
        await self.remove_agent_from_extensions(agent_id)

        # Add agent to new extensions
        for ext_data in extensions:
            uri = ext_data.get("uri", "")
            if not uri:
                continue

            # Check if extension is allowed in current mode
            if not config.is_extension_allowed(uri):
                logger.warning(f"Extension {uri} not allowed in current mode")
                continue

            existing_ext = await self.get_extension(uri)
            if existing_ext:
                existing_ext.add_declaring_agent(agent_id)
            else:
                # Create new extension info
                ext_info = ExtensionInfo(
                    uri=uri,
                    description=ext_data.get("description", ""),
                    required=ext_data.get("required", False),
                    params=ext_data.get("params", {}),
                    first_declared_by_agent=agent_id,
                    trust_level=config.get_default_trust_level(),
                )
                await self.store_extension(ext_info)

        return True

    async def remove_agent_from_extensions(self, agent_id: str) -> bool:
        """Remove agent from all extension declarations."""
        extensions_to_remove = []

        for uri, ext_info in self._extensions.items():
            ext_info.remove_declaring_agent(agent_id)
            # If no agents are using this extension anymore, remove it
            if ext_info.usage_count == 0:
                extensions_to_remove.append(uri)

        # Remove unused extensions
        for uri in extensions_to_remove:
            del self._extensions[uri]
            logger.info(f"Removed unused extension: {uri}")

        return True


class FileStorage(StorageBackend):
    """File-based persistent storage for agent registry."""

    def __init__(self, data_dir: str = "/data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.agents_file = self.data_dir / "agents.json"
        self.extensions_file = self.data_dir / "extensions.json"
        self._agents: dict[str, AgentCard] = {}
        self._extensions: dict[str, ExtensionInfo] = {}
        self._load_agents()
        self._load_extensions()

    def _load_agents(self) -> None:
        """Load agents from file."""
        try:
            if self.agents_file.exists():
                with open(self.agents_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self._agents = dict(data.items())
                logger.info(
                    f"Loaded {len(self._agents)} agents from {self.agents_file}"
                )
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

    def _load_extensions(self) -> None:
        """Load extensions from file."""
        try:
            if self.extensions_file.exists():
                with open(self.extensions_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self._extensions = {
                        uri: ExtensionInfo.from_dict(ext_data)
                        for uri, ext_data in data.items()
                    }
                logger.info(
                    f"Loaded {len(self._extensions)} extensions from {self.extensions_file}"
                )
        except Exception as e:
            logger.warning(f"Failed to load extensions from file: {e}")
            self._extensions = {}

    def _save_extensions(self) -> None:
        """Save extensions to file."""
        try:
            data = {uri: ext.to_dict() for uri, ext in self._extensions.items()}
            with open(self.extensions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(
                f"Saved {len(self._extensions)} extensions to {self.extensions_file}"
            )
        except Exception as e:
            logger.error(f"Failed to save extensions to file: {e}")

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

    # Extension-related methods (similar to InMemoryStorage but with file persistence)
    async def store_extension(self, extension_info: ExtensionInfo) -> bool:
        """Store extension information."""
        self._extensions[extension_info.uri] = extension_info
        self._save_extensions()
        logger.info(f"Stored extension: {extension_info.uri}")
        return True

    async def get_extension(self, uri: str) -> Optional[ExtensionInfo]:
        """Get extension information by URI."""
        return self._extensions.get(uri)

    async def list_extensions(
        self,
        uri_pattern: Optional[str] = None,
        declaring_agents: Optional[list[str]] = None,
        trust_levels: Optional[list[str]] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
    ) -> tuple[list[ExtensionInfo], Optional[str], int]:
        """List extensions with optional filtering and pagination."""
        extensions = list(self._extensions.values())

        # Apply filters
        if uri_pattern:
            extensions = [
                ext for ext in extensions if uri_pattern.lower() in ext.uri.lower()
            ]

        if declaring_agents:
            extensions = [
                ext
                for ext in extensions
                if any(agent in ext.declaring_agents for agent in declaring_agents)
            ]

        if trust_levels:
            extensions = [ext for ext in extensions if ext.trust_level in trust_levels]

        # Simple pagination
        total_count = len(extensions)
        start_idx = 0
        if page_token:
            try:
                start_idx = int(page_token)
            except ValueError:
                start_idx = 0

        end_idx = start_idx + page_size
        page_extensions = extensions[start_idx:end_idx]

        next_page_token = None
        if end_idx < total_count:
            next_page_token = str(end_idx)

        return page_extensions, next_page_token, total_count

    async def get_agent_extensions(self, agent_id: str) -> list[ExtensionInfo]:
        """Get all extensions used by a specific agent."""
        return [
            ext for ext in self._extensions.values() if agent_id in ext.declaring_agents
        ]

    async def update_agent_extensions(
        self, agent_id: str, extensions: list[dict]
    ) -> bool:
        """Update extensions for an agent."""
        # Remove agent from all current extensions
        await self.remove_agent_from_extensions(agent_id)

        # Add agent to new extensions
        for ext_data in extensions:
            uri = ext_data.get("uri", "")
            if not uri:
                continue

            # Check if extension is allowed in current mode
            if not config.is_extension_allowed(uri):
                logger.warning(f"Extension {uri} not allowed in current mode")
                continue

            existing_ext = await self.get_extension(uri)
            if existing_ext:
                existing_ext.add_declaring_agent(agent_id)
                self._save_extensions()  # Save after modification
            else:
                # Create new extension info
                ext_info = ExtensionInfo(
                    uri=uri,
                    description=ext_data.get("description", ""),
                    required=ext_data.get("required", False),
                    params=ext_data.get("params", {}),
                    first_declared_by_agent=agent_id,
                    trust_level=config.get_default_trust_level(),
                )
                await self.store_extension(ext_info)

        return True

    async def remove_agent_from_extensions(self, agent_id: str) -> bool:
        """Remove agent from all extension declarations."""
        extensions_to_remove = []
        modified = False

        for uri, ext_info in self._extensions.items():
            if agent_id in ext_info.declaring_agents:
                ext_info.remove_declaring_agent(agent_id)
                modified = True
                # If no agents are using this extension anymore, remove it
                if ext_info.usage_count == 0:
                    extensions_to_remove.append(uri)

        # Remove unused extensions
        for uri in extensions_to_remove:
            del self._extensions[uri]
            logger.info(f"Removed unused extension: {uri}")
            modified = True

        if modified:
            self._save_extensions()

        return True


def get_storage_backend() -> StorageBackend:
    """Get the appropriate storage backend based on environment configuration."""
    storage_type = config.storage_type
    data_dir = config.storage_data_dir

    if storage_type == "file":
        logger.info(f"Using file storage backend with data directory: {data_dir}")
        return FileStorage(data_dir)
    else:
        logger.info("Using in-memory storage backend")
        return InMemoryStorage()


# Global storage instance
storage = get_storage_backend()
