"""
Deal analysis endpoints for DealFlow AI Copilot.

Endpoints for:
- Uploading pitch deck documents
- Running AI-powered deal analysis
- Retrieving analysis results
- Managing analysis jobs
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.agents import OrchestratorAgent
from app.models.schemas import (
    AgentStatus,
    AnalysisRequest,
    AnalysisResponse,
    ICMemo,
    OrchestratorProgress,
    UploadResponse,
)
from app.services import get_document_service
from app.utils.exceptions import AnalysisError, ExtractionError
from app.utils.logger import logger

router = APIRouter(prefix="/deals", tags=["deals"])

# In-memory storage for analysis jobs (replace with Redis/DB in production)
_analysis_jobs: dict[str, dict[str, Any]] = {}
_analysis_results: dict[str, ICMemo] = {}


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload Pitch Deck",
    description="Upload a pitch deck PDF for analysis",
)
async def upload_pitch_deck(
    file: UploadFile = File(..., description="PDF file to upload"),
) -> UploadResponse:
    """
    Upload a pitch deck PDF for analysis.

    Args:
        file: PDF file upload

    Returns:
        Upload metadata including file_id for analysis

    Raises:
        HTTPException: If upload fails
    """
    logger.info(f"Receiving upload: {file.filename}")

    # Validate content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only PDF files are supported.",
        )

    try:
        # Read file content
        content = await file.read()

        # Save upload
        service = get_document_service()
        result = await service.save_upload(content, file.filename or "upload.pdf")

        logger.info(f"Upload successful: {result.file_id}")
        return result

    except ExtractionError as e:
        logger.error(f"Upload failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Start Deal Analysis",
    description="Start AI-powered analysis of an uploaded pitch deck",
)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
) -> AnalysisResponse:
    """
    Start analysis of an uploaded pitch deck.

    The analysis runs in the background and can be monitored via the
    /deals/{analysis_id}/status endpoint.

    Args:
        request: Analysis request with file_id or file_path
        background_tasks: FastAPI background tasks

    Returns:
        Analysis response with job ID for tracking

    Raises:
        HTTPException: If analysis cannot be started
    """
    # Validate input
    if not request.file_id and not request.file_path:
        raise HTTPException(
            status_code=400,
            detail="Either file_id or file_path must be provided",
        )

    # Generate analysis ID
    analysis_id = str(uuid.uuid4())[:12]

    # Get file path
    file_path = request.file_path
    if request.file_id:
        service = get_document_service()
        path = await service.get_file(request.file_id)
        if not path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}",
            )
        file_path = str(path)

    # Initialize job status
    _analysis_jobs[analysis_id] = {
        "status": AgentStatus.PENDING,
        "started_at": datetime.utcnow(),
        "file_path": file_path,
        "company_name": request.company_name,
        "progress": None,
        "error": None,
    }

    # Start background analysis
    background_tasks.add_task(
        _run_analysis,
        analysis_id=analysis_id,
        file_path=file_path,
        company_name_hint=request.company_name,
        additional_context=request.additional_context,
        fast_mode=request.fast_mode,
    )

    logger.info(f"Started analysis job: {analysis_id}")

    return AnalysisResponse(
        analysis_id=analysis_id,
        status=AgentStatus.PENDING,
        message="Analysis started. Use GET /deals/{analysis_id}/status to check progress.",
    )


@router.post(
    "/analyze/sync",
    response_model=AnalysisResponse,
    summary="Run Synchronous Analysis",
    description="Run deal analysis synchronously (waits for completion)",
)
async def analyze_sync(
    file: UploadFile = File(..., description="PDF file to analyze"),
    company_name: Optional[str] = None,
) -> AnalysisResponse:
    """
    Run analysis synchronously, returning results when complete.

    This endpoint blocks until analysis is complete (30-60 seconds typical).
    Use for testing or when immediate results are needed.

    Args:
        file: PDF file to analyze
        company_name: Optional company name hint

    Returns:
        Analysis response with complete results

    Raises:
        HTTPException: If analysis fails
    """
    logger.info(f"Starting synchronous analysis: {file.filename}")

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only PDF files are supported.",
        )

    analysis_id = str(uuid.uuid4())[:12]

    try:
        # Read and process PDF
        content = await file.read()
        service = get_document_service()
        images, text = await service.process_pdf_bytes(content)

        if not images and not text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract content from PDF",
            )

        # Run orchestrator
        orchestrator = OrchestratorAgent()
        result = await orchestrator.analyze(
            images=images,
            text_content=text,
            company_name_hint=company_name,
        )

        # Store result
        _analysis_results[analysis_id] = result

        logger.info(f"Synchronous analysis complete: {analysis_id}")

        return AnalysisResponse(
            analysis_id=analysis_id,
            status=AgentStatus.COMPLETED,
            message="Analysis complete",
            result=result,
        )

    except AnalysisError as e:
        logger.error(f"Analysis failed: {e.message}")
        return AnalysisResponse(
            analysis_id=analysis_id,
            status=AgentStatus.FAILED,
            message="Analysis failed",
            error=e.message,
        )

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/{analysis_id}/status",
    response_model=AnalysisResponse,
    summary="Get Analysis Status",
    description="Get the status and progress of an analysis job",
)
async def get_analysis_status(analysis_id: str) -> AnalysisResponse:
    """
    Get status of an analysis job.

    Args:
        analysis_id: Analysis job ID

    Returns:
        Current status and progress

    Raises:
        HTTPException: If analysis not found
    """
    if analysis_id not in _analysis_jobs:
        # Check results
        if analysis_id in _analysis_results:
            return AnalysisResponse(
                analysis_id=analysis_id,
                status=AgentStatus.COMPLETED,
                message="Analysis complete",
                result=_analysis_results[analysis_id],
            )

        raise HTTPException(
            status_code=404,
            detail=f"Analysis not found: {analysis_id}",
        )

    job = _analysis_jobs[analysis_id]

    # Build progress object
    progress = None
    if job.get("progress"):
        progress = job["progress"]

    return AnalysisResponse(
        analysis_id=analysis_id,
        status=job["status"],
        message=_get_status_message(job["status"]),
        progress=progress,
        error=job.get("error"),
        result=_analysis_results.get(analysis_id),
    )


@router.get(
    "/{analysis_id}/result",
    summary="Get Analysis Result",
    description="Get the complete analysis result (IC Memo)",
)
async def get_analysis_result(analysis_id: str) -> ICMemo:
    """
    Get the complete analysis result.

    Args:
        analysis_id: Analysis job ID

    Returns:
        Complete IC Memo

    Raises:
        HTTPException: If not found or not complete
    """
    if analysis_id not in _analysis_results:
        # Check if job exists
        if analysis_id in _analysis_jobs:
            job = _analysis_jobs[analysis_id]
            if job["status"] == AgentStatus.RUNNING:
                raise HTTPException(
                    status_code=202,
                    detail="Analysis still in progress",
                )
            elif job["status"] == AgentStatus.FAILED:
                raise HTTPException(
                    status_code=500,
                    detail=f"Analysis failed: {job.get('error', 'Unknown error')}",
                )

        raise HTTPException(
            status_code=404,
            detail=f"Analysis result not found: {analysis_id}",
        )

    return _analysis_results[analysis_id]


@router.delete(
    "/{analysis_id}",
    summary="Delete Analysis",
    description="Delete an analysis job and its results",
)
async def delete_analysis(analysis_id: str) -> dict[str, str]:
    """
    Delete an analysis job and its results.

    Args:
        analysis_id: Analysis job ID

    Returns:
        Confirmation message

    Raises:
        HTTPException: If not found
    """
    found = False

    if analysis_id in _analysis_jobs:
        del _analysis_jobs[analysis_id]
        found = True

    if analysis_id in _analysis_results:
        del _analysis_results[analysis_id]
        found = True

    if not found:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis not found: {analysis_id}",
        )

    logger.info(f"Deleted analysis: {analysis_id}")

    return {"message": f"Analysis {analysis_id} deleted"}


@router.get(
    "",
    summary="List Analyses",
    description="List all analysis jobs",
)
async def list_analyses(
    status: Optional[str] = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    List all analysis jobs.

    Args:
        status: Filter by status (pending, running, completed, failed)
        limit: Maximum number of results

    Returns:
        List of analysis jobs
    """
    jobs: list[dict[str, Any]] = []

    for analysis_id, job in list(_analysis_jobs.items())[:limit]:
        if status and job["status"].value != status:
            continue

        jobs.append({
            "analysis_id": analysis_id,
            "status": job["status"].value,
            "started_at": job["started_at"].isoformat(),
            "has_result": analysis_id in _analysis_results,
        })

    # Also include completed results not in jobs
    for analysis_id in _analysis_results:
        if analysis_id not in _analysis_jobs:
            result = _analysis_results[analysis_id]
            jobs.append({
                "analysis_id": analysis_id,
                "status": "completed",
                "started_at": result.memo_date.isoformat(),
                "has_result": True,
                "company_name": result.company_name,
            })

    return {
        "total": len(jobs),
        "analyses": jobs[:limit],
    }


