"""
Business services for DealFlow AI Copilot.

This package contains:
- DocumentService: PDF processing and text/image extraction
- AnalysisService: Deal analysis orchestration (future)
- ExportService: PDF/Excel report generation (future)
"""

from app.services.document_service import DocumentService, get_document_service

__all__ = [
    "DocumentService",
    "get_document_service",
]
