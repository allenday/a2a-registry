"""Supporting services for GraphQL AgentExtension system."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import strawberry

from .types import (
    DependencyConflict,
    DependencyNode,
    DependencyTree,
    ExtensionAnalytics,
    ExtensionType,
    SecurityScan,
    SecurityScanResult,
    TrustLevel,
    TrustLevelCount,
    TypeCount,
    UsageStatistics,
    Vulnerability,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of extension validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


class AnalyticsService:
    """Service for extension analytics and usage statistics."""

    def __init__(self, extension_storage: Any) -> None:
        self.storage = extension_storage
        self._analytics_cache: dict[str, tuple[ExtensionAnalytics, datetime]] = {}
        self._usage_stats_cache: dict[str, tuple[UsageStatistics, datetime]] = {}

    async def get_extension_analytics(
        self, time_range: str = "30d"
    ) -> ExtensionAnalytics:
        """Get comprehensive extension analytics."""

        cache_key = f"analytics_{time_range}"
        if cache_key in self._analytics_cache:
            cached_result, cache_time = self._analytics_cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=1):
                return cached_result

        # Get all extensions for analysis
        all_extensions = await self.storage.search_extensions(limit=1000)

        # Calculate metrics
        total_extensions = len(all_extensions)
        total_downloads = sum(ext.download_count for ext in all_extensions)

        # Extensions by type
        type_counts: dict[str, int] = {}
        for ext in all_extensions:
            type_name = ext.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        extensions_by_type = [
            TypeCount(type=ExtensionType(ext_type), count=count)
            for ext_type, count in type_counts.items()
        ]

        # Extensions by trust level
        trust_counts: dict[str, int] = {}
        for ext in all_extensions:
            trust_level = ext.trust_level.value
            trust_counts[trust_level] = trust_counts.get(trust_level, 0) + 1

        extensions_by_trust_level = [
            TrustLevelCount(trust_level=TrustLevel(trust_level), count=count)
            for trust_level, count in trust_counts.items()
        ]

        # Top extensions by download count
        top_extensions = sorted(
            all_extensions, key=lambda x: x.download_count, reverse=True
        )[:10]

        # Recent extensions (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_extensions = [
            ext for ext in all_extensions if ext.created_at >= thirty_days_ago
        ]
        recent_extensions.sort(key=lambda x: x.created_at, reverse=True)
        recent_extensions = recent_extensions[:10]

        # Trending extensions (high recent downloads)
        trending_extensions = sorted(
            all_extensions, key=lambda x: (x.download_count, x.created_at), reverse=True
        )[:10]

        result = ExtensionAnalytics(
            total_extensions=total_extensions,
            total_downloads=total_downloads,
            extensions_by_type=extensions_by_type,
            extensions_by_trust_level=extensions_by_trust_level,
            top_extensions=top_extensions,
            recent_extensions=recent_extensions,
            trending_extensions=trending_extensions,
        )

        # Cache result
        self._analytics_cache[cache_key] = (result, datetime.now())

        return result

    async def get_usage_stats(self, extension_id: str) -> UsageStatistics:
        """Get usage statistics for a specific extension."""

        if extension_id in self._usage_stats_cache:
            cached_stats, cache_time = self._usage_stats_cache[extension_id]
            if datetime.now() - cache_time < timedelta(minutes=15):
                return cached_stats

        # Get extension
        extension = await self.storage.get_extension(extension_id)
        if not extension:
            return UsageStatistics(
                total_downloads=0,
                weekly_downloads=0,
                monthly_downloads=0,
                active_installations=0,
                review_count=0,
            )

        # Get agent relations to calculate active installations
        agent_relations = await self.storage.get_extension_agents(extension_id)
        active_installations = len(
            [rel for rel in agent_relations if rel.status == "active"]
        )

        # Calculate download trends (simplified - in reality, track daily downloads)
        total_downloads = extension.download_count
        weekly_downloads = max(0, total_downloads // 10)  # Rough estimate
        monthly_downloads = max(0, total_downloads // 3)  # Rough estimate

        # Calculate popularity rank (position among all extensions by downloads)
        all_extensions = await self.storage.search_extensions(limit=1000)
        sorted_by_downloads = sorted(
            all_extensions, key=lambda x: x.download_count, reverse=True
        )
        popularity_rank = next(
            (
                i + 1
                for i, ext in enumerate(sorted_by_downloads)
                if ext.id == extension_id
            ),
            None,
        )

        # Last used timestamp
        last_used = None
        if agent_relations:
            last_used_times = [
                rel.last_used for rel in agent_relations if rel.last_used
            ]
            if last_used_times:
                last_used = max(last_used_times)

        stats = UsageStatistics(
            total_downloads=total_downloads,
            weekly_downloads=weekly_downloads,
            monthly_downloads=monthly_downloads,
            active_installations=active_installations,
            popularity_rank=popularity_rank,
            last_used=last_used,
            average_rating=4.2,  # Mock rating
            review_count=len(agent_relations),  # Use installations as proxy for reviews
        )

        # Cache stats
        self._usage_stats_cache[extension_id] = (stats, datetime.now())

        return stats

    async def get_usage_stats_batch(
        self, extension_ids: list[str]
    ) -> dict[str, UsageStatistics]:
        """Batch get usage statistics for multiple extensions."""

        results = {}
        for ext_id in extension_ids:
            results[ext_id] = await self.get_usage_stats(ext_id)

        return results


class SecurityService:
    """Service for extension security scanning and validation."""

    def __init__(self) -> None:
        self._scan_cache: dict[str, tuple[SecurityScan, datetime]] = {}
        self._vulnerability_db = self._load_vulnerability_db()

    def _load_vulnerability_db(self) -> dict[str, list[dict[str, Any]]]:
        """Load vulnerability database (mock implementation)."""
        return {
            "known_malicious_patterns": [
                {
                    "pattern": "eval(",
                    "severity": "high",
                    "description": "Code injection risk",
                },
                {
                    "pattern": "exec(",
                    "severity": "high",
                    "description": "Code execution risk",
                },
                {
                    "pattern": "__import__",
                    "severity": "medium",
                    "description": "Dynamic imports",
                },
            ],
            "suspicious_domains": [
                {"domain": "malicious-domain.com", "severity": "high"},
                {"domain": "suspicious-site.net", "severity": "medium"},
            ],
        }

    async def scan_extension(self, extension_id: str) -> SecurityScan:
        """Perform security scan on an extension."""

        if extension_id in self._scan_cache:
            cached_scan, cache_time = self._scan_cache[extension_id]
            if datetime.now() - cache_time < timedelta(hours=24):
                return cached_scan

        # Get extension for scanning

        # This would be injected in real implementation

        scan_result = SecurityScanResult.CLEAN

        # Mock vulnerability scanning
        mock_vulnerabilities = [
            Vulnerability(
                id="CVE-2024-0001",
                severity="medium",
                description="Potential XSS vulnerability in extension content",
                cve_id="CVE-2024-0001",
                fixed_in="1.1.0",
            )
        ]

        # Determine scan result based on vulnerabilities
        if any(v.severity == "high" for v in mock_vulnerabilities):
            scan_result = SecurityScanResult.VULNERABILITIES
        elif any(v.severity == "medium" for v in mock_vulnerabilities):
            scan_result = SecurityScanResult.WARNINGS
        elif mock_vulnerabilities:
            scan_result = SecurityScanResult.WARNINGS

        scan = SecurityScan(
            extension_id=strawberry.ID(extension_id),
            scan_type="static_analysis",
            result=scan_result,
            vulnerabilities=mock_vulnerabilities,
            scan_date=datetime.now(),
            scanner="A2A Security Scanner v1.0",
        )

        # Cache scan result
        self._scan_cache[extension_id] = (scan, datetime.now())

        return scan

    async def get_latest_scans_batch(
        self, extension_ids: list[str]
    ) -> dict[str, Optional[SecurityScan]]:
        """Batch get latest security scans for multiple extensions."""

        results: dict[str, Optional[SecurityScan]] = {}
        for ext_id in extension_ids:
            try:
                results[ext_id] = await self.scan_extension(ext_id)
            except Exception as e:
                logger.error(f"Error scanning extension {ext_id}: {e}")
                results[ext_id] = None

        return results

    async def get_scan_history(
        self, extension_id: str, limit: int = 10
    ) -> list[SecurityScan]:
        """Get security scan history for an extension."""

        # Mock implementation - return recent scans with different dates
        base_scan = await self.scan_extension(extension_id)
        history = []

        for i in range(min(limit, 5)):  # Mock 5 historical scans
            scan_date = datetime.now() - timedelta(days=i * 7)  # Weekly scans
            historical_scan = SecurityScan(
                extension_id=strawberry.ID(extension_id),
                scan_type=base_scan.scan_type,
                result=base_scan.result,
                vulnerabilities=base_scan.vulnerabilities,
                scan_date=scan_date,
                scanner=base_scan.scanner,
            )
            history.append(historical_scan)

        return history


class DependencyResolverService:
    """Service for resolving extension dependencies."""

    def __init__(self, extension_storage: Any) -> None:
        self.storage = extension_storage

    async def resolve_dependency_tree(
        self, extension_id: str, version: Optional[str] = None
    ) -> DependencyTree:
        """Resolve complete dependency tree for an extension."""

        extension = await self.storage.get_extension(extension_id)
        if not extension:
            raise ValueError(f"Extension {extension_id} not found")

        # Get direct dependencies
        dependencies = await self.storage.get_dependencies(extension_id)

        # Resolve dependency nodes recursively
        dependency_nodes = []
        conflicts = []

        for dep in dependencies:
            node = await self._resolve_dependency_node(dep, {extension_id})
            dependency_nodes.append(node)

        # Check for conflicts
        conflicts = await self._detect_conflicts(dependency_nodes)

        return DependencyTree(
            extension=extension, dependencies=dependency_nodes, conflicts=conflicts
        )

    async def _resolve_dependency_node(
        self, dependency: Any, visited: set[str], depth: int = 0
    ) -> DependencyNode:
        """Recursively resolve a dependency node."""

        if depth > 10:  # Prevent infinite recursion
            logger.warning(
                f"Dependency resolution depth limit reached for {dependency.extension_id}"
            )
            return DependencyNode(
                extension=None, required_version=dependency.version, children=[]
            )

        if dependency.extension_id in visited:
            # Circular dependency detected
            logger.warning(f"Circular dependency detected: {dependency.extension_id}")
            return DependencyNode(
                extension=None, required_version=dependency.version, children=[]
            )

        # Get dependency extension
        dep_extension = await self.storage.get_extension(dependency.extension_id)
        if not dep_extension:
            return DependencyNode(
                extension=None, required_version=dependency.version, children=[]
            )

        # Add to visited set
        visited.add(dependency.extension_id)

        # Get dependencies of this dependency
        sub_dependencies = await self.storage.get_dependencies(dependency.extension_id)

        # Resolve child nodes
        children = []
        for sub_dep in sub_dependencies:
            child_node = await self._resolve_dependency_node(
                sub_dep, visited.copy(), depth + 1
            )
            children.append(child_node)

        return DependencyNode(
            extension=dep_extension,
            required_version=dependency.version,
            children=children,
        )

    async def _detect_conflicts(
        self, dependency_nodes: list[DependencyNode]
    ) -> list[DependencyConflict]:
        """Detect version conflicts in dependency tree."""

        conflicts = []
        version_map: dict[str, list[str]] = (
            {}
        )  # extension_id -> list of required versions

        def collect_versions(nodes: list[DependencyNode]) -> None:
            for node in nodes:
                if node.extension:
                    ext_id = node.extension.id
                    if ext_id not in version_map:
                        version_map[ext_id] = []
                    version_map[ext_id].append(node.required_version)

                    # Recursively collect from children
                    collect_versions(node.children)

        collect_versions(dependency_nodes)

        # Check for conflicts (simplified version comparison)
        for ext_id, versions in version_map.items():
            unique_versions = list(set(versions))
            if len(unique_versions) > 1:
                conflicts.append(
                    DependencyConflict(
                        dependency=ext_id,
                        required_versions=unique_versions,
                        resolution=f"Use version {unique_versions[0]}",  # Simple resolution
                    )
                )

        return conflicts


class CompatibilityService:
    """Service for checking extension compatibility."""

    def __init__(self, extension_storage: Any) -> None:
        self.storage = extension_storage

    async def check_compatibility(self, extension_id: str, agent_id: str) -> list[Any]:
        """Check compatibility between extension and agent."""

        # Get extension compatibility info
        await self.storage.get_compatibility_info(extension_id)

        # In a real implementation, get agent platform info and compare
        # For now, return mock compatibility info
        from .types import CompatibilityInfo

        mock_compatibility = [
            CompatibilityInfo(
                platform="python", version="3.9+", tested=True, issues=[]
            ),
            CompatibilityInfo(
                platform="a2a-protocol", version="0.3.0", tested=True, issues=[]
            ),
        ]

        return mock_compatibility


class RecommendationService:
    """Service for extension recommendations."""

    def __init__(self, extension_storage: Any) -> None:
        self.storage = extension_storage
        self._recommendation_cache: dict[str, tuple[list[Any], datetime]] = {}

    async def get_recommendations(self, agent_id: str, limit: int = 10) -> list[Any]:
        """Get recommended extensions for an agent."""

        cache_key = f"recommendations_{agent_id}"
        if cache_key in self._recommendation_cache:
            cached_recs, cache_time = self._recommendation_cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=4):
                return cached_recs[:limit]

        # Get agent's current extensions
        current_extensions = await self.storage.get_agent_extensions(agent_id)
        current_ext_ids = {rel.extension_id for rel in current_extensions}

        # Get all extensions
        all_extensions = await self.storage.search_extensions(limit=1000)

        # Filter out already installed extensions
        available_extensions = [
            ext for ext in all_extensions if ext.id not in current_ext_ids
        ]

        # Score extensions based on:
        # 1. Download count (popularity)
        # 2. Trust level
        # 3. Complementary types
        scored_extensions = []

        for ext in available_extensions:
            score = 0

            # Popularity score (normalized)
            max_downloads = max((e.download_count for e in all_extensions), default=1)
            popularity_score = (ext.download_count / max_downloads) * 40
            score += popularity_score

            # Trust level score
            trust_scores = {
                "official": 30,
                "verified": 20,
                "community": 10,
                "deprecated": 0,
            }
            score += trust_scores.get(ext.trust_level.value, 0)

            # Type diversity bonus
            current_types = {
                rel.extension.type.value for rel in current_extensions if rel.extension
            }
            if ext.type.value not in current_types:
                score += 15

            # Recently updated bonus
            if ext.updated_at and (datetime.now() - ext.updated_at).days < 30:
                score += 10

            scored_extensions.append((ext, score))

        # Sort by score and return top recommendations
        scored_extensions.sort(key=lambda x: x[1], reverse=True)
        recommendations = [ext for ext, score in scored_extensions[: limit * 2]]

        # Cache recommendations
        self._recommendation_cache[cache_key] = (recommendations, datetime.now())

        return recommendations[:limit]


class ValidationService:
    """Service for validating extensions before publishing."""

    def __init__(self) -> None:
        self.security_service = SecurityService()

    async def validate_for_publishing(self, extension: Any) -> ValidationResult:
        """Validate extension for publishing."""

        errors = []
        warnings = []

        # Basic validation
        if not extension.name or len(extension.name.strip()) < 3:
            errors.append("Extension name must be at least 3 characters")

        if not extension.description or len(extension.description.strip()) < 20:
            warnings.append("Extension description should be at least 20 characters")

        if not extension.content or not extension.content.data:
            errors.append("Extension content cannot be empty")

        # Security validation
        try:
            security_scan = await self.security_service.scan_extension(extension.id)

            if security_scan.result == SecurityScanResult.MALICIOUS:
                errors.append(
                    "Extension failed security scan: malicious content detected"
                )
            elif security_scan.result == SecurityScanResult.VULNERABILITIES:
                high_vulns = [
                    v for v in security_scan.vulnerabilities if v.severity == "high"
                ]
                if high_vulns:
                    errors.append(
                        f"Extension has {len(high_vulns)} high-severity vulnerabilities"
                    )
                else:
                    warnings.append("Extension has security vulnerabilities")
            elif security_scan.result == SecurityScanResult.WARNINGS:
                warnings.append("Extension has security warnings")

        except Exception as e:
            warnings.append(f"Could not complete security scan: {e}")

        # Content validation
        if extension.content and extension.content.data:
            content_str = str(extension.content.data).lower()

            # Check for potentially dangerous patterns
            dangerous_patterns = ["eval(", "exec(", "import os", "subprocess"]
            found_patterns = [p for p in dangerous_patterns if p in content_str]

            if found_patterns:
                warnings.append(
                    f"Potentially dangerous patterns found: {', '.join(found_patterns)}"
                )

        # Metadata validation
        if not extension.license:
            warnings.append("Consider adding a license to your extension")

        if not extension.repository:
            warnings.append("Consider adding a repository URL for transparency")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
