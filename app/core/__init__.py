"""
Core business logic for DealFlow AI Copilot.

This package contains:
- GeminiClient: Production-grade wrapper for Google Gemini API
- Deal workflow orchestration (coming soon)
- Analysis pipelines (coming soon)
- Business rules and validation (coming soon)
"""

from app.core.gemini_client import GeminiClient, get_gemini_client

__all__ = ["GeminiClient", "get_gemini_client"]
