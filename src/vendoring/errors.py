class VendoringError(Exception):
    """Errors originating from this package."""


class ConfigurationError(VendoringError):
    """Errors related to configuration handling."""


class RequirementsError(VendoringError):
    """Errors related to requirements.txt handling."""
