"""Security middleware and authorization for GraphQL API."""

import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional

import jwt

logger = logging.getLogger(__name__)


class SecurityContext:
    """Security context containing user information and permissions."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        roles: Optional[list[str]] = None,
        permissions: Optional[set[str]] = None,
        is_authenticated: bool = False,
        auth_method: str = "none",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        self.user_id = user_id
        self.roles = roles or []
        self.permissions = permissions or set()
        self.is_authenticated = is_authenticated
        self.auth_method = auth_method
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_id = None

    @classmethod
    def from_info(cls, info: Any) -> "SecurityContext":
        """Extract security context from GraphQL info object."""
        context = info.context
        result = context.get("security_context", cls())
        if not isinstance(result, cls):
            raise ValueError(
                f"Invalid security context: expected {cls.__name__}, got {type(result)}"
            )
        return result

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)


class AuthenticationError(Exception):
    """Authentication-related errors."""

    pass


class AuthorizationError(Exception):
    """Authorization-related errors."""

    pass


class SecurityMiddleware:
    """GraphQL security middleware for authentication and authorization."""

    def __init__(
        self,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        rate_limit_per_minute: int = 1000,
        enable_query_complexity_analysis: bool = True,
        max_query_complexity: int = 1000,
        max_query_depth: int = 15,
    ):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.rate_limit_per_minute = rate_limit_per_minute
        self.enable_query_complexity_analysis = enable_query_complexity_analysis
        self.max_query_complexity = max_query_complexity
        self.max_query_depth = max_query_depth

        # Rate limiting storage (in production, use Redis)
        self.rate_limit_storage: dict[str, int] = {}

    async def authenticate_request(self, request: Any) -> SecurityContext:
        """Authenticate incoming GraphQL request."""

        # Extract authentication token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return SecurityContext()  # Unauthenticated context

        token = auth_header.split(" ", 1)[1]

        try:
            # Decode JWT token
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            user_id = payload.get("sub")
            roles = payload.get("roles", [])
            permissions = set(payload.get("permissions", []))

            # Additional security checks
            if payload.get("exp", 0) < datetime.utcnow().timestamp():
                raise AuthenticationError("Token expired")

            return SecurityContext(
                user_id=user_id,
                roles=roles,
                permissions=permissions,
                is_authenticated=True,
                auth_method="jwt",
                ip_address=request.client.host if hasattr(request, "client") else None,
                user_agent=request.headers.get("User-Agent"),
            )

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise AuthenticationError("Invalid authentication token") from e
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError("Authentication failed") from e

    async def check_rate_limit(self, user_id: str, ip_address: str) -> bool:
        """Check if request is within rate limits."""

        # Use user_id if authenticated, otherwise use IP
        key = user_id if user_id else ip_address
        current_time = datetime.utcnow()
        minute_key = f"{key}:{current_time.strftime('%Y-%m-%d-%H-%M')}"

        # Get current count
        current_count = self.rate_limit_storage.get(minute_key, 0)

        if current_count >= self.rate_limit_per_minute:
            logger.warning(f"Rate limit exceeded for {key}")
            return False

        # Increment counter
        self.rate_limit_storage[minute_key] = current_count + 1

        # Clean up old entries (simple cleanup, in production use Redis TTL)
        cutoff_time = current_time - timedelta(minutes=2)
        keys_to_remove = [
            k
            for k in self.rate_limit_storage.keys()
            if len(k.split(":")) > 1
            and datetime.strptime(k.split(":", 1)[1], "%Y-%m-%d-%H-%M") < cutoff_time
        ]
        for key in keys_to_remove:
            del self.rate_limit_storage[key]

        return True

    def analyze_query_complexity(self, query: str) -> dict[str, int]:
        """Analyze GraphQL query complexity and depth."""

        # Simplified complexity analysis
        # In production, use a proper GraphQL query analyzer

        complexity_score = 0
        depth_score = 0

        # Count field selections (rough complexity estimate)
        field_count = query.count("{") + query.count("}")
        complexity_score += field_count * 10

        # Count nested levels (rough depth estimate)
        max_depth = 0
        current_depth = 0
        for char in query:
            if char == "{":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == "}":
                current_depth -= 1

        depth_score = max_depth

        # Count expensive operations
        if "search" in query.lower():
            complexity_score += 50
        if "analytics" in query.lower():
            complexity_score += 100
        if "dependencies" in query.lower():
            complexity_score += 30

        return {"complexity": complexity_score, "depth": depth_score}

    async def process_request(self, request: Any, query: str) -> SecurityContext:
        """Process incoming GraphQL request with full security checks."""

        # Authenticate request
        security_ctx = await self.authenticate_request(request)

        # Rate limiting
        if not await self.check_rate_limit(
            security_ctx.user_id or "anonymous", security_ctx.ip_address or "unknown"
        ):
            raise AuthorizationError("Rate limit exceeded")

        # Query complexity analysis
        if self.enable_query_complexity_analysis:
            analysis = self.analyze_query_complexity(query)

            if analysis["complexity"] > self.max_query_complexity:
                logger.warning(f"Query complexity too high: {analysis['complexity']}")
                raise AuthorizationError("Query too complex")

            if analysis["depth"] > self.max_query_depth:
                logger.warning(f"Query depth too high: {analysis['depth']}")
                raise AuthorizationError("Query too deep")

        return security_ctx


# Permission system
EXTENSION_PERMISSIONS = {
    "extension:create": "Create new extensions",
    "extension:read": "Read extension details",
    "extension:update": "Update own extensions",
    "extension:delete": "Delete own extensions",
    "extension:publish": "Publish extensions",
    "extension:list": "List extensions",
    "extension:search": "Search extensions",
    "extension:subscribe": "Subscribe to extension updates",
    "agent:read": "Read agent details",
    "agent:modify": "Modify agent configuration",
    "agent:list": "List agents",
    "security:read": "Read security scans",
    "security:scan": "Initiate security scans",
    "security:subscribe": "Subscribe to security alerts",
    "analytics:read": "Read analytics data",
    "admin": "Administrative access",
}

# Role-based permissions
ROLE_PERMISSIONS = {
    "user": [
        "extension:read",
        "extension:list",
        "extension:search",
        "agent:read",
        "agent:list",
    ],
    "developer": [
        "extension:create",
        "extension:read",
        "extension:update",
        "extension:delete",
        "extension:list",
        "extension:search",
        "extension:subscribe",
        "agent:read",
        "agent:modify",
        "agent:list",
        "security:read",
    ],
    "publisher": [
        "extension:create",
        "extension:read",
        "extension:update",
        "extension:delete",
        "extension:publish",
        "extension:list",
        "extension:search",
        "extension:subscribe",
        "agent:read",
        "agent:modify",
        "agent:list",
        "security:read",
        "security:scan",
    ],
    "admin": [
        # All permissions
        *EXTENSION_PERMISSIONS.keys()
    ],
}


def get_permissions_for_roles(roles: list[str]) -> set[str]:
    """Get combined permissions for a list of roles."""
    permissions = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, []))
    return permissions


async def check_permissions(
    security_ctx: SecurityContext,
    required_permission: str,
    resource_id: Optional[str] = None,
) -> bool:
    """Check if user has required permission for a resource."""

    # Unauthenticated users can only read public data
    if not security_ctx.is_authenticated:
        return required_permission in [
            "extension:read",
            "extension:list",
            "extension:search",
        ]

    # Check basic permission
    if not security_ctx.has_permission(required_permission):
        return False

    # Resource-specific checks
    if resource_id and required_permission in ["extension:update", "extension:delete"]:
        # Users can only modify their own extensions (unless admin)
        if not security_ctx.has_permission("admin"):
            # In a real implementation, check extension ownership
            # For now, assume all authenticated users can modify
            pass

    return True


def authorize_field(permission: str, resource_id_field: Optional[str] = None) -> Any:
    """Decorator for field-level authorization."""

    def decorator(resolver_func: Any) -> Any:
        @wraps(resolver_func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract info from arguments
            info = None
            for arg in args:
                if hasattr(arg, "context"):
                    info = arg
                    break

            if not info:
                raise AuthorizationError("Missing GraphQL info context")

            security_ctx = SecurityContext.from_info(info)

            # Extract resource ID if specified
            resource_id = None
            if resource_id_field:
                resource_id = kwargs.get(resource_id_field)

            # Check permissions
            if not await check_permissions(security_ctx, permission, resource_id):
                raise AuthorizationError(
                    f"Access denied: missing permission '{permission}'"
                )

            return await resolver_func(*args, **kwargs)

        return wrapper

    return decorator


def require_authentication(resolver_func: Any) -> Any:
    """Decorator to require authentication for a resolver."""

    @wraps(resolver_func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Extract info from arguments
        info = None
        for arg in args:
            if hasattr(arg, "context"):
                info = arg
                break

        if not info:
            raise AuthenticationError("Missing GraphQL info context")

        security_ctx = SecurityContext.from_info(info)

        if not security_ctx.is_authenticated:
            raise AuthenticationError("Authentication required")

        return await resolver_func(*args, **kwargs)

    return wrapper


def require_roles(required_roles: list[str]) -> Any:
    """Decorator to require specific roles."""

    def decorator(resolver_func: Any) -> Any:
        @wraps(resolver_func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            info = None
            for arg in args:
                if hasattr(arg, "context"):
                    info = arg
                    break

            if not info:
                raise AuthorizationError("Missing GraphQL info context")

            security_ctx = SecurityContext.from_info(info)

            if not security_ctx.has_any_role(required_roles):
                raise AuthorizationError(
                    f"Access denied: requires one of roles {required_roles}"
                )

            return await resolver_func(*args, **kwargs)

        return wrapper

    return decorator


# Audit logging
class AuditLogger:
    """Audit logger for security events."""

    def __init__(self, storage_service: Any = None) -> None:
        self.storage_service = storage_service

    async def log_action(
        self,
        user_id: str,
        action: str,
        resource_id: Optional[str] = None,
        resource_type: str = "extension",
        metadata: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
    ) -> None:
        """Log security-relevant action."""

        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "metadata": metadata or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
        }

        # Log to standard logger
        logger.info(f"AUDIT: {audit_entry}")

        # Store in database if service available
        if self.storage_service:
            await self.storage_service.store_audit_log(audit_entry)


# Input sanitization
def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Sanitize user input."""
    if not isinstance(value, str):
        return str(value)

    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", "\x00"]
    for char in dangerous_chars:
        value = value.replace(char, "")

    return value.strip()


def validate_extension_content(content: dict[str, Any]) -> list[str]:
    """Validate extension content for security issues."""
    errors = []

    # Check for potentially dangerous content
    content_str = str(content).lower()

    dangerous_patterns = [
        "eval(",
        "exec(",
        "import os",
        "import sys",
        "subprocess",
        "__import__",
        "open(",
        "file(",
        "input(",
        "raw_input(",
        "execfile(",
        "reload(",
        "__builtins__",
    ]

    for pattern in dangerous_patterns:
        if pattern in content_str:
            errors.append(f"Potentially dangerous content detected: {pattern}")

    # Check content size
    content_size = len(str(content))
    if content_size > 1024 * 1024:  # 1MB limit
        errors.append("Extension content too large (max 1MB)")

    return errors
