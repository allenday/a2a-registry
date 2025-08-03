"""GraphQL resolvers for AgentExtension system."""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Optional

import strawberry

from .dataloaders import cache_field_result
from .pagination import create_connection
from .security import SecurityContext, check_permissions
from .types import (
    AgentCard,
    AgentExtension,
    AgentExtensionRelation,
    CompatibilityInfo,
    CreateExtensionInput,
    DependencyTree,
    ExtensionAnalytics,
    ExtensionConnection,
    ExtensionMutationResponse,
    ExtensionSearchInput,
    ExtensionSortInput,
    ExtensionUpdatedPayload,
    JSONType,
    PageInfo,
    SecurityAlertPayload,
    SecurityScan,
    UpdateExtensionInput,
    UsageStatistics,
)

logger = logging.getLogger(__name__)


@strawberry.type
class Query:
    """GraphQL Query root for AgentExtension system."""

    @strawberry.field
    async def extension(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> Optional[AgentExtension]:
        """Get a single extension by ID."""

        # Security check - field-level authorization
        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(security_ctx, "extension:read", resource_id=id):
            return None

        storage = info.context["extension_storage"]
        result = await storage.get_extension(id)
        if result is None:
            return None
        if not isinstance(result, AgentExtension):
            raise ValueError(
                f"Invalid extension data returned from storage: {type(result)}"
            )
        return result

    @strawberry.field
    async def extensions(
        self,
        info: strawberry.Info,
        search: Optional[ExtensionSearchInput] = None,
        sort: Optional[ExtensionSortInput] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> ExtensionConnection:
        """Search and paginate extensions."""

        # Security check
        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(security_ctx, "extension:list"):
            return ExtensionConnection(
                edges=[],
                page_info=PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    total_count=0,
                ),
            )

        storage = info.context["extension_storage"]

        # Apply security filters based on user permissions
        filtered_search = await apply_security_filters(security_ctx, search)

        # Execute search with pagination
        results = await storage.search_extensions(
            search=filtered_search,
            sort=sort,
            limit=first or last or 20,
            offset=after or before,
        )

        return create_connection(results, first, after, last, before)

    @strawberry.field
    @cache_field_result("dependency_tree_{extension_id}_{version}", ttl_seconds=600)
    async def resolve_dependencies(
        self,
        info: strawberry.Info,
        extension_id: strawberry.ID,
        version: Optional[str] = None,
    ) -> DependencyTree:
        """Resolve dependency tree for an extension."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(
            security_ctx, "extension:read", resource_id=extension_id
        ):
            raise Exception("Access denied")

        resolver = info.context["dependency_resolver"]
        result = await resolver.resolve_dependency_tree(extension_id, version)
        if not isinstance(result, DependencyTree):
            raise ValueError(f"Invalid dependency tree data returned: {type(result)}")
        return result

    @strawberry.field
    async def check_compatibility(
        self,
        info: strawberry.Info,
        extension_id: strawberry.ID,
        agent_id: strawberry.ID,
    ) -> list[CompatibilityInfo]:
        """Check compatibility between extension and agent."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(
            security_ctx, "extension:read", resource_id=extension_id
        ):
            return []

        compatibility_service = info.context["compatibility_service"]
        result = await compatibility_service.check_compatibility(extension_id, agent_id)
        if not isinstance(result, list):
            raise ValueError(f"Invalid compatibility data returned: {type(result)}")
        return result

    @strawberry.field
    @cache_field_result("extension_analytics_{time_range}", ttl_seconds=1800)
    async def extension_analytics(
        self, info: strawberry.Info, time_range: str = "30d"
    ) -> ExtensionAnalytics:
        """Get extension analytics and metrics."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(security_ctx, "analytics:read"):
            raise Exception("Access denied")

        analytics = info.context["analytics_service"]
        result = await analytics.get_extension_analytics(time_range)
        if not isinstance(result, ExtensionAnalytics):
            raise ValueError(f"Invalid analytics data returned: {type(result)}")
        return result

    @strawberry.field
    async def extension_usage(
        self,
        info: strawberry.Info,
        extension_id: strawberry.ID,
        time_range: str = "30d",
    ) -> UsageStatistics:
        """Get usage statistics for a specific extension."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(
            security_ctx, "extension:read", resource_id=extension_id
        ):
            raise Exception("Access denied")

        # Use DataLoader for optimized loading
        loader = info.context["usage_stats_loader"]
        result = await loader.load(extension_id)
        if result is None:
            raise ValueError(
                f"Usage statistics not found for extension: {extension_id}"
            )
        if not isinstance(result, UsageStatistics):
            raise ValueError(f"Invalid usage statistics data returned: {type(result)}")
        return result

    @strawberry.field
    async def security_scan(
        self, info: strawberry.Info, extension_id: strawberry.ID
    ) -> Optional[SecurityScan]:
        """Get latest security scan for an extension."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(
            security_ctx, "security:read", resource_id=extension_id
        ):
            return None

        loader = info.context["security_scan_loader"]
        result = await loader.load(extension_id)
        if result is not None and not isinstance(result, SecurityScan):
            raise ValueError(f"Invalid security scan data returned: {type(result)}")
        return result

    @strawberry.field
    async def security_scans(
        self, info: strawberry.Info, extension_id: strawberry.ID, limit: int = 10
    ) -> list[SecurityScan]:
        """Get security scan history for an extension."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(
            security_ctx, "security:read", resource_id=extension_id
        ):
            return []

        security_service = info.context["security_service"]
        result = await security_service.get_scan_history(extension_id, limit)
        if not isinstance(result, list):
            raise ValueError(f"Invalid scan history data returned: {type(result)}")
        return result

    @strawberry.field
    async def agent_extensions(
        self, info: strawberry.Info, agent_id: strawberry.ID
    ) -> list[AgentExtensionRelation]:
        """Get extensions installed on an agent."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(
            security_ctx, "agent:read", resource_id=agent_id
        ):
            return []

        storage = info.context["extension_storage"]
        result = await storage.get_agent_extensions(agent_id)
        if not isinstance(result, list):
            raise ValueError(f"Invalid agent extensions data returned: {type(result)}")
        return result

    @strawberry.field
    async def extension_agents(
        self, info: strawberry.Info, extension_id: strawberry.ID
    ) -> list[AgentExtensionRelation]:
        """Get agents using a specific extension."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(
            security_ctx, "extension:read", resource_id=extension_id
        ):
            return []

        # Use DataLoader for optimized loading
        loader = info.context["agent_extension_relation_loader"]
        result = await loader.load(extension_id)
        if not isinstance(result, list):
            raise ValueError(f"Invalid extension agents data returned: {type(result)}")
        return result

    @strawberry.field
    async def search_extensions(
        self, info: strawberry.Info, query: str, limit: int = 20
    ) -> list[AgentExtension]:
        """Full-text search for extensions."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(security_ctx, "extension:search"):
            return []

        search_service = info.context["search_service"]
        result = await search_service.full_text_search(query, limit, security_ctx)
        if not isinstance(result, list):
            raise ValueError(f"Invalid search results data returned: {type(result)}")
        return result

    @strawberry.field
    async def recommend_extensions(
        self, info: strawberry.Info, agent_id: strawberry.ID, limit: int = 10
    ) -> list[AgentExtension]:
        """Get recommended extensions for an agent."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(
            security_ctx, "agent:read", resource_id=agent_id
        ):
            return []

        recommendation_service = info.context["recommendation_service"]
        result = await recommendation_service.get_recommendations(agent_id, limit)
        if not isinstance(result, list):
            raise ValueError(f"Invalid recommendations data returned: {type(result)}")
        return result

    # Integration with existing agent system
    @strawberry.field
    async def agent(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> Optional[AgentCard]:
        """Get agent from existing system."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(security_ctx, "agent:read", resource_id=id):
            return None

        loader = info.context["agent_loader"]
        result = await loader.load(id)
        if result is not None and not isinstance(result, AgentCard):
            raise ValueError(f"Invalid agent data returned: {type(result)}")
        return result

    @strawberry.field
    async def agents(self, info: strawberry.Info) -> list[AgentCard]:
        """List all agents from existing system."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(security_ctx, "agent:list"):
            return []

        storage = info.context["agent_storage"]
        result = await storage.list_agents()
        if not isinstance(result, list):
            raise ValueError(f"Invalid agents list data returned: {type(result)}")
        return result


@strawberry.type
class Mutation:
    """GraphQL Mutation root for AgentExtension system."""

    @strawberry.mutation
    async def create_extension(
        self, info: strawberry.Info, input: CreateExtensionInput
    ) -> ExtensionMutationResponse:
        """Create a new extension."""

        security_ctx = SecurityContext.from_info(info)
        if not await check_permissions(security_ctx, "extension:create"):
            return ExtensionMutationResponse(
                success=False, errors=["Access denied: insufficient permissions"]
            )

        try:
            # Validate input
            validation_errors = await validate_extension_input(input, info.context)
            if validation_errors:
                return ExtensionMutationResponse(
                    success=False, errors=validation_errors
                )

            # Create extension
            storage = info.context["extension_storage"]
            extension = await storage.create_extension(input, security_ctx.user_id)

            # Audit log
            audit_service = info.context.get("audit_service")
            if audit_service:
                await audit_service.log_action(
                    user_id=security_ctx.user_id,
                    action="extension_created",
                    resource_id=extension.id,
                    metadata={"extension_name": extension.name},
                )

            # Trigger subscription
            subscription_manager = info.context.get("subscription_manager")
            if subscription_manager:
                await subscription_manager.publish(
                    "extension_updated",
                    ExtensionUpdatedPayload(extension=extension, change_type="created"),
                )

            return ExtensionMutationResponse(success=True, extension=extension)

        except Exception as e:
            logger.error(f"Error creating extension: {e}")
            return ExtensionMutationResponse(
                success=False, errors=[f"Internal error: {str(e)}"]
            )

    @strawberry.mutation
    async def update_extension(
        self, info: strawberry.Info, id: strawberry.ID, input: UpdateExtensionInput
    ) -> ExtensionMutationResponse:
        """Update an existing extension."""

        security_ctx = SecurityContext.from_info(info)

        # Check if user can modify this extension
        if not await check_permissions(
            security_ctx, "extension:update", resource_id=id
        ):
            return ExtensionMutationResponse(
                success=False, errors=["Access denied: cannot modify this extension"]
            )

        try:
            storage = info.context["extension_storage"]

            # Check if extension exists and user owns it
            existing_extension = await storage.get_extension(id)
            if not existing_extension:
                return ExtensionMutationResponse(
                    success=False, errors=["Extension not found"]
                )

            # Validate update input
            validation_errors = await validate_extension_update(
                input, existing_extension, info.context
            )
            if validation_errors:
                return ExtensionMutationResponse(
                    success=False, errors=validation_errors
                )

            # Update extension
            updated_extension = await storage.update_extension(
                id, input, security_ctx.user_id
            )

            # Audit log
            audit_service = info.context.get("audit_service")
            if audit_service:
                await audit_service.log_action(
                    user_id=security_ctx.user_id,
                    action="extension_updated",
                    resource_id=id,
                    metadata={"changes": input.__dict__},
                )

            # Trigger subscription
            subscription_manager = info.context.get("subscription_manager")
            if subscription_manager:
                await subscription_manager.publish(
                    "extension_updated",
                    ExtensionUpdatedPayload(
                        extension=updated_extension, change_type="updated"
                    ),
                )

            return ExtensionMutationResponse(success=True, extension=updated_extension)

        except Exception as e:
            logger.error(f"Error updating extension {id}: {e}")
            return ExtensionMutationResponse(
                success=False, errors=[f"Internal error: {str(e)}"]
            )

    @strawberry.mutation
    async def delete_extension(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> ExtensionMutationResponse:
        """Delete an extension."""

        security_ctx = SecurityContext.from_info(info)

        if not await check_permissions(
            security_ctx, "extension:delete", resource_id=id
        ):
            return ExtensionMutationResponse(
                success=False, errors=["Access denied: cannot delete this extension"]
            )

        try:
            storage = info.context["extension_storage"]

            # Get extension before deletion for audit
            extension = await storage.get_extension(id)
            if not extension:
                return ExtensionMutationResponse(
                    success=False, errors=["Extension not found"]
                )

            # Check for dependencies
            dependent_extensions = await storage.get_extensions_depending_on(id)
            if dependent_extensions:
                return ExtensionMutationResponse(
                    success=False,
                    errors=[
                        f"Cannot delete: {len(dependent_extensions)} extensions depend on it"
                    ],
                )

            # Delete extension
            success = await storage.delete_extension(id)

            if success:
                # Audit log
                audit_service = info.context.get("audit_service")
                if audit_service:
                    await audit_service.log_action(
                        user_id=security_ctx.user_id,
                        action="extension_deleted",
                        resource_id=id,
                        metadata={"extension_name": extension.name},
                    )

                # Trigger subscription
                subscription_manager = info.context.get("subscription_manager")
                if subscription_manager:
                    await subscription_manager.publish(
                        "extension_updated",
                        ExtensionUpdatedPayload(
                            extension=extension, change_type="deleted"
                        ),
                    )

                return ExtensionMutationResponse(success=True)
            else:
                return ExtensionMutationResponse(
                    success=False, errors=["Failed to delete extension"]
                )

        except Exception as e:
            logger.error(f"Error deleting extension {id}: {e}")
            return ExtensionMutationResponse(
                success=False, errors=[f"Internal error: {str(e)}"]
            )

    @strawberry.mutation
    async def publish_extension(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> ExtensionMutationResponse:
        """Publish an extension (make it available for public use)."""

        security_ctx = SecurityContext.from_info(info)

        if not await check_permissions(
            security_ctx, "extension:publish", resource_id=id
        ):
            return ExtensionMutationResponse(
                success=False, errors=["Access denied: cannot publish this extension"]
            )

        try:
            storage = info.context["extension_storage"]
            extension = await storage.get_extension(id)

            if not extension:
                return ExtensionMutationResponse(
                    success=False, errors=["Extension not found"]
                )

            # Validate extension before publishing
            validation_service = info.context["validation_service"]
            validation_result = await validation_service.validate_for_publishing(
                extension
            )

            if not validation_result.is_valid:
                return ExtensionMutationResponse(
                    success=False, errors=validation_result.errors
                )

            # Publish extension
            published_extension = await storage.publish_extension(
                id, security_ctx.user_id
            )

            # Trigger security scan
            security_service = info.context.get("security_service")
            if security_service:
                asyncio.create_task(security_service.scan_extension(id))

            return ExtensionMutationResponse(
                success=True, extension=published_extension
            )

        except Exception as e:
            logger.error(f"Error publishing extension {id}: {e}")
            return ExtensionMutationResponse(
                success=False, errors=[f"Internal error: {str(e)}"]
            )

    @strawberry.mutation
    async def install_extension(
        self,
        info: strawberry.Info,
        agent_id: strawberry.ID,
        extension_id: strawberry.ID,
        version: Optional[str] = None,
        configuration: Optional[JSONType] = None,
    ) -> bool:
        """Install an extension on an agent."""

        security_ctx = SecurityContext.from_info(info)

        if not await check_permissions(
            security_ctx, "agent:modify", resource_id=agent_id
        ):
            return False

        try:
            storage = info.context["extension_storage"]
            result = await storage.install_extension(
                agent_id, extension_id, version, configuration, security_ctx.user_id
            )
            return bool(result)
        except Exception as e:
            logger.error(
                f"Error installing extension {extension_id} on agent {agent_id}: {e}"
            )
            return False

    @strawberry.mutation
    async def uninstall_extension(
        self,
        info: strawberry.Info,
        agent_id: strawberry.ID,
        extension_id: strawberry.ID,
    ) -> bool:
        """Uninstall an extension from an agent."""

        security_ctx = SecurityContext.from_info(info)

        if not await check_permissions(
            security_ctx, "agent:modify", resource_id=agent_id
        ):
            return False

        try:
            storage = info.context["extension_storage"]
            result = await storage.uninstall_extension(
                agent_id, extension_id, security_ctx.user_id
            )
            return bool(result)
        except Exception as e:
            logger.error(
                f"Error uninstalling extension {extension_id} from agent {agent_id}: {e}"
            )
            return False


@strawberry.type
class Subscription:
    """GraphQL Subscription root for real-time updates."""

    @strawberry.subscription
    async def extension_updated(
        self, info: strawberry.Info, extension_id: Optional[strawberry.ID] = None
    ) -> AsyncIterator[ExtensionUpdatedPayload]:
        """Subscribe to extension updates."""

        security_ctx = SecurityContext.from_info(info)

        if not await check_permissions(security_ctx, "extension:subscribe"):
            return

        subscription_manager = info.context["subscription_manager"]
        async for update in subscription_manager.subscribe(
            "extension_updated", extension_id
        ):
            # Filter based on permissions
            if await check_permissions(
                security_ctx, "extension:read", resource_id=update.extension.id
            ):
                yield update

    @strawberry.subscription
    async def security_alert(
        self, info: strawberry.Info, extension_id: Optional[strawberry.ID] = None
    ) -> AsyncIterator[SecurityAlertPayload]:
        """Subscribe to security alerts."""

        security_ctx = SecurityContext.from_info(info)

        if not await check_permissions(security_ctx, "security:subscribe"):
            return

        subscription_manager = info.context["subscription_manager"]
        async for alert in subscription_manager.subscribe(
            "security_alert", extension_id
        ):
            # Filter based on permissions
            if await check_permissions(
                security_ctx, "extension:read", resource_id=alert.extension_id
            ):
                yield alert


# Helper functions
async def apply_security_filters(
    security_ctx: SecurityContext, search: Optional[ExtensionSearchInput]
) -> Optional[ExtensionSearchInput]:
    """Apply security filters to search input based on user permissions."""

    if not search:
        search = ExtensionSearchInput()

    # If user doesn't have admin permissions, filter out certain trust levels
    if not security_ctx.has_permission("admin"):
        allowed_trust_levels = ["community", "verified", "official"]
        if search.trust_levels:
            search.trust_levels = [
                tl for tl in search.trust_levels if tl.value in allowed_trust_levels
            ]
        else:
            from .types import TrustLevel

            search.trust_levels = [
                TrustLevel.COMMUNITY,
                TrustLevel.VERIFIED,
                TrustLevel.OFFICIAL,
            ]

    return search


async def validate_extension_input(
    input: CreateExtensionInput, context: dict
) -> list[str]:
    """Validate extension creation input."""
    errors = []

    # Basic validation
    if not input.name or len(input.name.strip()) < 3:
        errors.append("Extension name must be at least 3 characters")

    if not input.content.data:
        errors.append("Extension content cannot be empty")

    # Check for duplicate names
    storage = context["extension_storage"]
    existing = await storage.get_extension_by_name(input.name)
    if existing:
        errors.append(f"Extension with name '{input.name}' already exists")

    # Validate dependencies
    for dep in input.dependencies:
        dep_ext = await storage.get_extension(dep.extension_id)
        if not dep_ext:
            errors.append(f"Dependency extension '{dep.extension_id}' not found")

    return errors


async def validate_extension_update(
    input: UpdateExtensionInput, existing: AgentExtension, context: dict
) -> list[str]:
    """Validate extension update input."""
    errors = []

    # Check if name is being changed and conflicts
    if input.name and input.name != existing.name:
        storage = context["extension_storage"]
        existing_with_name = await storage.get_extension_by_name(input.name)
        if existing_with_name and existing_with_name.id != existing.id:
            errors.append(f"Extension with name '{input.name}' already exists")

    return errors
