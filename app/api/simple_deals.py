"""
Simplified Deal Analysis API.

Clean endpoint for multi-file upload and analysis with categorized output.
"""

from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.agents.simple_orchestrator import get_simple_orchestrator
from app.models.simple_output import FullAnalysisResult
from app.utils.logger import logger

router = APIRouter(prefix="/analyze", tags=["simple-analysis"])


@router.post(
    "/",
    response_model=FullAnalysisResult,
    summary="Analyze Multiple Documents",
    description="""
Upload multiple documents (PDF, DOCX, XLSX) for comprehensive deal analysis.

**What happens:**
1. **Extraction**: AI reads all documents and extracts structured data
2. **Analysis**: Business model, market, and competitive analysis
3. **Risk Assessment**: Identifies and categorizes risks
4. **Valuation**: Multiple methodologies to estimate value
5. **Summary**: Executive summary with recommendation

**Output Structure:**
- `summary`: Executive summary for quick decisions
- `extraction`: Raw data extracted (with methodology explanation)
- `analysis`: Business scores with reasoning
- `risks`: Categorized risks with severity
- `valuation`: Value range with methods used

**Supported Formats:** PDF, DOCX, XLSX
""",
)
async def analyze_documents(
    files: list[UploadFile] = File(..., description="Documents to analyze (PDF, DOCX, XLSX)"),
    company_name: Optional[str] = Form(None, description="Optional company name hint"),
) -> FullAnalysisResult:
    """
    Analyze multiple documents and return categorized results.

    Args:
        files: List of uploaded files
        company_name: Optional company name hint for better extraction

    Returns:
        FullAnalysisResult with summary and all agent outputs
    """
    logger.info(f"Received {len(files)} files for analysis")

    # Validate files
    valid_extensions = [".pdf", ".docx", ".xlsx"]
    file_data: list[tuple[str, bytes]] = []

    for file in files:
        # Check extension
        filename = file.filename or "unknown"
        ext = filename.lower().split(".")[-1]

        if f".{ext}" not in valid_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {filename}. Supported: PDF, DOCX, XLSX"
            )

        # Read content
        content = await file.read()
        file_data.append((filename, content))
        logger.info(f"Loaded file: {filename} ({len(content)} bytes)")

    if not file_data:
        raise HTTPException(status_code=400, detail="No valid files provided")

    # Run analysis
    try:
        orchestrator = get_simple_orchestrator()
        result = await orchestrator.analyze_bytes(file_data, company_name)

        logger.info(
            f"Analysis complete: {result.summary.company_name}, "
            f"recommendation={result.summary.recommendation.value}"
        )

        return result

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post(
    "/quick",
    summary="Quick Extraction Only",
    description="Extract data from documents without full analysis (faster).",
)
async def quick_extract(
    files: list[UploadFile] = File(..., description="Documents to extract from"),
    company_name: Optional[str] = Form(None),
):
    """
    Quick extraction only - no analysis, risks, or valuation.
    Useful for previewing data before full analysis.
    """
    logger.info(f"Quick extraction of {len(files)} files")

    file_data: list[tuple[str, bytes]] = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename or "unknown", content))

    try:
        orchestrator = get_simple_orchestrator()
        content = await orchestrator.processor.process_file_bytes(file_data)
        extraction = await orchestrator._extract(content, company_name)

        return {
            "company": extraction.company.model_dump(),
            "financials": extraction.financials.model_dump(),
            "team": [t.model_dump() for t in extraction.team],
            "team_size": extraction.team_size,
            "market": extraction.market.model_dump(),
            "documents_processed": extraction.documents_processed,
            "data_gaps": extraction.data_gaps,
        }

    except Exception as e:
        logger.error(f"Quick extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
