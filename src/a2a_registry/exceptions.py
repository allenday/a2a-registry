"""Custom exceptions for A2A Registry with clear, actionable error messages."""

import logging
from typing import Any, Optional


class A2ARegistryError(Exception):
    """Base exception for all A2A Registry errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.context = context or {}

        # Log the error with full context
        logger = logging.getLogger(__name__)
        logger.error(
            "A2A Registry Error",
            extra={
                "error_code": self.error_code,
                "message": self.message,
                "details": self.details,
                "context": self.context,
                "exception_type": self.__class__.__name__,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "type": self.__class__.__name__,
        }


class ValidationError(A2ARegistryError):
    """Raised when input validation fails."""

    def __init__(
        self,
        field: str,
        value: Any,
        reason: str,
        context: Optional[dict[str, Any]] = None,
    ):
        message = f"Validation failed for field '{field}': {reason}"
        details = {
            "field": field,
            "value": str(value)[:100],  # Truncate long values
            "reason": reason,
        }
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            context=context,
        )


class AgentNotFoundError(A2ARegistryError):
    """Raised when an agent is not found in the registry."""

    def __init__(self, agent_id: str, context: Optional[dict[str, Any]] = None):
        message = f"Agent with ID '{agent_id}' not found in registry"
        details = {"agent_id": agent_id}
        super().__init__(
            message=message,
            error_code="AGENT_NOT_FOUND",
            details=details,
            context=context,
        )


class AgentRegistrationError(A2ARegistryError):
    """Raised when agent registration fails."""

    def __init__(
        self, agent_id: str, reason: str, context: Optional[dict[str, Any]] = None
    ):
        message = f"Failed to register agent '{agent_id}': {reason}"
        details = {"agent_id": agent_id, "reason": reason}
        super().__init__(
            message=message,
            error_code="AGENT_REGISTRATION_FAILED",
            details=details,
            context=context,
        )


class ExtensionNotFoundError(A2ARegistryError):
    """Raised when an extension is not found."""

    def __init__(self, extension_uri: str, context: Optional[dict[str, Any]] = None):
        message = f"Extension with URI '{extension_uri}' not found"
        details = {"extension_uri": extension_uri}
        super().__init__(
            message=message,
            error_code="EXTENSION_NOT_FOUND",
            details=details,
            context=context,
        )


class ExtensionNotAllowedError(A2ARegistryError):
    """Raised when an extension is not allowed in current configuration."""

    def __init__(
        self,
        extension_uri: str,
        mode: str,
        allowlist: Optional[list] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        message = f"Extension '{extension_uri}' not allowed in {mode} mode"
        if allowlist:
            message += f". Allowed extensions: {', '.join(allowlist)}"
        else:
            message += ". Check A2A_REGISTRY_EXTENSION_ALLOWLIST configuration."

        details = {
            "extension_uri": extension_uri,
            "mode": mode,
            "allowlist": allowlist or [],
        }
        super().__init__(
            message=message,
            error_code="EXTENSION_NOT_ALLOWED",
            details=details,
            context=context,
        )


class StorageError(A2ARegistryError):
    """Raised when storage operations fail."""

    def __init__(
        self, operation: str, reason: str, context: Optional[dict[str, Any]] = None
    ):
        message = f"Storage operation '{operation}' failed: {reason}"
        details = {"operation": operation, "reason": reason}
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            details=details,
            context=context,
        )


class ConfigurationError(A2ARegistryError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        config_key: str,
        value: Any,
        reason: str,
        context: Optional[dict[str, Any]] = None,
    ):
        message = f"Invalid configuration for '{config_key}': {reason}"
        details = {"config_key": config_key, "value": str(value), "reason": reason}
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            context=context,
        )


class PaginationError(A2ARegistryError):
    """Raised when pagination parameters are invalid."""

    def __init__(
        self,
        parameter: str,
        value: Any,
        reason: str,
        context: Optional[dict[str, Any]] = None,
    ):
        message = f"Invalid pagination parameter '{parameter}': {reason}"
        details = {"parameter": parameter, "value": str(value), "reason": reason}
        super().__init__(
            message=message,
            error_code="PAGINATION_ERROR",
            details=details,
            context=context,
        )


class FileOperationError(A2ARegistryError):
    """Raised when file operations fail."""

    def __init__(
        self,
        file_path: str,
        operation: str,
        reason: str,
        context: Optional[dict[str, Any]] = None,
    ):
        message = f"File operation '{operation}' failed for '{file_path}': {reason}"
        details = {"file_path": file_path, "operation": operation, "reason": reason}
        super().__init__(
            message=message,
            error_code="FILE_OPERATION_ERROR",
            details=details,
            context=context,
        )


class JSONRPCError(A2ARegistryError):
    """Raised when JSON-RPC operations fail."""

    def __init__(
        self,
        method: str,
        reason: str,
        rpc_code: int = -32603,
        context: Optional[dict[str, Any]] = None,
    ):
        message = f"JSON-RPC method '{method}' failed: {reason}"
        details = {"method": method, "reason": reason, "rpc_code": rpc_code}
        super().__init__(
            message=message,
            error_code="JSONRPC_ERROR",
            details=details,
            context=context,
        )
        self.rpc_code = rpc_code


class DuplicateAgentError(A2ARegistryError):
    """Raised when attempting to register an agent that already exists."""

    def __init__(self, agent_id: str, context: Optional[dict[str, Any]] = None):
        message = f"Agent with ID '{agent_id}' already exists in registry"
        details = {"agent_id": agent_id}
        super().__init__(
            message=message,
            error_code="DUPLICATE_AGENT",
            details=details,
            context=context,
        )


class InvalidAgentCardError(A2ARegistryError):
    """Raised when agent card data is invalid."""

    def __init__(
        self,
        field: str,
        issue: str,
        agent_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        message = f"Invalid agent card: {issue}"
        if field:
            message += f" (field: {field})"
        if agent_id:
            message += f" (agent: {agent_id})"

        details = {"field": field, "issue": issue, "agent_id": agent_id}
        super().__init__(
            message=message,
            error_code="INVALID_AGENT_CARD",
            details=details,
            context=context,
        )
