"""
BACOWR API Gateway (FastAPI)

This module provides the HTTP API layer for BACOWR.
All external clients (GUI, Hoppscotch, CLI) interact through this interface.

Key principles:
- No business logic here - only routing and validation
- All heavy lifting delegated to JobOrchestrator
- Clean request/response using Pydantic models
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

from bacowr.domain.models import (
    JobInput,
    JobResponse,
    ArticleRecord,
    Job,
    BatchResponse,
    Batch,
)

# Import factory functions from main
from bacowr.main import get_orchestrator, get_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# APPLICATION FACTORY
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="BACOWR API",
        description="Backlink Content Writer - API-first backend for SEO article generation",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    # Health check
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint."""
        return {
            "status": "healthy",
            "service": "BACOWR API",
            "version": "1.0.0"
        }

    # ========================================================================
    # JOB ENDPOINTS
    # ========================================================================

    @app.post(
        "/jobs/full-run",
        response_model=ArticleRecord,
        status_code=status.HTTP_201_CREATED,
        summary="Generate a single article",
        description="Execute complete pipeline: preflight → LLM → storage → QA"
    )
    async def create_full_run_job(job_input: JobInput) -> ArticleRecord:
        """
        Create and execute a complete article generation job.

        This is the main endpoint for single article generation.

        Args:
            job_input: Job specification (publisher, target, anchor, mode)

        Returns:
            ArticleRecord: Complete article with metadata

        Raises:
            HTTPException: On validation or processing errors
        """
        try:
            logger.info(f"Received full-run request for publisher: {job_input.publisher_domain}")

            # Get orchestrator and run job
            orchestrator = get_orchestrator()
            article_record = orchestrator.run_single_job(job_input)

            logger.info(
                f"Job completed successfully: {article_record.id} - "
                f"{article_record.word_count} words, "
                f"QA: {article_record.qa_status}"
            )

            return article_record

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing job: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error processing job: {str(e)}"
            )

    @app.get(
        "/jobs/{job_id}",
        response_model=JobResponse,
        summary="Get job details",
        description="Retrieve information about a specific job"
    )
    async def get_job(job_id: str) -> JobResponse:
        """
        Retrieve details about a specific job.

        Args:
            job_id: Unique job identifier

        Returns:
            JobResponse: Job details and article if available

        Raises:
            HTTPException: If job not found
        """
        try:
            logger.info(f"Fetching job: {job_id}")

            # Get storage and fetch job/article
            storage = get_storage()
            job = storage.get_job(job_id)
            article = storage.get_article(job_id)

            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )

            return JobResponse(
                job=job,
                article=article,
                message="Job retrieved successfully"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error fetching job: {str(e)}"
            )

    # ========================================================================
    # BATCH ENDPOINTS (Future - T9+)
    # ========================================================================

    @app.post(
        "/batches/create",
        response_model=BatchResponse,
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        summary="Create a new batch (future)",
        description="Create a batch of multiple article generation jobs"
    )
    async def create_batch():
        """
        Create a new batch of jobs.

        NOTE: This is a placeholder for future implementation.
        Batch functionality will be added in modules T9+.
        """
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Batch creation not yet implemented. Planned for future modules."
        )

    @app.post(
        "/batches/{batch_id}/run",
        response_model=BatchResponse,
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        summary="Execute a batch (future)",
        description="Start processing all jobs in a batch"
    )
    async def run_batch(batch_id: str):
        """
        Execute all jobs in a batch.

        NOTE: This is a placeholder for future implementation.
        """
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Batch execution not yet implemented. Planned for future modules."
        )

    @app.get(
        "/batches/{batch_id}",
        response_model=BatchResponse,
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        summary="Get batch details (future)",
        description="Retrieve information about a specific batch"
    )
    async def get_batch(batch_id: str):
        """
        Get details about a batch.

        NOTE: This is a placeholder for future implementation.
        """
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Batch retrieval not yet implemented. Planned for future modules."
        )

    # ========================================================================
    # DIAGNOSTICS & CONFIG
    # ========================================================================

    @app.get("/config")
    async def get_config():
        """
        Get current system configuration (non-sensitive).

        Returns basic system info for debugging.
        """
        return {
            "api_version": "1.0.0",
            "modules_implemented": [
                "T1: Domain Models",
                "T2: API Gateway (current)",
            ],
            "modules_pending": [
                "T3: Job Orchestrator",
                "T4: Preflight Engine",
                "T5: LLM Client",
                "T6: Storage Layer",
                "T7: QA Service",
                "T8: Frontend Spec",
            ],
            "status": "development"
        }


# ============================================================================
# APPLICATION INSTANCE
# ============================================================================

# Create the app instance for ASGI servers (uvicorn, gunicorn, etc.)
app = create_app()


# ============================================================================
# ENTRYPOINT FOR DIRECT EXECUTION
# ============================================================================

if __name__ == "__main__":
    # For direct execution, use the main.py entry point instead
    # which properly initializes all dependencies
    from bacowr.main import main
    main()