# Background task functions


async def _run_analysis(
    analysis_id: str,
    file_path: str,
    company_name_hint: Optional[str],
    additional_context: Optional[str],
    fast_mode: bool,
) -> None:
    """Run analysis in background."""
    try:
        # Update status
        _analysis_jobs[analysis_id]["status"] = AgentStatus.RUNNING

        # Process PDF
        service = get_document_service()
        images, text = await service.process_pdf(file_path)

        if not images and not text:
            raise AnalysisError(
                message="Could not extract content from PDF",
                error_code="EXTRACTION_FAILED",
            )

        # Add additional context to text
        if additional_context:
            text = f"Additional Context:\n{additional_context}\n\n{text}"

        # Create orchestrator with progress callback
        orchestrator = OrchestratorAgent()

        def progress_callback(progress: OrchestratorProgress) -> None:
            _analysis_jobs[analysis_id]["progress"] = progress

        orchestrator.on_progress(progress_callback)

        # Run analysis
        result = await orchestrator.analyze(
            images=images,
            text_content=text,
            company_name_hint=company_name_hint,
            fast_mode=fast_mode,
        )

        # Store result
        _analysis_results[analysis_id] = result
        _analysis_jobs[analysis_id]["status"] = AgentStatus.COMPLETED

        logger.info(f"Background analysis complete: {analysis_id}")

    except Exception as e:
        logger.error(f"Background analysis failed: {e}", exc_info=True)
        _analysis_jobs[analysis_id]["status"] = AgentStatus.FAILED
        _analysis_jobs[analysis_id]["error"] = str(e)


def _get_status_message(status: AgentStatus) -> str:
    """Get human-readable status message."""
    messages = {
        AgentStatus.PENDING: "Analysis queued, waiting to start",
        AgentStatus.RUNNING: "Analysis in progress",
        AgentStatus.COMPLETED: "Analysis complete",
        AgentStatus.FAILED: "Analysis failed",
        AgentStatus.RETRYING: "Retrying after error",
    }
    return messages.get(status, "Unknown status")
