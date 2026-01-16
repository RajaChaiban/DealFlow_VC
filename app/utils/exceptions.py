"""
Custom exceptions for DealFlow AI Copilot.

Provides structured error handling with error codes and details.
"""

from typing import Any, Optional


class DealFlowBaseException(Exception):
    """
    Base exception for all DealFlow errors.

    Attributes:
        message: Human-readable error message
        details: Additional error context
        error_code: Optional error code for categorization
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "error_code": self.error_code,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, error_code={self.error_code!r})"


class ExtractionError(DealFlowBaseException):
    """
    Raised when document extraction fails.

    Examples:
        - PDF parsing errors
        - Invalid file format
        - Corrupted documents
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = "EXTRACTION_ERROR",
    ) -> None:
        super().__init__(message, details, error_code)


class AnalysisError(DealFlowBaseException):
    """
    Raised when AI analysis fails.

    Examples:
        - Model API errors
        - Invalid model response
        - Analysis timeout
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = "ANALYSIS_ERROR",
    ) -> None:
        super().__init__(message, details, error_code)


class ValidationError(DealFlowBaseException):
    """
    Raised when data validation fails.

    Examples:
        - Invalid input data
        - Missing required fields
        - Type mismatches
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = "VALIDATION_ERROR",
    ) -> None:
        super().__init__(message, details, error_code)


class APIError(DealFlowBaseException):
    """
    Raised when external API calls fail.

    Examples:
        - PitchBook API errors
        - Crunchbase API errors
        - Network failures
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = "API_ERROR",
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message, details, error_code)
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = super().to_dict()
        result["status_code"] = self.status_code
        return result
