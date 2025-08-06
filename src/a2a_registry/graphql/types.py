"""GraphQL type definitions for AgentExtension system."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

import strawberry

# Type aliases for use in type annotations
JSONType = dict[str, Any]
SemVerType = str
IDType = str  # Strawberry ID type

# Scalars
SemVer = strawberry.scalar(str, name="SemVer")
JSON = strawberry.scalar(dict[str, Any], name="JSON")


# Enums
@strawberry.enum
class ExtensionType(Enum):
    AUTHENTICATION = "authentication"
    SCHEMA = "schema"
    ML_MODEL = "ml_model"
    BUSINESS_RULE = "business_rule"
    PROTOCOL_ADAPTER = "protocol_adapter"
    INTEGRATION = "integration"


@strawberry.enum
class TrustLevel(Enum):
    COMMUNITY = "community"
    VERIFIED = "verified"
    OFFICIAL = "official"
    DEPRECATED = "deprecated"


@strawberry.enum
class ValidationStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"
    EXPIRED = "expired"


@strawberry.enum
class ExtensionStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


@strawberry.enum
class SecurityScanResult(Enum):
    CLEAN = "clean"
    WARNINGS = "warnings"
    VULNERABILITIES = "vulnerabilities"
    MALICIOUS = "malicious"


@strawberry.enum
class ExtensionSortField(Enum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DOWNLOAD_COUNT = "download_count"
    POPULARITY_RANK = "popularity_rank"
    VERSION = "version"


@strawberry.enum
class SortDirection(Enum):
    ASC = "asc"
    DESC = "desc"


# Core Types
@strawberry.type
class ExtensionContent:
    format: str
    data: JSONType
    schema: str | None = None
    examples: list[JSONType] = strawberry.field(default_factory=list)
    documentation: str | None = None


@strawberry.type
class ExtensionDependency:
    extension_id: strawberry.ID
    version: str
    optional: bool = False

    @strawberry.field
    async def extension(self, info: Any) -> Optional["AgentExtension"]:
        """Resolve dependency extension using DataLoader."""
        loader = info.context["extension_loader"]
        result = await loader.load(self.extension_id)
        if result is not None and not isinstance(result, AgentExtension):
            raise ValueError(f"Invalid extension data from loader: {type(result)}")
        return result


@strawberry.type
class UsageStatistics:
    total_downloads: int
    weekly_downloads: int
    monthly_downloads: int
    active_installations: int
    popularity_rank: int | None = None
    last_used: datetime | None = None
    average_rating: float | None = None
    review_count: int = 0


@strawberry.type
class CompatibilityInfo:
    platform: str
    version: str
    tested: bool
    issues: list[str] = strawberry.field(default_factory=list)


@strawberry.type
class Skill:
    id: str
    name: str
    description: str | None = None


@strawberry.type
class AgentCard:
    name: str
    description: str
    version: str
    url: str
    protocol_version: str
    preferred_transport: str | None = None
    skills: list[Skill] = strawberry.field(default_factory=list)
    capabilities: list[str] = strawberry.field(default_factory=list)


@strawberry.type
class AgentExtensionRelation:
    agent_id: strawberry.ID
    extension_id: strawberry.ID
    installed_version: SemVerType
    installed_at: datetime
    last_used: datetime | None = None
    usage_count: int = 0
    configuration: JSONType | None = None
    status: str = "active"

    @strawberry.field
    async def agent(self, info: Any) -> AgentCard | None:
        """Resolve agent using DataLoader."""
        loader = info.context["agent_loader"]
        result = await loader.load(self.agent_id)
        if result is None:
            return None
        # Convert external AgentCard to our GraphQL AgentCard type
        if hasattr(result, "name") and hasattr(result, "description"):
            return AgentCard(
                name=result.name,
                description=result.description,
                version=getattr(result, "version", "1.0.0"),
                url=getattr(result, "url", ""),
                protocol_version=getattr(result, "protocol_version", "0.3.0"),
                preferred_transport=getattr(result, "preferred_transport", None),
                skills=getattr(result, "skills", []),
                capabilities=getattr(result, "capabilities", []),
            )
        raise ValueError(f"Invalid agent data from loader: {type(result)}")

    @strawberry.field
    async def extension(self, info: Any) -> Optional["AgentExtension"]:
        """Resolve extension using DataLoader."""
        loader = info.context["extension_loader"]
        result = await loader.load(self.extension_id)
        if result is not None and not isinstance(result, AgentExtension):
            raise ValueError(f"Invalid extension data from loader: {type(result)}")
        return result


@strawberry.type
class Vulnerability:
    id: str
    severity: str
    description: str
    cve_id: str | None = None
    fixed_in: str | None = None


@strawberry.type
class SecurityScan:
    extension_id: strawberry.ID
    scan_type: str
    result: SecurityScanResult
    vulnerabilities: list[Vulnerability]
    scan_date: datetime
    scanner: str


@strawberry.type
class AgentExtension:
    id: strawberry.ID
    version: SemVerType
    name: str
    type: ExtensionType
    content: ExtensionContent
    trust_level: TrustLevel
    validation_status: ValidationStatus
    status: ExtensionStatus

    # Metadata
    description: str | None = None
    tags: list[str] = strawberry.field(default_factory=list)
    author: str = "unknown"
    license: str | None = None
    homepage: str | None = None
    repository: str | None = None

    # Security
    signature: str | None = None
    checksum: str = ""
    validated_at: datetime | None = None
    validated_by: str | None = None

    # Analytics
    download_count: int = 0

    # Audit
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    created_by: strawberry.ID
    updated_by: strawberry.ID

    @strawberry.field
    async def dependencies(self, info: Any) -> list[ExtensionDependency]:
        """Get extension dependencies."""
        storage = info.context["extension_storage"]
        result = await storage.get_dependencies(self.id)
        if not isinstance(result, list):
            raise ValueError(f"Invalid dependencies data from storage: {type(result)}")
        return result

    @strawberry.field
    async def agents(self, info: Any) -> list[AgentExtensionRelation]:
        """Get agents using this extension."""
        storage = info.context["extension_storage"]
        result = await storage.get_extension_agents(self.id)
        if not isinstance(result, list):
            raise ValueError(
                f"Invalid extension agents data from storage: {type(result)}"
            )
        return result

    @strawberry.field
    async def usage_stats(self, info: Any) -> UsageStatistics:
        """Get usage statistics for this extension."""
        analytics = info.context["analytics_service"]
        result = await analytics.get_usage_stats(self.id)
        if not isinstance(result, UsageStatistics):
            raise ValueError(
                f"Invalid usage statistics data from analytics: {type(result)}"
            )
        return result

    @strawberry.field
    async def compatibility(self, info: Any) -> list[CompatibilityInfo]:
        """Get compatibility information."""
        storage = info.context["extension_storage"]
        result = await storage.get_compatibility_info(self.id)
        if not isinstance(result, list):
            raise ValueError(
                f"Invalid compatibility info data from storage: {type(result)}"
            )
        return result


# Pagination Types
@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None = None
    end_cursor: str | None = None
    total_count: int = 0


@strawberry.type
class ExtensionEdge:
    node: AgentExtension
    cursor: str


@strawberry.type
class ExtensionConnection:
    edges: list[ExtensionEdge]
    page_info: PageInfo


# Analytics Types
@strawberry.type
class TypeCount:
    type: ExtensionType
    count: int


@strawberry.type
class TrustLevelCount:
    trust_level: TrustLevel
    count: int


@strawberry.type
class ExtensionAnalytics:
    total_extensions: int
    total_downloads: int
    extensions_by_type: list[TypeCount]
    extensions_by_trust_level: list[TrustLevelCount]
    top_extensions: list[AgentExtension]
    recent_extensions: list[AgentExtension]
    trending_extensions: list[AgentExtension]


# Dependency Resolution Types
@strawberry.type
class DependencyConflict:
    dependency: str
    required_versions: list[str]
    resolution: str | None = None


@strawberry.type
class DependencyNode:
    extension: AgentExtension | None
    required_version: str
    children: list["DependencyNode"] = strawberry.field(default_factory=list)


@strawberry.type
class DependencyTree:
    extension: AgentExtension
    dependencies: list[DependencyNode]
    conflicts: list[DependencyConflict]


# Input Types
@strawberry.input
class ExtensionContentInput:
    format: str
    data: JSONType
    schema: str | None = None
    examples: list[JSONType] = strawberry.field(default_factory=list)
    documentation: str | None = None


@strawberry.input
class ExtensionDependencyInput:
    extension_id: strawberry.ID
    version: str
    optional: bool = False


@strawberry.input
class CreateExtensionInput:
    name: str
    type: ExtensionType
    content: ExtensionContentInput
    description: str | None = None
    tags: list[str] = strawberry.field(default_factory=list)
    license: str | None = None
    homepage: str | None = None
    repository: str | None = None
    dependencies: list[ExtensionDependencyInput] = strawberry.field(
        default_factory=list
    )


@strawberry.input
class UpdateExtensionInput:
    name: str | None = None
    description: str | None = None
    content: ExtensionContentInput | None = None
    tags: list[str] | None = None
    license: str | None = None
    homepage: str | None = None
    repository: str | None = None
    dependencies: list[ExtensionDependencyInput] | None = None


@strawberry.input
class ExtensionSearchInput:
    query: str | None = None
    types: list[ExtensionType] | None = None
    trust_levels: list[TrustLevel] | None = None
    tags: list[str] | None = None
    author: str | None = None
    min_downloads: int | None = None
    compatible_with: str | None = None
    depends_on: list[strawberry.ID] | None = None
    has_valid_signature: bool | None = None
    published_after: datetime | None = None
    published_before: datetime | None = None


@strawberry.input
class ExtensionSortInput:
    field: ExtensionSortField
    direction: SortDirection = SortDirection.ASC


# Mutation Response Types
@strawberry.type
class ExtensionMutationResponse:
    success: bool
    extension: AgentExtension | None = None
    errors: list[str] = strawberry.field(default_factory=list)


# Subscription Payload Types
@strawberry.type
class ExtensionUpdatedPayload:
    extension: AgentExtension
    change_type: str  # "created", "updated", "deleted", "status_changed"


@strawberry.type
class SecurityAlertPayload:
    extension_id: strawberry.ID
    alert_type: str
    severity: str
    message: str
    scan_result: SecurityScan | None = None
