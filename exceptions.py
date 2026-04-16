"""Custom exceptions for the Coinbase crypto pipeline.

Provides specific exception types for different error scenarios
to enable better error handling and debugging.
"""


class PipelineException(Exception):
    """Base exception for the crypto pipeline."""
    pass


class ExtractException(PipelineException):
    """Raised when data extraction fails."""
    pass


class TransformException(PipelineException):
    """Raised when data transformation fails."""
    pass


class LoadException(PipelineException):
    """Raised when data loading fails."""
    pass


class ValidationException(PipelineException):
    """Raised when data validation fails."""
    pass


class ConfigException(PipelineException):
    """Raised when configuration is invalid."""
    pass


class APIException(ExtractException):
    """Raised when Coinbase API call fails."""
    pass


class APIRateLimitException(APIException):
    """Raised when API rate limit is hit."""
    pass


class DatabaseException(LoadException):
    """Raised when database operation fails."""
    pass


__all__ = [
    "PipelineException",
    "ExtractException",
    "TransformException",
    "LoadException",
    "ValidationException",
    "ConfigException",
    "APIException",
    "APIRateLimitException",
    "DatabaseException",
]

