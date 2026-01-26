"""
Multi-File Processor Service.

Handles processing of multiple files (PDF, DOCX, XLSX) and combines
their content into a unified structure for analysis.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from PIL import Image

from app.services.document_service import DocumentService
from app.utils.logger import logger


@dataclass
class ProcessedDocument:
    """Result of processing a single document."""
    filename: str
    file_type: str  # pdf, docx, xlsx
    text_content: str
    images: list[Image.Image]
    page_count: int
    is_structured: bool  # True for XLSX, False for PDF/DOCX


@dataclass
class CombinedContent:
    """Combined content from all processed documents."""
    # All images (from PDFs)
    all_images: list[Image.Image]

    # Combined text by type
    unstructured_text: str  # From PDFs and DOCX
    structured_text: str    # From XLSX (formatted tables)

    # Full combined text for extraction
    combined_text: str

    # Metadata
    documents: list[ProcessedDocument]
    total_pages: int
    file_summary: str  # e.g., "2 PDFs, 1 Excel file"


class MultiFileProcessor:
    """
    Processes multiple files of different types and combines their content.

    Supported formats:
    - PDF: Extracts text and converts pages to images
    - DOCX: Extracts text from paragraphs and tables
    - XLSX: Extracts data from all sheets as structured text

    Example:
        ```python
        processor = MultiFileProcessor()

        # Process multiple files
        content = await processor.process_files([
            "pitch_deck.pdf",
            "financials.xlsx",
            "team_bios.docx"
        ])

        print(f"Processed: {content.file_summary}")
        print(f"Total text: {len(content.combined_text)} chars")
        print(f"Images: {len(content.all_images)}")
        ```
    """

    def __init__(self):
        """Initialize the multi-file processor."""
        self.doc_service = DocumentService()
        logger.info("MultiFileProcessor initialized")

    async def process_files(
        self,
        file_paths: list[str],
    ) -> CombinedContent:
        """
        Process multiple files and combine their content.

        Args:
            file_paths: List of paths to files to process

        Returns:
            CombinedContent with all extracted data
        """
        logger.info(f"Processing {len(file_paths)} files")

        documents: list[ProcessedDocument] = []
        all_images: list[Image.Image] = []
        unstructured_texts: list[str] = []
        structured_texts: list[str] = []

        for file_path in file_paths:
            try:
                doc = await self._process_single_file(file_path)
                documents.append(doc)

                # Collect images
                all_images.extend(doc.images)

                # Separate structured vs unstructured
                if doc.is_structured:
                    structured_texts.append(f"\n=== {doc.filename} ===\n{doc.text_content}")
                else:
                    unstructured_texts.append(f"\n=== {doc.filename} ===\n{doc.text_content}")

                logger.info(f"Processed: {doc.filename} ({doc.file_type}, {len(doc.text_content)} chars)")

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                # Continue with other files

        # Combine texts
        unstructured_text = "\n".join(unstructured_texts)
        structured_text = "\n".join(structured_texts)

        # Build combined text with clear sections
        combined_parts = []
        if unstructured_text.strip():
            combined_parts.append("=== DOCUMENT CONTENT ===\n" + unstructured_text)
        if structured_text.strip():
            combined_parts.append("=== STRUCTURED DATA ===\n" + structured_text)

        combined_text = "\n\n".join(combined_parts)

        # Build file summary
        file_types = {}
        for doc in documents:
            file_types[doc.file_type] = file_types.get(doc.file_type, 0) + 1

        summary_parts = []
        if file_types.get("pdf", 0):
            summary_parts.append(f"{file_types['pdf']} PDF{'s' if file_types['pdf'] > 1 else ''}")
        if file_types.get("docx", 0):
            summary_parts.append(f"{file_types['docx']} Word doc{'s' if file_types['docx'] > 1 else ''}")
        if file_types.get("xlsx", 0):
            summary_parts.append(f"{file_types['xlsx']} Excel file{'s' if file_types['xlsx'] > 1 else ''}")

        file_summary = ", ".join(summary_parts) if summary_parts else "No files processed"

        total_pages = sum(doc.page_count for doc in documents)

        result = CombinedContent(
            all_images=all_images,
            unstructured_text=unstructured_text,
            structured_text=structured_text,
            combined_text=combined_text,
            documents=documents,
            total_pages=total_pages,
            file_summary=file_summary,
        )

        logger.info(
            f"Combined content ready: {file_summary}, "
            f"{len(all_images)} images, {len(combined_text)} chars"
        )

        return result

    async def process_file_bytes(
        self,
        files: list[tuple[str, bytes]],  # [(filename, content), ...]
    ) -> CombinedContent:
        """
        Process multiple files from bytes.

        Args:
            files: List of (filename, content_bytes) tuples

        Returns:
            CombinedContent with all extracted data
        """
        logger.info(f"Processing {len(files)} files from bytes")

        documents: list[ProcessedDocument] = []
        all_images: list[Image.Image] = []
        unstructured_texts: list[str] = []
        structured_texts: list[str] = []

        for filename, content in files:
            try:
                doc = await self._process_bytes(filename, content)
                documents.append(doc)

                all_images.extend(doc.images)

                if doc.is_structured:
                    structured_texts.append(f"\n=== {doc.filename} ===\n{doc.text_content}")
                else:
                    unstructured_texts.append(f"\n=== {doc.filename} ===\n{doc.text_content}")

                logger.info(f"Processed: {doc.filename} ({doc.file_type}, {len(doc.text_content)} chars)")

            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")

        # Combine texts
        unstructured_text = "\n".join(unstructured_texts)
        structured_text = "\n".join(structured_texts)

        combined_parts = []
        if unstructured_text.strip():
            combined_parts.append("=== DOCUMENT CONTENT ===\n" + unstructured_text)
        if structured_text.strip():
            combined_parts.append("=== STRUCTURED DATA ===\n" + structured_text)

        combined_text = "\n\n".join(combined_parts)

        # Build file summary
        file_types = {}
        for doc in documents:
            file_types[doc.file_type] = file_types.get(doc.file_type, 0) + 1

        summary_parts = []
        if file_types.get("pdf", 0):
            summary_parts.append(f"{file_types['pdf']} PDF{'s' if file_types['pdf'] > 1 else ''}")
        if file_types.get("docx", 0):
            summary_parts.append(f"{file_types['docx']} Word doc{'s' if file_types['docx'] > 1 else ''}")
        if file_types.get("xlsx", 0):
            summary_parts.append(f"{file_types['xlsx']} Excel file{'s' if file_types['xlsx'] > 1 else ''}")

        file_summary = ", ".join(summary_parts) if summary_parts else "No files processed"
        total_pages = sum(doc.page_count for doc in documents)

        return CombinedContent(
            all_images=all_images,
            unstructured_text=unstructured_text,
            structured_text=structured_text,
            combined_text=combined_text,
            documents=documents,
            total_pages=total_pages,
            file_summary=file_summary,
        )

    async def _process_single_file(self, file_path: str) -> ProcessedDocument:
        """Process a single file by path."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            images, text = await self.doc_service.process_pdf(file_path)
            return ProcessedDocument(
                filename=path.name,
                file_type="pdf",
                text_content=text,
                images=images,
                page_count=len(images) if images else 1,
                is_structured=False,
            )

        elif ext == ".docx":
            images, text = await self.doc_service.process_docx(file_path)
            return ProcessedDocument(
                filename=path.name,
                file_type="docx",
                text_content=text,
                images=images,
                page_count=1,
                is_structured=False,
            )

        elif ext == ".xlsx":
            images, text = await self.doc_service.process_xlsx(file_path)
            # Count sheets as pages
            sheet_count = text.count("--- Sheet:")
            return ProcessedDocument(
                filename=path.name,
                file_type="xlsx",
                text_content=text,
                images=images,
                page_count=max(1, sheet_count),
                is_structured=True,
            )

        else:
            raise ValueError(f"Unsupported file type: {ext}")

    async def _process_bytes(self, filename: str, content: bytes) -> ProcessedDocument:
        """Process a single file from bytes."""
        ext = os.path.splitext(filename.lower())[1]

        if ext == ".pdf":
            images, text = await self.doc_service.process_pdf_bytes(content)
            return ProcessedDocument(
                filename=filename,
                file_type="pdf",
                text_content=text,
                images=images,
                page_count=len(images) if images else 1,
                is_structured=False,
            )

        elif ext == ".docx":
            images, text = self.doc_service._process_docx_bytes(content)
            return ProcessedDocument(
                filename=filename,
                file_type="docx",
                text_content=text,
                images=images,
                page_count=1,
                is_structured=False,
            )

        elif ext == ".xlsx":
            images, text = self.doc_service._process_xlsx_bytes(content)
            sheet_count = text.count("--- Sheet:")
            return ProcessedDocument(
                filename=filename,
                file_type="xlsx",
                text_content=text,
                images=images,
                page_count=max(1, sheet_count),
                is_structured=True,
            )

        else:
            raise ValueError(f"Unsupported file type: {ext}")


# Singleton instance
_processor: Optional[MultiFileProcessor] = None


def get_multi_file_processor() -> MultiFileProcessor:
    """Get the global multi-file processor instance."""
    global _processor
    if _processor is None:
        _processor = MultiFileProcessor()
    return _processor
