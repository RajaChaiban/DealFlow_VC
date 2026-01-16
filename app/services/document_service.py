"""
Document Processing Service for DealFlow AI Copilot.

Handles PDF upload, processing, and text/image extraction:
- PDF to image conversion (using pdf2image)
- Text extraction (using PyPDF2)
- Image preprocessing for optimal AI analysis
- File storage management
"""

import hashlib
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
from PyPDF2 import PdfReader

from app.config import settings
from app.models.schemas import UploadResponse
from app.utils.exceptions import ExtractionError
from app.utils.logger import logger


class DocumentService:
    """
    Service for processing pitch deck documents.

    Handles:
    - PDF file upload and storage
    - PDF to image conversion for vision analysis
    - Text extraction from PDFs
    - Image optimization for AI processing

    Example:
        ```python
        service = DocumentService()

        # Upload a file
        upload = await service.save_upload(file_content, "pitch_deck.pdf")

        # Process the PDF
        images, text = await service.process_pdf(upload.file_path)

        # Use with orchestrator
        orchestrator = OrchestratorAgent()
        result = await orchestrator.analyze(images=images, text_content=text)
        ```
    """

    def __init__(
        self,
        upload_dir: Optional[str] = None,
        processed_dir: Optional[str] = None,
        max_file_size_mb: int = 50,
        max_pages: int = 100,
        image_dpi: int = 150,
        image_format: str = "PNG",
    ) -> None:
        """
        Initialize the document service.

        Args:
            upload_dir: Directory for uploaded files
            processed_dir: Directory for processed files
            max_file_size_mb: Maximum file size in MB
            max_pages: Maximum pages to process
            image_dpi: DPI for PDF to image conversion
            image_format: Output image format (PNG recommended)
        """
        self.upload_dir = Path(upload_dir or settings.upload_dir)
        self.processed_dir = Path(processed_dir or settings.processed_dir)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.max_pages = max_pages
        self.image_dpi = image_dpi
        self.image_format = image_format

        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"DocumentService initialized: upload_dir={self.upload_dir}")

    async def save_upload(
        self,
        content: bytes,
        filename: str,
    ) -> UploadResponse:
        """
        Save uploaded file to disk.

        Args:
            content: File content as bytes
            filename: Original filename

        Returns:
            UploadResponse with file metadata

        Raises:
            ExtractionError: If file is too large or invalid
        """
        # Validate file size
        if len(content) > self.max_file_size_bytes:
            raise ExtractionError(
                message=f"File too large: {len(content) / 1024 / 1024:.1f}MB exceeds {self.max_file_size_bytes / 1024 / 1024:.0f}MB limit",
                error_code="FILE_TOO_LARGE",
            )

        # Validate file type
        if not filename.lower().endswith(".pdf"):
            raise ExtractionError(
                message=f"Invalid file type: {filename}. Only PDF files are supported.",
                error_code="INVALID_FILE_TYPE",
            )

        # Generate unique file ID
        file_hash = hashlib.md5(content).hexdigest()[:12]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_id = f"{timestamp}_{file_hash}"

        # Clean filename
        clean_name = self._sanitize_filename(filename)
        stored_filename = f"{file_id}_{clean_name}"

        # Save file
        file_path = self.upload_dir / stored_filename

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        logger.info(f"Saved upload: {stored_filename} ({len(content)} bytes)")

        # Detect MIME type
        mime_type = "application/pdf"

        return UploadResponse(
            file_id=file_id,
            filename=filename,
            file_path=str(file_path),
            file_size_bytes=len(content),
            mime_type=mime_type,
        )

    async def process_pdf(
        self,
        file_path: str,
    ) -> tuple[list[Image.Image], str]:
        """
        Process a PDF file into images and text.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (list of PIL Images, extracted text)

        Raises:
            ExtractionError: If PDF processing fails
        """
        pdf_path = Path(file_path)

        if not pdf_path.exists():
            raise ExtractionError(
                message=f"File not found: {file_path}",
                error_code="FILE_NOT_FOUND",
            )

        logger.info(f"Processing PDF: {pdf_path.name}")

        # Extract text
        text = await self._extract_text(pdf_path)
        logger.info(f"Extracted {len(text)} characters of text")

        # Convert to images
        images = await self._convert_to_images(pdf_path)
        logger.info(f"Converted PDF to {len(images)} images")

        return images, text

    async def process_pdf_bytes(
        self,
        content: bytes,
    ) -> tuple[list[Image.Image], str]:
        """
        Process PDF from bytes without saving to disk.

        Args:
            content: PDF content as bytes

        Returns:
            Tuple of (list of PIL Images, extracted text)
        """
        logger.info(f"Processing PDF from bytes: {len(content)} bytes")

        # Extract text from bytes
        text = self._extract_text_from_bytes(content)
        logger.info(f"Extracted {len(text)} characters of text")

        # Convert to images from bytes
        images = self._convert_bytes_to_images(content)
        logger.info(f"Converted PDF to {len(images)} images")

        return images, text

    async def _extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(str(pdf_path))
            text_parts: list[str] = []

            for i, page in enumerate(reader.pages):
                if i >= self.max_pages:
                    logger.warning(f"Reached max pages ({self.max_pages}), stopping extraction")
                    break

                try:
                    page_text = page.extract_text() or ""
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i + 1}: {e}")
                    text_parts.append(f"--- Page {i + 1} ---\n[Text extraction failed]")

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise ExtractionError(
                message=f"Failed to extract text from PDF: {e}",
                error_code="TEXT_EXTRACTION_FAILED",
            )

    def _extract_text_from_bytes(self, content: bytes) -> str:
        """Extract text from PDF bytes."""
        import io

        try:
            reader = PdfReader(io.BytesIO(content))
            text_parts: list[str] = []

            for i, page in enumerate(reader.pages):
                if i >= self.max_pages:
                    break

                try:
                    page_text = page.extract_text() or ""
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i + 1}: {e}")

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"PDF text extraction from bytes failed: {e}")
            return ""

    async def _convert_to_images(self, pdf_path: Path) -> list[Image.Image]:
        """Convert PDF pages to images."""
        try:
            # Convert PDF to images
            images = convert_from_path(
                str(pdf_path),
                dpi=self.image_dpi,
                fmt=self.image_format.lower(),
                first_page=1,
                last_page=self.max_pages,
            )

            # Optimize images for AI processing
            optimized = [self._optimize_image(img) for img in images]

            return optimized

        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            raise ExtractionError(
                message=f"Failed to convert PDF to images: {e}. Make sure poppler-utils is installed.",
                error_code="IMAGE_CONVERSION_FAILED",
                details={"hint": "Install poppler-utils: apt-get install poppler-utils (Linux) or brew install poppler (macOS)"},
            )

    def _convert_bytes_to_images(self, content: bytes) -> list[Image.Image]:
        """Convert PDF bytes to images."""
        try:
            images = convert_from_bytes(
                content,
                dpi=self.image_dpi,
                fmt=self.image_format.lower(),
                first_page=1,
                last_page=self.max_pages,
            )

            optimized = [self._optimize_image(img) for img in images]
            return optimized

        except Exception as e:
            logger.error(f"PDF bytes to image conversion failed: {e}")
            return []

    def _optimize_image(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for AI processing.

        - Resize if too large
        - Convert to RGB
        - Ensure reasonable file size
        """
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize if too large (max 2000px on longest side)
        max_size = 2000
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path components
        name = os.path.basename(filename)

        # Replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        sanitized = "".join(c if c in safe_chars else "_" for c in name)

        # Limit length
        if len(sanitized) > 100:
            base, ext = os.path.splitext(sanitized)
            sanitized = base[:100 - len(ext)] + ext

        return sanitized

    async def get_file(self, file_id: str) -> Optional[Path]:
        """
        Get file path by ID.

        Args:
            file_id: File ID from upload

        Returns:
            Path to file or None if not found
        """
        # Search for file with matching ID prefix
        for file_path in self.upload_dir.iterdir():
            if file_path.name.startswith(file_id):
                return file_path

        return None

    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file by ID.

        Args:
            file_id: File ID from upload

        Returns:
            True if deleted, False if not found
        """
        file_path = await self.get_file(file_id)

        if file_path and file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {file_path.name}")
            return True

        return False

    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Remove files older than specified age.

        Args:
            max_age_hours: Maximum file age in hours

        Returns:
            Number of files deleted
        """
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        deleted = 0

        for directory in [self.upload_dir, self.processed_dir]:
            for file_path in directory.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                    file_path.unlink()
                    deleted += 1

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old files")

        return deleted


# Singleton instance
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """Get or create document service singleton."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
