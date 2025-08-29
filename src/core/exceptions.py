"""
Custom exceptions for batch annotation tool.
"""


class BatchAnnotationError(Exception):
    """Base exception for batch annotation tool."""
    pass


class ValidationError(BatchAnnotationError):
    """Raised when validation fails."""
    pass


class FileProcessingError(BatchAnnotationError):
    """Raised when file processing fails."""
    pass


class ModelError(BatchAnnotationError):
    """Raised when model operations fail."""
    pass


class ExportError(BatchAnnotationError):
    """Raised when export operations fail."""
    pass