"""DataLoader implementations for optimizing N+1 queries in GraphQL resolvers."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from strawberry.dataloader import DataLoader

if TYPE_CHECKING:
    from .types import (
        AgentCard,
        AgentExtension,
        AgentExtensionRelation,
        CompatibilityInfo,
        ExtensionDependency,
        SecurityScan,
        UsageStatistics,
    )

logger = logging.getLogger(__name__)


class ExtensionDataLoader(DataLoader[str, Optional["AgentExtension"]]):
    """DataLoader for AgentExtension entities to prevent N+1 queries."""

    def __init__(self, extension_storage: Any) -> None:
        super().__init__(load_fn=self._load_extensions)
        self.extension_storage = extension_storage

    async def _load_extensions(
        self, extension_ids: list[str]
    ) -> list[Optional["AgentExtension"]]:
        """Batch load extensions by IDs."""
        try:
            # Fetch all extensions in a single batch operation
            extensions = await self.extension_storage.get_extensions_by_ids(
                extension_ids
            )

            # Create a lookup dictionary
            extension_dict = {ext.id: ext for ext in extensions}

            # Return extensions in the same order as requested IDs
            return [extension_dict.get(ext_id) for ext_id in extension_ids]

        except Exception as e:
            logger.error(f"Error loading extensions: {e}")
            # Return None for all requested IDs on error
            return [None] * len(extension_ids)


class AgentDataLoader(DataLoader[str, Optional["AgentCard"]]):
    """DataLoader for AgentCard entities."""

    def __init__(self, agent_storage: Any) -> None:
        super().__init__(load_fn=self._load_agents)
        self.agent_storage = agent_storage

    async def _load_agents(self, agent_ids: list[str]) -> list[Optional["AgentCard"]]:
        """Batch load agents by IDs."""
        try:
            agents = await self.agent_storage.get_agents_by_ids(agent_ids)
            agent_dict = {
                agent.name: agent for agent in agents
            }  # AgentCard uses 'name' as ID
            return [agent_dict.get(agent_id) for agent_id in agent_ids]

        except Exception as e:
            logger.error(f"Error loading agents: {e}")
            return [None] * len(agent_ids)


class DependencyDataLoader(DataLoader[str, list["ExtensionDependency"]]):
    """DataLoader for extension dependencies."""

    def __init__(self, extension_storage: Any) -> None:
        super().__init__(load_fn=self._load_dependencies)
        self.extension_storage = extension_storage

    async def _load_dependencies(
        self, extension_ids: list[str]
    ) -> list[list["ExtensionDependency"]]:
        """Batch load dependencies for multiple extensions."""
        try:
            # Fetch dependencies for all extensions in a single query
            dependencies_map = await self.extension_storage.get_dependencies_batch(
                extension_ids
            )

            # Return dependencies in the same order as requested IDs
            return [dependencies_map.get(ext_id, []) for ext_id in extension_ids]

        except Exception as e:
            logger.error(f"Error loading dependencies: {e}")
            return [[] for _ in extension_ids]


class UsageStatsDataLoader(DataLoader[str, "UsageStatistics"]):
    """DataLoader for extension usage statistics."""

    def __init__(self, analytics_service: Any) -> None:
        super().__init__(load_fn=self._load_usage_stats)
        self.analytics_service = analytics_service

    async def _load_usage_stats(
        self, extension_ids: list[str]
    ) -> list["UsageStatistics"]:
        """Batch load usage statistics for multiple extensions."""
        try:
            stats_map = await self.analytics_service.get_usage_stats_batch(
                extension_ids
            )

            # Create default stats for missing entries
            from .types import UsageStatistics

            default_stats = UsageStatistics(
                total_downloads=0,
                weekly_downloads=0,
                monthly_downloads=0,
                active_installations=0,
                review_count=0,
            )

            return [stats_map.get(ext_id, default_stats) for ext_id in extension_ids]

        except Exception as e:
            logger.error(f"Error loading usage statistics: {e}")
            from .types import UsageStatistics

            default_stats = UsageStatistics(
                total_downloads=0,
                weekly_downloads=0,
                monthly_downloads=0,
                active_installations=0,
                review_count=0,
            )
            return [default_stats] * len(extension_ids)


class AgentExtensionRelationDataLoader(DataLoader[str, list["AgentExtensionRelation"]]):
    """DataLoader for agent-extension relationships."""

    def __init__(self, extension_storage: Any) -> None:
        super().__init__(load_fn=self._load_relations)
        self.extension_storage = extension_storage

    async def _load_relations(
        self, extension_ids: list[str]
    ) -> list[list["AgentExtensionRelation"]]:
        """Batch load agent relations for multiple extensions."""
        try:
            relations_map = await self.extension_storage.get_extension_agents_batch(
                extension_ids
            )
            return [relations_map.get(ext_id, []) for ext_id in extension_ids]

        except Exception as e:
            logger.error(f"Error loading agent-extension relations: {e}")
            return [[] for _ in extension_ids]


class CompatibilityDataLoader(DataLoader[str, list["CompatibilityInfo"]]):
    """DataLoader for compatibility information."""

    def __init__(self, extension_storage: Any) -> None:
        super().__init__(load_fn=self._load_compatibility)
        self.extension_storage = extension_storage

    async def _load_compatibility(
        self, extension_ids: list[str]
    ) -> list[list["CompatibilityInfo"]]:
        """Batch load compatibility info for multiple extensions."""
        try:
            compat_map = await self.extension_storage.get_compatibility_info_batch(
                extension_ids
            )
            return [compat_map.get(ext_id, []) for ext_id in extension_ids]

        except Exception as e:
            logger.error(f"Error loading compatibility info: {e}")
            return [[] for _ in extension_ids]


class SecurityScanDataLoader(DataLoader[str, Optional["SecurityScan"]]):
    """DataLoader for security scan results."""

    def __init__(self, security_service: Any) -> None:
        super().__init__(load_fn=self._load_security_scans)
        self.security_service = security_service

    async def _load_security_scans(
        self, extension_ids: list[str]
    ) -> list[Optional["SecurityScan"]]:
        """Batch load latest security scans for multiple extensions."""
        try:
            scans_map = await self.security_service.get_latest_scans_batch(
                extension_ids
            )
            return [scans_map.get(ext_id) for ext_id in extension_ids]

        except Exception as e:
            logger.error(f"Error loading security scans: {e}")
            return [None] * len(extension_ids)


def create_data_loaders(context: dict[str, Any]) -> dict[str, Optional[DataLoader]]:
    """Create all DataLoader instances for the GraphQL context."""

    extension_storage = context["extension_storage"]
    agent_storage = context["agent_storage"]
    analytics_service = context.get("analytics_service")
    security_service = context.get("security_service")

    return {
        "extension_loader": ExtensionDataLoader(extension_storage),
        "agent_loader": AgentDataLoader(agent_storage),
        "dependency_loader": DependencyDataLoader(extension_storage),
        "usage_stats_loader": (
            UsageStatsDataLoader(analytics_service) if analytics_service else None
        ),
        "agent_extension_relation_loader": AgentExtensionRelationDataLoader(
            extension_storage
        ),
        "compatibility_loader": CompatibilityDataLoader(extension_storage),
        "security_scan_loader": (
            SecurityScanDataLoader(security_service) if security_service else None
        ),
    }


# Context manager for DataLoader lifecycle
class DataLoaderContext:
    """Context manager for handling DataLoader lifecycle in GraphQL requests."""

    def __init__(self, context: dict[str, Any]):
        self.context = context
        self.data_loaders = create_data_loaders(context)

    async def __aenter__(self) -> dict[str, Any]:
        # Add data loaders to context
        self.context.update(self.data_loaders)
        return self.context

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Clean up data loaders if needed
        for loader in self.data_loaders.values():
            if loader and hasattr(loader, "clear_all"):
                loader.clear_all()


# Utility function for field-level caching
def cache_field_result(cache_key: str, ttl_seconds: int = 300) -> Any:
    """Decorator for caching field resolver results."""

    def decorator(resolver_func: Any) -> Any:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache from context (Redis, in-memory, etc.)
            info = args[1] if len(args) > 1 else kwargs.get("info")
            if not info or "cache" not in info.context:
                return await resolver_func(*args, **kwargs)

            cache = info.context["cache"]

            # Try to get from cache first
            try:
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get error: {e}")

            # Execute resolver and cache result
            result = await resolver_func(*args, **kwargs)

            try:
                await cache.set(cache_key, result, ttl=ttl_seconds)
                logger.debug(f"Cached result for {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

            return result

        return wrapper

    return decorator
