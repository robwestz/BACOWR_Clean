"""
BACOWR Domain Models & DTOs

This module contains all core data models used throughout the BACOWR system.
All models use Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# ENUMS
# ============================================================================

class JobStatus(str, Enum):
    """Status values for individual jobs."""
    CREATED = "created"
    PREFLIGHT_RUNNING = "preflight_running"
    PREFLIGHT_COMPLETE = "preflight_complete"
    LLM_RUNNING = "llm_running"
    GENERATED = "generated"
    QA_PENDING = "qa_pending"
    QA_APPROVED = "qa_approved"
    QA_NEEDS_CHANGES = "qa_needs_changes"
    FAILED = "failed"


class BatchStatus(str, Enum):
    """Status values for batches."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class PreflightMode(str, Enum):
    """Preflight engine operation modes."""
    LIGHT = "light"  # Metadata only, no SERP
    HEAVY = "heavy"  # Full SERP analysis (future)


class QAStatus(str, Enum):
    """Quality assurance status values."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    NEEDS_CHANGES = "needs_changes"
    REJECTED = "rejected"


# ============================================================================
# INPUT MODELS
# ============================================================================

class JobInput(BaseModel):
    """
    Input data for a single article generation job.

    This is what clients (GUI/API/CLI) send to initiate article creation.
    """
    publisher_domain: str = Field(
        ...,
        description="Domain where the article will be published (e.g., 'modernalivet.se')"
    )
    target_url: HttpUrl = Field(
        ...,
        description="URL that the article should link to (backlink target)"
    )
    anchor_text: str = Field(
        ...,
        description="The anchor text for the backlink"
    )
    preflight_mode: PreflightMode = Field(
        default=PreflightMode.LIGHT,
        description="Which preflight mode to use (light or heavy)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "publisher_domain": "modernalivet.se",
                "target_url": "https://www.rusta.com/sv-se/hem-och-inredning/belysning",
                "anchor_text": "bästa lamporna för",
                "preflight_mode": "light"
            }
        }


# ============================================================================
# PREFLIGHT MODELS
# ============================================================================

class PublisherProfile(BaseModel):
    """Profile information about the publisher domain."""
    domain: str
    category: Optional[str] = None
    tone: str = "informell, vänlig"
    audience: str = "svenska konsumenter"
    notes: Optional[str] = None


class TargetProfile(BaseModel):
    """Extracted information about the target URL."""
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    first_paragraphs: List[str] = Field(default_factory=list)
    entities: Optional[List[str]] = Field(
        default=None,
        description="Key entities/topics extracted from target (future)"
    )


class SERPProfile(BaseModel):
    """SERP analysis data (Heavy Preflight only - future)."""
    query: str
    top_results: List[Dict[str, Any]] = Field(default_factory=list)
    required_subtopics: List[str] = Field(default_factory=list)
    lsi_keywords: List[str] = Field(default_factory=list)


class PreflightResult(BaseModel):
    """
    Complete output from the Preflight Engine.

    Contains all research data and the structured prompt for LLM generation.
    """
    publisher_profile: PublisherProfile
    target_profile: TargetProfile
    serp_profile: Optional[SERPProfile] = None
    research_prompt: str = Field(
        ...,
        description="The complete, structured prompt ready for LLM"
    )
    mode: PreflightMode
    bridge_type: Optional[str] = Field(
        default="informativ",
        description="Type of content bridge (informativ, guide, jämförelse, etc.)"
    )
    required_subtopics: List[str] = Field(
        default_factory=list,
        description="Subtopics that should be covered"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# LLM MODELS
# ============================================================================

class LLMResult(BaseModel):
    """
    Output from LLM generation.

    Contains the generated article and metadata about the generation process.
    """
    article_markdown: str = Field(
        ...,
        description="The complete article in Markdown format (900-1200 words)"
    )
    used_model: str = Field(
        ...,
        description="Name/ID of the LLM model used (e.g., 'claude-sonnet-3.5')"
    )
    token_usage: Optional[Dict[str, int]] = Field(
        default=None,
        description="Token counts (input/output) if available"
    )
    cost_estimate: Optional[float] = Field(
        default=None,
        description="Estimated cost in USD if calculable"
    )
    model_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional model-specific metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# STORAGE & RECORD MODELS
# ============================================================================

class Job(BaseModel):
    """
    Represents a single article generation job with its full lifecycle.
    """
    id: str = Field(
        ...,
        description="Unique identifier for this job"
    )
    job_input: JobInput
    status: JobStatus = Field(default=JobStatus.CREATED)
    batch_id: Optional[str] = Field(
        default=None,
        description="ID of parent batch if this job is part of one"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class ArticleRecord(BaseModel):
    """
    Complete record of a generated article with all associated data.

    This is the primary output object returned to clients.
    """
    id: str = Field(
        ...,
        description="Unique identifier (typically same as job_id)"
    )
    job_id: str
    batch_id: Optional[str] = None

    # The core content
    article_markdown: str

    # Original input
    job_input: JobInput

    # Generation metadata
    preflight_result: Optional[PreflightResult] = None
    llm_result: Optional[LLMResult] = None

    # QA information
    qa_status: QAStatus = Field(default=QAStatus.PENDING_REVIEW)
    qa_flags: List[str] = Field(
        default_factory=list,
        description="Automated quality flags (e.g., 'word_count_low', 'anchor_missing')"
    )
    qa_comment: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metrics
    word_count: Optional[int] = None


class Batch(BaseModel):
    """
    Represents a batch of multiple article generation jobs.

    Used for processing large sets of backlinks (e.g., 175 links per month).
    """
    id: str = Field(
        ...,
        description="Unique identifier for this batch"
    )
    name: str = Field(
        ...,
        description="Human-readable name for the batch"
    )
    description: Optional[str] = None

    status: BatchStatus = Field(default=BatchStatus.CREATED)

    total_jobs: int = Field(
        ...,
        description="Total number of jobs in this batch"
    )
    completed_jobs: int = Field(
        default=0,
        description="Number of successfully completed jobs"
    )
    failed_jobs: int = Field(
        default=0,
        description="Number of failed jobs"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============================================================================
# QA MODELS
# ============================================================================

class QARecord(BaseModel):
    """
    Quality assurance evaluation record for an article.
    """
    job_id: str
    status: QAStatus
    auto_flags: List[str] = Field(
        default_factory=list,
        description="Automatically detected issues"
    )
    manual_comment: Optional[str] = Field(
        default=None,
        description="Human reviewer comment"
    )
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class JobResponse(BaseModel):
    """Standard API response for job-related endpoints."""
    job: Job
    article: Optional[ArticleRecord] = None
    message: Optional[str] = None


class BatchResponse(BaseModel):
    """Standard API response for batch-related endpoints."""
    batch: Batch
    jobs: Optional[List[Job]] = None
    message: Optional[str] = None
