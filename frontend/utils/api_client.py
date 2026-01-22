"""
API Client for DealFlow Backend
Handles all communication with the FastAPI backend service.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisStatus(Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class APIResponse:
    """Standardized API response wrapper."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class DealFlowAPIClient:
    """
    Production-grade API client for DealFlow backend.

    Features:
    - Connection pooling via requests Session
    - Automatic retry with exponential backoff
    - Comprehensive error handling
    - Request/response logging
    - Timeout configuration
    """

    DEFAULT_TIMEOUT = 30  # seconds
    LONG_TIMEOUT = 300  # 5 minutes for sync analysis
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client.

        Args:
            base_url: Backend API base URL
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = MAX_RETRIES,
        **kwargs
    ) -> APIResponse:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            **kwargs: Additional arguments for requests

        Returns:
            APIResponse object with success status and data/error
        """
        url = f"{self.base_url}{endpoint}"
        last_error = None

        for attempt in range(retries):
            try:
                logger.info(f"API Request: {method} {url} (attempt {attempt + 1}/{retries})")

                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=timeout,
                    **kwargs
                )

                # Log response status
                logger.info(f"API Response: {response.status_code}")

                # Handle successful responses
                if response.status_code in (200, 201):
                    try:
                        data = response.json()
                    except ValueError:
                        data = {"raw": response.text}
                    return APIResponse(
                        success=True,
                        data=data,
                        status_code=response.status_code
                    )

                # Handle client errors (4xx) - don't retry
                if 400 <= response.status_code < 500:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("detail", str(error_data))
                    except ValueError:
                        error_msg = response.text or f"HTTP {response.status_code}"

                    return APIResponse(
                        success=False,
                        error=error_msg,
                        status_code=response.status_code
                    )

                # Handle server errors (5xx) - retry
                last_error = f"Server error: HTTP {response.status_code}"

            except Timeout as e:
                last_error = f"Request timeout after {timeout}s"
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")

            except ConnectionError as e:
                last_error = "Unable to connect to backend server. Please ensure the API is running."
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")

            except RequestException as e:
                last_error = f"Request failed: {str(e)}"
                logger.warning(f"Request exception on attempt {attempt + 1}: {e}")

            # Exponential backoff before retry
            if attempt < retries - 1:
                delay = self.RETRY_DELAY * (2 ** attempt)
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)

        return APIResponse(
            success=False,
            error=last_error or "Unknown error occurred"
        )

    def health_check(self) -> APIResponse:
        """
        Check backend health status.

        Returns:
            APIResponse with health status
        """
        return self._make_request("GET", "/health", timeout=5, retries=1)

    def upload_documents(self, files: List[Tuple[str, bytes, str]]) -> APIResponse:
        """
        Upload PDF documents for analysis.

        Args:
            files: List of tuples (filename, file_bytes, content_type)

        Returns:
            APIResponse with upload result
        """
        if not files:
            return APIResponse(success=False, error="No files provided")

        # Prepare multipart form data
        files_data = []
        for filename, file_bytes, content_type in files:
            files_data.append(
                ("files", (filename, file_bytes, content_type))
            )

        return self._make_request(
            "POST",
            "/api/v1/deals/upload",
            files=files_data,
            timeout=60  # Allow more time for file upload
        )

    def analyze_sync(
        self,
        file_ids: Optional[List[str]] = None,
        company_name: Optional[str] = None,
        uploaded_files: Optional[List[Tuple[str, bytes, str]]] = None
    ) -> APIResponse:
        """
        Trigger synchronous deal analysis.

        Args:
            file_ids: List of uploaded file IDs
            company_name: Optional company name for research
            uploaded_files: Optional files to upload and analyze directly

        Returns:
            APIResponse with full IC memo analysis
        """
        # If files are provided directly, upload them first
        if uploaded_files:
            files_data = []
            for filename, file_bytes, content_type in uploaded_files:
                files_data.append(
                    ("files", (filename, file_bytes, content_type))
                )

            # Include company name in the form data if provided
            data = {}
            if company_name:
                data["company_name"] = company_name

            return self._make_request(
                "POST",
                "/api/v1/deals/analyze/sync",
                files=files_data,
                data=data if data else None,
                timeout=self.LONG_TIMEOUT
            )

        # Otherwise, use file IDs
        payload = {}
        if file_ids:
            payload["file_ids"] = file_ids
        if company_name:
            payload["company_name"] = company_name

        return self._make_request(
            "POST",
            "/api/v1/deals/analyze/sync",
            json=payload,
            timeout=self.LONG_TIMEOUT
        )

    def analyze_async(
        self,
        file_ids: Optional[List[str]] = None,
        company_name: Optional[str] = None
    ) -> APIResponse:
        """
        Trigger asynchronous deal analysis.

        Args:
            file_ids: List of uploaded file IDs
            company_name: Optional company name for research

        Returns:
            APIResponse with analysis_id for tracking
        """
        payload = {}
        if file_ids:
            payload["file_ids"] = file_ids
        if company_name:
            payload["company_name"] = company_name

        return self._make_request(
            "POST",
            "/api/v1/deals/analyze",
            json=payload,
            timeout=self.DEFAULT_TIMEOUT
        )

    def get_analysis_status(self, analysis_id: str) -> APIResponse:
        """
        Check the status of an async analysis.

        Args:
            analysis_id: The analysis job ID

        Returns:
            APIResponse with current status and progress
        """
        return self._make_request(
            "GET",
            f"/api/v1/deals/{analysis_id}/status",
            timeout=10
        )

    def get_analysis_result(self, analysis_id: str) -> APIResponse:
        """
        Get the results of a completed analysis.

        Args:
            analysis_id: The analysis job ID

        Returns:
            APIResponse with full IC memo results
        """
        return self._make_request(
            "GET",
            f"/api/v1/deals/{analysis_id}/result",
            timeout=30
        )

    def poll_analysis(
        self,
        analysis_id: str,
        poll_interval: int = 2,
        max_wait: int = 300,
        callback: Optional[callable] = None
    ) -> APIResponse:
        """
        Poll for analysis completion with optional status callback.

        Args:
            analysis_id: The analysis job ID
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait
            callback: Optional function to call with status updates

        Returns:
            APIResponse with final results or timeout error
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_response = self.get_analysis_status(analysis_id)

            if not status_response.success:
                return status_response

            status = status_response.data.get("status", "unknown")

            # Call callback with current status if provided
            if callback:
                callback(status_response.data)

            if status == AnalysisStatus.COMPLETED.value:
                return self.get_analysis_result(analysis_id)

            if status == AnalysisStatus.FAILED.value:
                error_msg = status_response.data.get("error", "Analysis failed")
                return APIResponse(success=False, error=error_msg)

            time.sleep(poll_interval)

        return APIResponse(
            success=False,
            error=f"Analysis timed out after {max_wait} seconds"
        )

    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for quick API access
def get_api_client(base_url: str = "http://localhost:8000") -> DealFlowAPIClient:
    """
    Get a configured API client instance.

    Args:
        base_url: Backend API base URL

    Returns:
        Configured DealFlowAPIClient instance
    """
    return DealFlowAPIClient(base_url)
