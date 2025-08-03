"""Configuration settings for A2A Registry."""

import os


class RegistryConfig:
    """Configuration for A2A Registry development and production modes."""

    def __init__(self) -> None:
        # Development mode configuration
        self.dev_mode = os.getenv("A2A_REGISTRY_DEV_MODE", "true").lower() == "true"

        # Extension verification settings
        self.require_extension_verification = (
            os.getenv("A2A_REGISTRY_REQUIRE_EXTENSION_VERIFICATION", "false").lower()
            == "true"
        )

        # Domain verification settings (production mode)
        self.require_domain_verification = (
            os.getenv("A2A_REGISTRY_REQUIRE_DOMAIN_VERIFICATION", "false").lower()
            == "true"
        )

        # JWS signature verification settings (production mode)
        self.require_signature_verification = (
            os.getenv("A2A_REGISTRY_REQUIRE_SIGNATURE_VERIFICATION", "false").lower()
            == "true"
        )

        # Extension URI allowlist (production mode)
        allowlist_str = os.getenv("A2A_REGISTRY_EXTENSION_ALLOWLIST", "")
        self.extension_allowlist: set[str] = {
            uri.strip() for uri in allowlist_str.split(",") if uri.strip()
        }

        # Default trust level for development mode
        self.default_dev_trust_level = os.getenv(
            "A2A_REGISTRY_DEFAULT_DEV_TRUST_LEVEL", "TRUST_LEVEL_UNVERIFIED"
        )

        # Storage configuration
        self.storage_type = os.getenv("STORAGE_TYPE", "memory").lower()
        self.storage_data_dir = os.getenv("STORAGE_DATA_DIR", "/data")

    @property
    def is_production_mode(self) -> bool:
        """Check if registry is running in production mode."""
        return not self.dev_mode

    def is_extension_allowed(self, uri: str) -> bool:
        """Check if an extension URI is allowed based on current mode."""
        if self.dev_mode:
            # In dev mode, allow all extensions
            return True

        if not self.require_extension_verification:
            # If verification is not required, allow all
            return True

        # In production mode with verification required, check allowlist
        return uri in self.extension_allowlist

    def get_default_trust_level(self) -> str:
        """Get default trust level based on mode."""
        if self.dev_mode:
            return self.default_dev_trust_level
        return "TRUST_LEVEL_UNVERIFIED"


# Global configuration instance
config = RegistryConfig()
