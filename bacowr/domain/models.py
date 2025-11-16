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
# HEAVY PREFLIGHT ENUMS (v2.0)
# ============================================================================

class BridgeType(str, Enum):
    """Bridge type for link integration strategy."""
    STRONG = "strong"  # Direct semantic match
    PIVOT = "pivot"    # Thematic bridge needed
    WRAPPER = "wrapper"  # Meta-frame required


class SERPIntent(str, Enum):
    """Primary SERP intent classification."""
    INFO_PRIMARY = "info_primary"
    COMMERCIAL_RESEARCH = "commercial_research"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL_BRAND = "navigational_brand"
    SUPPORT = "support"
    LOCAL = "local"
    MIXED = "mixed"


class AnchorType(str, Enum):
    """Anchor text type classification."""
    EXACT = "exact"
    PARTIAL = "partial"
    BRAND = "brand"
    GENERIC = "generic"


class TrustLevel(str, Enum):
    """Trust source hierarchy levels."""
    T1_PUBLIC = "T1_public"      # Government, standards
    T2_ACADEMIC = "T2_academic"  # Universities, research
    T3_INDUSTRY = "T3_industry"  # Industry orgs, whitepapers
    T4_MEDIA = "T4_media"        # Reputable news


class AlignmentStatus(str, Enum):
    """Intent alignment status."""
    ALIGNED = "aligned"
    PARTIAL = "partial"
    OFF = "off"


class AnchorRisk(str, Enum):
    """Anchor placement risk level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DataConfidence(str, Enum):
    """Confidence level in extracted data."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PageArchetype(str, Enum):
    """SERP page type classification."""
    GUIDE = "guide"
    COMPARISON = "comparison"
    CATEGORY = "category"
    PRODUCT = "product"
    REVIEW = "review"
    TOOL = "tool"
    FAQ = "faq"
    NEWS = "news"
    OFFICIAL = "official"
    OTHER = "other"


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


# ============================================================================
# HEAVY PREFLIGHT EXTENSION MODELS (v2.0)
# ============================================================================

class IntentAlignment(BaseModel):
    """Intent alignment between different components."""
    anchor_vs_serp: AlignmentStatus = AlignmentStatus.ALIGNED
    target_vs_serp: AlignmentStatus = AlignmentStatus.ALIGNED
    publisher_vs_serp: AlignmentStatus = AlignmentStatus.ALIGNED
    overall: AlignmentStatus = AlignmentStatus.ALIGNED


class IntentExtension(BaseModel):
    """Extended intent analysis for Heavy Preflight."""
    serp_intent_primary: SERPIntent = Field(
        ...,
        description="Primary SERP intent from search results"
    )
    serp_intent_secondary: List[str] = Field(
        default_factory=list,
        description="Secondary intents detected"
    )
    target_page_intent: str = Field(
        ...,
        description="Intent derived from target page"
    )
    anchor_implied_intent: str = Field(
        ...,
        description="Intent implied by anchor text"
    )
    publisher_role_intent: str = Field(
        ...,
        description="Intent based on publisher's role"
    )
    intent_alignment: IntentAlignment = Field(
        default_factory=IntentAlignment,
        description="Alignment analysis between components"
    )
    recommended_bridge_type: BridgeType = Field(
        ...,
        description="Recommended bridge type based on intent"
    )
    recommended_article_angle: str = Field(
        ...,
        description="Recommended angle for the article"
    )
    required_subtopics: List[str] = Field(
        default_factory=list,
        description="Required subtopics from SERP analysis"
    )
    forbidden_angles: List[str] = Field(
        default_factory=list,
        description="Angles to avoid"
    )
    notes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional notes and rationale"
    )


class SERPResultSample(BaseModel):
    """Sample of a single SERP result."""
    rank: int
    url: str
    title: str
    detected_page_type: PageArchetype
    snippet: Optional[str] = None
    content_signals: List[str] = Field(default_factory=list)
    key_entities: List[str] = Field(default_factory=list)
    key_subtopics: List[str] = Field(default_factory=list)


class SERPSet(BaseModel):
    """SERP analysis for a single query."""
    query: str
    dominant_intent: SERPIntent
    secondary_intents: List[str] = Field(default_factory=list)
    page_archetypes: List[PageArchetype] = Field(default_factory=list)
    required_subtopics: List[str] = Field(default_factory=list)
    top_results_sample: List[SERPResultSample] = Field(default_factory=list)


class SERPResearchExtension(BaseModel):
    """Complete SERP research data."""
    main_query: str
    cluster_queries: List[str] = Field(default_factory=list)
    queries_rationale: str
    serp_sets: List[SERPSet] = Field(default_factory=list)
    derived_links: Dict[str, Any] = Field(
        default_factory=dict,
        description="Links to intent_extension data"
    )


class AnchorSwap(BaseModel):
    """Anchor text swap information."""
    performed: bool = False
    from_type: Optional[AnchorType] = None
    to_type: Optional[AnchorType] = None
    rationale: str = ""


class NearWindow(BaseModel):
    """LSI near-window configuration."""
    unit: str = "sentence"
    radius: int = 2
    lsi_count: int = 0


class Placement(BaseModel):
    """Link placement details."""
    paragraph_index_in_section: int = 0
    offset_chars: int = 0
    near_window: NearWindow = Field(default_factory=NearWindow)


class TrustPolicy(BaseModel):
    """Trust source policy information."""
    level: TrustLevel
    fallback_used: bool = False
    unresolved: List[str] = Field(default_factory=list)


class Compliance(BaseModel):
    """Compliance and disclaimer information."""
    disclaimers_injected: List[str] = Field(default_factory=list)


class LinksExtension(BaseModel):
    """Extended link metadata for Heavy Preflight."""
    bridge_type: BridgeType
    bridge_theme: Optional[str] = None
    anchor_swap: AnchorSwap = Field(default_factory=AnchorSwap)
    placement: Placement = Field(default_factory=Placement)
    trust_policy: TrustPolicy
    compliance: Compliance = Field(default_factory=Compliance)


class ReadabilityMetrics(BaseModel):
    """Readability measurements."""
    lix: Optional[float] = None
    target_range: str = "35–45"


class NotesObservability(BaseModel):
    """QC observability notes."""
    signals_used: List[str] = Field(default_factory=list)
    autofix_done: bool = False


class QCExtension(BaseModel):
    """Extended QC metadata."""
    anchor_risk: AnchorRisk = AnchorRisk.LOW
    readability: ReadabilityMetrics = Field(default_factory=ReadabilityMetrics)
    thresholds_version: str = "A1"
    notes_observability: NotesObservability = Field(default_factory=NotesObservability)


# ============================================================================
# UPDATED PREFLIGHT RESULT (with extensions)
# ============================================================================

class PreflightResult(BaseModel):
    """
    Complete output from the Preflight Engine.

    Contains all research data and the structured prompt for LLM generation.
    Includes optional Heavy Preflight extensions.
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

    # Heavy Preflight Extensions (v2.0) - Optional
    intent_extension: Optional[IntentExtension] = Field(
        default=None,
        description="Intent analysis (Heavy mode only)"
    )
    serp_research_extension: Optional[SERPResearchExtension] = Field(
        default=None,
        description="SERP research data (Heavy mode only)"
    )
    links_extension: Optional[LinksExtension] = Field(
        default=None,
        description="Link strategy metadata (Heavy mode only)"
    )
    qc_extension: Optional[QCExtension] = Field(
        default=None,
        description="QC metadata (Heavy mode only)"
    )


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
