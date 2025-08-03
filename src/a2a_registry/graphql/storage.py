"""Storage backend for AgentExtension entities."""

import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import strawberry

from .types import (
    AgentExtension,
    AgentExtensionRelation,
    CompatibilityInfo,
    CreateExtensionInput,
    ExtensionContent,
    ExtensionDependency,
    ExtensionSearchInput,
    ExtensionSortInput,
    ExtensionStatus,
    ExtensionType,
    TrustLevel,
    UpdateExtensionInput,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtensionEntity:
    """Internal storage entity for AgentExtension."""

    id: str
    version: str
    name: str
    description: Optional[str]
    type: str
    content: dict[str, Any]
    trust_level: str
    validation_status: str
    status: str
    tags: list[str]
    author: str
    license: Optional[str]
    homepage: Optional[str]
    repository: Optional[str]
    signature: Optional[str]
    checksum: str
    validated_at: Optional[datetime]
    validated_by: Optional[str]
    download_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    created_by: str
    updated_by: str
    dependencies: list[dict[str, Any]]


class ExtensionStorageBackend(ABC):
    """Abstract base class for AgentExtension storage backends."""

    @abstractmethod
    async def create_extension(
        self, input_data: CreateExtensionInput, user_id: str
    ) -> AgentExtension:
        """Create a new extension."""
        pass

    @abstractmethod
    async def get_extension(self, extension_id: str) -> Optional[AgentExtension]:
        """Get extension by ID."""
        pass

    @abstractmethod
    async def get_extension_by_name(self, name: str) -> Optional[AgentExtension]:
        """Get extension by name."""
        pass

    @abstractmethod
    async def get_extensions_by_ids(
        self, extension_ids: list[str]
    ) -> list[AgentExtension]:
        """Batch get extensions by IDs."""
        pass

    @abstractmethod
    async def update_extension(
        self, extension_id: str, input_data: UpdateExtensionInput, user_id: str
    ) -> AgentExtension:
        """Update an existing extension."""
        pass

    @abstractmethod
    async def delete_extension(self, extension_id: str) -> bool:
        """Delete an extension."""
        pass

    @abstractmethod
    async def publish_extension(
        self, extension_id: str, user_id: str
    ) -> AgentExtension:
        """Publish an extension."""
        pass

    @abstractmethod
    async def search_extensions(
        self,
        search: Optional[ExtensionSearchInput] = None,
        sort: Optional[ExtensionSortInput] = None,
        limit: int = 20,
        offset: Optional[str] = None,
    ) -> list[AgentExtension]:
        """Search extensions with filtering and sorting."""
        pass

    @abstractmethod
    async def count_extensions(self, search_params: dict[str, Any]) -> int:
        """Count extensions matching search criteria."""
        pass

    @abstractmethod
    async def get_dependencies(self, extension_id: str) -> list[ExtensionDependency]:
        """Get extension dependencies."""
        pass

    @abstractmethod
    async def get_dependencies_batch(
        self, extension_ids: list[str]
    ) -> dict[str, list[ExtensionDependency]]:
        """Batch get dependencies for multiple extensions."""
        pass

    @abstractmethod
    async def get_extension_agents(
        self, extension_id: str
    ) -> list[AgentExtensionRelation]:
        """Get agents using this extension."""
        pass

    @abstractmethod
    async def get_extension_agents_batch(
        self, extension_ids: list[str]
    ) -> dict[str, list[AgentExtensionRelation]]:
        """Batch get agent relations for multiple extensions."""
        pass

    @abstractmethod
    async def get_agent_extensions(self, agent_id: str) -> list[AgentExtensionRelation]:
        """Get extensions installed on an agent."""
        pass

    @abstractmethod
    async def install_extension(
        self,
        agent_id: str,
        extension_id: str,
        version: Optional[str],
        configuration: Optional[dict[str, Any]],
        user_id: str,
    ) -> bool:
        """Install extension on agent."""
        pass

    @abstractmethod
    async def uninstall_extension(
        self, agent_id: str, extension_id: str, user_id: str
    ) -> bool:
        """Uninstall extension from agent."""
        pass

    @abstractmethod
    async def get_compatibility_info(
        self, extension_id: str
    ) -> list[CompatibilityInfo]:
        """Get compatibility information for extension."""
        pass

    @abstractmethod
    async def get_compatibility_info_batch(
        self, extension_ids: list[str]
    ) -> dict[str, list[CompatibilityInfo]]:
        """Batch get compatibility info for multiple extensions."""
        pass

    @abstractmethod
    async def get_extensions_depending_on(
        self, extension_id: str
    ) -> list[AgentExtension]:
        """Get extensions that depend on this extension."""
        pass


class InMemoryExtensionStorage(ExtensionStorageBackend):
    """In-memory storage implementation for AgentExtensions."""

    def __init__(self) -> None:
        self._extensions: dict[str, ExtensionEntity] = {}
        self._extensions_by_name: dict[str, str] = {}  # name -> id mapping
        self._agent_extensions: dict[str, list[dict[str, Any]]] = (
            {}
        )  # agent_id -> relations
        self._extension_agents: dict[str, list[dict[str, Any]]] = (
            {}
        )  # extension_id -> relations
        self._dependencies: dict[str, list[dict[str, Any]]] = (
            {}
        )  # extension_id -> dependencies
        self._compatibility: dict[str, list[dict[str, Any]]] = (
            {}
        )  # extension_id -> compatibility

    async def create_extension(
        self, input_data: CreateExtensionInput, user_id: str
    ) -> AgentExtension:
        """Create a new extension."""

        # Generate ID and checksum
        extension_id = str(uuid.uuid4())
        content_str = json.dumps(input_data.content.data, sort_keys=True)
        checksum = hashlib.sha256(content_str.encode()).hexdigest()

        now = datetime.now(timezone.utc)

        # Create entity
        entity = ExtensionEntity(
            id=strawberry.ID(extension_id),
            version="1.0.0",  # Default version
            name=input_data.name,
            description=input_data.description,
            type=input_data.type.value,
            content=asdict(input_data.content),
            trust_level=TrustLevel.COMMUNITY.value,
            validation_status=ValidationStatus.PENDING.value,
            status=ExtensionStatus.DRAFT.value,
            tags=input_data.tags,
            author=user_id,
            license=input_data.license,
            homepage=input_data.homepage,
            repository=input_data.repository,
            signature=None,
            checksum=checksum,
            validated_at=None,
            validated_by=None,
            download_count=0,
            created_at=now,
            updated_at=now,
            published_at=None,
            created_by=user_id,
            updated_by=user_id,
            dependencies=[asdict(dep) for dep in input_data.dependencies],
        )

        # Store entity
        self._extensions[extension_id] = entity
        self._extensions_by_name[input_data.name] = extension_id

        # Store dependencies
        if input_data.dependencies:
            self._dependencies[extension_id] = [
                asdict(dep) for dep in input_data.dependencies
            ]

        return self._entity_to_graphql(entity)

    async def get_extension(self, extension_id: str) -> Optional[AgentExtension]:
        """Get extension by ID."""
        entity = self._extensions.get(extension_id)
        return self._entity_to_graphql(entity) if entity else None

    async def get_extension_by_name(self, name: str) -> Optional[AgentExtension]:
        """Get extension by name."""
        extension_id = self._extensions_by_name.get(name)
        if extension_id:
            return await self.get_extension(extension_id)
        return None

    async def get_extensions_by_ids(
        self, extension_ids: list[str]
    ) -> list[AgentExtension]:
        """Batch get extensions by IDs."""
        results = []
        for ext_id in extension_ids:
            entity = self._extensions.get(ext_id)
            if entity:
                results.append(self._entity_to_graphql(entity))
        return results

    async def update_extension(
        self, extension_id: str, input_data: UpdateExtensionInput, user_id: str
    ) -> AgentExtension:
        """Update an existing extension."""

        entity = self._extensions.get(extension_id)
        if not entity:
            raise ValueError(f"Extension {extension_id} not found")

        # Update fields
        if input_data.name:
            # Update name mapping
            if entity.name in self._extensions_by_name:
                del self._extensions_by_name[entity.name]
            entity.name = input_data.name
            self._extensions_by_name[input_data.name] = extension_id

        if input_data.description is not None:
            entity.description = input_data.description

        if input_data.content:
            entity.content = asdict(input_data.content)
            # Recalculate checksum
            content_str = json.dumps(input_data.content.data, sort_keys=True)
            entity.checksum = hashlib.sha256(content_str.encode()).hexdigest()

        if input_data.tags is not None:
            entity.tags = input_data.tags

        if input_data.license is not None:
            entity.license = input_data.license

        if input_data.homepage is not None:
            entity.homepage = input_data.homepage

        if input_data.repository is not None:
            entity.repository = input_data.repository

        if input_data.dependencies is not None:
            entity.dependencies = [asdict(dep) for dep in input_data.dependencies]
            self._dependencies[extension_id] = entity.dependencies

        entity.updated_at = datetime.now(timezone.utc)
        entity.updated_by = user_id

        return self._entity_to_graphql(entity)

    async def delete_extension(self, extension_id: str) -> bool:
        """Delete an extension."""
        entity = self._extensions.get(extension_id)
        if not entity:
            return False

        # Remove from name mapping
        if entity.name in self._extensions_by_name:
            del self._extensions_by_name[entity.name]

        # Remove extension
        del self._extensions[extension_id]

        # Clean up related data
        self._dependencies.pop(extension_id, None)
        self._extension_agents.pop(extension_id, None)
        self._compatibility.pop(extension_id, None)

        return True

    async def publish_extension(
        self, extension_id: str, user_id: str
    ) -> AgentExtension:
        """Publish an extension."""
        entity = self._extensions.get(extension_id)
        if not entity:
            raise ValueError(f"Extension {extension_id} not found")

        entity.status = ExtensionStatus.PUBLISHED.value
        entity.published_at = datetime.now(timezone.utc)
        entity.updated_by = user_id
        entity.updated_at = datetime.now(timezone.utc)

        return self._entity_to_graphql(entity)

    async def search_extensions(
        self,
        search: Optional[ExtensionSearchInput] = None,
        sort: Optional[ExtensionSortInput] = None,
        limit: int = 20,
        offset: Optional[str] = None,
    ) -> list[AgentExtension]:
        """Search extensions with filtering and sorting."""

        results = list(self._extensions.values())

        # Apply filters
        if search:
            if search.query:
                query_lower = search.query.lower()
                results = [
                    ext
                    for ext in results
                    if (
                        query_lower in ext.name.lower()
                        or (ext.description and query_lower in ext.description.lower())
                        or any(query_lower in tag.lower() for tag in ext.tags)
                    )
                ]

            if search.types:
                type_values = [t.value for t in search.types]
                results = [ext for ext in results if ext.type in type_values]

            if search.trust_levels:
                trust_values = [tl.value for tl in search.trust_levels]
                results = [ext for ext in results if ext.trust_level in trust_values]

            if search.tags:
                results = [
                    ext
                    for ext in results
                    if any(tag in ext.tags for tag in search.tags)
                ]

            if search.author:
                results = [ext for ext in results if ext.author == search.author]

            if search.min_downloads:
                results = [
                    ext for ext in results if ext.download_count >= search.min_downloads
                ]

            if search.published_after:
                results = [
                    ext
                    for ext in results
                    if ext.published_at and ext.published_at >= search.published_after
                ]

            if search.published_before:
                results = [
                    ext
                    for ext in results
                    if ext.published_at and ext.published_at <= search.published_before
                ]

        # Apply sorting
        if sort:
            reverse = sort.direction.value == "desc"

            if sort.field.value == "name":
                results.sort(key=lambda x: x.name, reverse=reverse)
            elif sort.field.value == "created_at":
                results.sort(key=lambda x: x.created_at, reverse=reverse)
            elif sort.field.value == "updated_at":
                results.sort(key=lambda x: x.updated_at, reverse=reverse)
            elif sort.field.value == "download_count":
                results.sort(key=lambda x: x.download_count, reverse=reverse)
            elif sort.field.value == "version":
                results.sort(key=lambda x: x.version, reverse=reverse)

        # Apply pagination
        start_idx = 0
        if offset:
            # In a real implementation, decode cursor to get start position
            pass

        results = results[start_idx : start_idx + limit]

        return [self._entity_to_graphql(entity) for entity in results]

    async def count_extensions(self, search_params: dict[str, Any]) -> int:
        """Count extensions matching search criteria."""
        # Simplified implementation
        return len(self._extensions)

    async def get_dependencies(self, extension_id: str) -> list[ExtensionDependency]:
        """Get extension dependencies."""
        deps_data = self._dependencies.get(extension_id, [])
        return [
            ExtensionDependency(
                extension_id=dep["extension_id"],
                version=dep["version"],
                optional=dep.get("optional", False),
            )
            for dep in deps_data
        ]

    async def get_dependencies_batch(
        self, extension_ids: list[str]
    ) -> dict[str, list[ExtensionDependency]]:
        """Batch get dependencies for multiple extensions."""
        result = {}
        for ext_id in extension_ids:
            result[ext_id] = await self.get_dependencies(ext_id)
        return result

    async def get_extension_agents(
        self, extension_id: str
    ) -> list[AgentExtensionRelation]:
        """Get agents using this extension."""
        relations_data = self._extension_agents.get(extension_id, [])
        return [
            AgentExtensionRelation(
                agent_id=strawberry.ID(rel["agent_id"]),
                extension_id=strawberry.ID(extension_id),
                installed_version=rel["installed_version"],
                installed_at=rel["installed_at"],
                last_used=rel.get("last_used"),
                usage_count=rel.get("usage_count", 0),
                configuration=rel.get("configuration"),
                status=rel.get("status", "active"),
            )
            for rel in relations_data
        ]

    async def get_extension_agents_batch(
        self, extension_ids: list[str]
    ) -> dict[str, list[AgentExtensionRelation]]:
        """Batch get agent relations for multiple extensions."""
        result = {}
        for ext_id in extension_ids:
            result[ext_id] = await self.get_extension_agents(ext_id)
        return result

    async def get_agent_extensions(self, agent_id: str) -> list[AgentExtensionRelation]:
        """Get extensions installed on an agent."""
        relations_data = self._agent_extensions.get(agent_id, [])
        return [
            AgentExtensionRelation(
                agent_id=strawberry.ID(agent_id),
                extension_id=strawberry.ID(rel["extension_id"]),
                installed_version=rel["installed_version"],
                installed_at=rel["installed_at"],
                last_used=rel.get("last_used"),
                usage_count=rel.get("usage_count", 0),
                configuration=rel.get("configuration"),
                status=rel.get("status", "active"),
            )
            for rel in relations_data
        ]

    async def install_extension(
        self,
        agent_id: str,
        extension_id: str,
        version: Optional[str],
        configuration: Optional[dict[str, Any]],
        user_id: str,
    ) -> bool:
        """Install extension on agent."""

        # Check if extension exists
        if extension_id not in self._extensions:
            return False

        entity = self._extensions[extension_id]
        install_version = version or entity.version

        relation_data = {
            "extension_id": extension_id,
            "installed_version": install_version,
            "installed_at": datetime.now(timezone.utc),
            "configuration": configuration,
            "usage_count": 0,
            "status": "active",
        }

        # Add to agent extensions
        if agent_id not in self._agent_extensions:
            self._agent_extensions[agent_id] = []

        # Check if already installed
        existing = next(
            (
                rel
                for rel in self._agent_extensions[agent_id]
                if rel["extension_id"] == extension_id
            ),
            None,
        )

        if existing:
            # Update existing installation
            existing.update(relation_data)
        else:
            self._agent_extensions[agent_id].append(relation_data)

        # Add to extension agents
        if extension_id not in self._extension_agents:
            self._extension_agents[extension_id] = []

        agent_relation = {
            "agent_id": agent_id,
            "installed_version": install_version,
            "installed_at": datetime.now(timezone.utc),
            "configuration": configuration,
            "usage_count": 0,
            "status": "active",
        }

        existing_agent = next(
            (
                rel
                for rel in self._extension_agents[extension_id]
                if rel["agent_id"] == agent_id
            ),
            None,
        )

        if existing_agent:
            existing_agent.update(agent_relation)
        else:
            self._extension_agents[extension_id].append(agent_relation)

        # Increment download count
        entity.download_count += 1

        return True

    async def uninstall_extension(
        self, agent_id: str, extension_id: str, user_id: str
    ) -> bool:
        """Uninstall extension from agent."""

        # Remove from agent extensions
        if agent_id in self._agent_extensions:
            self._agent_extensions[agent_id] = [
                rel
                for rel in self._agent_extensions[agent_id]
                if rel["extension_id"] != extension_id
            ]

        # Remove from extension agents
        if extension_id in self._extension_agents:
            self._extension_agents[extension_id] = [
                rel
                for rel in self._extension_agents[extension_id]
                if rel["agent_id"] != agent_id
            ]

        return True

    async def get_compatibility_info(
        self, extension_id: str
    ) -> list[CompatibilityInfo]:
        """Get compatibility information for extension."""
        compat_data = self._compatibility.get(extension_id, [])
        return [
            CompatibilityInfo(
                platform=comp["platform"],
                version=comp["version"],
                tested=comp["tested"],
                issues=comp.get("issues", []),
            )
            for comp in compat_data
        ]

    async def get_compatibility_info_batch(
        self, extension_ids: list[str]
    ) -> dict[str, list[CompatibilityInfo]]:
        """Batch get compatibility info for multiple extensions."""
        result = {}
        for ext_id in extension_ids:
            result[ext_id] = await self.get_compatibility_info(ext_id)
        return result

    async def get_extensions_depending_on(
        self, extension_id: str
    ) -> list[AgentExtension]:
        """Get extensions that depend on this extension."""
        dependents = []

        for entity in self._extensions.values():
            for dep in entity.dependencies:
                if dep.get("extension_id") == extension_id:
                    dependents.append(self._entity_to_graphql(entity))
                    break

        return dependents

    def _entity_to_graphql(self, entity: ExtensionEntity) -> AgentExtension:
        """Convert storage entity to GraphQL type."""

        return AgentExtension(
            id=strawberry.ID(entity.id),
            version=entity.version,
            name=entity.name,
            description=entity.description,
            type=ExtensionType(entity.type),
            content=ExtensionContent(**entity.content),
            trust_level=TrustLevel(entity.trust_level),
            validation_status=ValidationStatus(entity.validation_status),
            status=ExtensionStatus(entity.status),
            tags=entity.tags,
            author=entity.author,
            license=entity.license,
            homepage=entity.homepage,
            repository=entity.repository,
            signature=entity.signature,
            checksum=entity.checksum,
            validated_at=entity.validated_at,
            validated_by=entity.validated_by,
            download_count=entity.download_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            published_at=entity.published_at,
            created_by=strawberry.ID(entity.created_by),
            updated_by=strawberry.ID(entity.updated_by),
        )
