"""
BACOWR QA & Status Service

Automated quality assurance for generated articles.
Performs automatic checks and manages QA status lifecycle.

QA checks (v1):
- Word count (target: 900-1200 words)
- Anchor text presence
- Basic structure validation

Future enhancements (v2+):
- SERP-based topic coverage
- Readability scoring
- Keyword density analysis
- Link placement quality

Key principles:
- No LLM calls here (pure rule-based checks)
- Clear, actionable feedback
- Support for manual QA workflow
"""

import logging
import re
from typing import Optional, List
from datetime import datetime

from bacowr.domain.models import (
    ArticleRecord,
    QAStatus,
    QARecord,
)

logger = logging.getLogger(__name__)


# ============================================================================
# QA THRESHOLDS
# ============================================================================

WORD_COUNT_MIN = 900
WORD_COUNT_MAX = 1200
WORD_COUNT_WARNING_MIN = 800
WORD_COUNT_WARNING_MAX = 1400


class QAService:
    """
    Quality assurance service for article evaluation.

    Performs automated checks and manages QA status.
    """

    def __init__(self):
        """Initialize QA service."""
        logger.info("QAService initialized")

    # ========================================================================
    # AUTOMATIC EVALUATION
    # ========================================================================

    def initial_qa_evaluation(self, article_record: ArticleRecord) -> ArticleRecord:
        """
        Perform initial automated QA evaluation.

        This is called immediately after article generation.
        Sets QA status and flags based on automated checks.

        Args:
            article_record: Article to evaluate

        Returns:
            ArticleRecord: Updated record with QA status and flags
        """
        logger.info(f"Running initial QA for article: {article_record.id}")

        flags = []

        # ================================================================
        # CHECK 1: Word count
        # ================================================================
        word_count_flags = self._check_word_count(
            article_record.article_markdown,
            article_record.word_count
        )
        flags.extend(word_count_flags)

        # ================================================================
        # CHECK 2: Anchor text presence
        # ================================================================
        anchor_flags = self._check_anchor_text(
            article_record.article_markdown,
            article_record.job_input.anchor_text
        )
        flags.extend(anchor_flags)

        # ================================================================
        # CHECK 3: Target URL presence
        # ================================================================
        url_flags = self._check_target_url(
            article_record.article_markdown,
            str(article_record.job_input.target_url)
        )
        flags.extend(url_flags)

        # ================================================================
        # CHECK 4: Basic structure
        # ================================================================
        structure_flags = self._check_structure(article_record.article_markdown)
        flags.extend(structure_flags)

        # ================================================================
        # DETERMINE QA STATUS
        # ================================================================
        qa_status = self._determine_qa_status(flags)

        # Update article record
        article_record.qa_flags = flags
        article_record.qa_status = qa_status
        article_record.updated_at = datetime.utcnow()

        logger.info(
            f"QA evaluation complete: {article_record.id} - "
            f"status={qa_status}, flags={len(flags)}"
        )

        return article_record

    # ========================================================================
    # INDIVIDUAL CHECKS
    # ========================================================================

    def _check_word_count(
        self,
        article_text: str,
        word_count: Optional[int] = None
    ) -> List[str]:
        """
        Check if word count is within acceptable range.

        Args:
            article_text: Article content
            word_count: Pre-calculated word count (optional)

        Returns:
            list: QA flags
        """
        flags = []

        # Calculate word count if not provided
        if word_count is None:
            word_count = len(article_text.split())

        logger.debug(f"Word count: {word_count}")

        # Critical errors
        if word_count < WORD_COUNT_WARNING_MIN:
            flags.append(f"word_count_too_low_{word_count}")
        elif word_count > WORD_COUNT_WARNING_MAX:
            flags.append(f"word_count_too_high_{word_count}")

        # Warnings (not ideal but acceptable)
        elif word_count < WORD_COUNT_MIN:
            flags.append(f"word_count_slightly_low_{word_count}")
        elif word_count > WORD_COUNT_MAX:
            flags.append(f"word_count_slightly_high_{word_count}")

        return flags

    def _check_anchor_text(self, article_text: str, anchor_text: str) -> List[str]:
        """
        Check if anchor text is present in article.

        Args:
            article_text: Article content
            anchor_text: Expected anchor text

        Returns:
            list: QA flags
        """
        flags = []

        # Case-insensitive search
        article_lower = article_text.lower()
        anchor_lower = anchor_text.lower()

        if anchor_lower not in article_lower:
            flags.append("anchor_text_missing")
            logger.warning(f"Anchor text not found: '{anchor_text}'")
        else:
            # Check if it's in a Markdown link
            link_pattern = rf'\[([^\]]*{re.escape(anchor_lower)}[^\]]*)\]\([^\)]+\)'
            if not re.search(link_pattern, article_lower):
                flags.append("anchor_text_not_linked")
                logger.warning(f"Anchor text found but not in link: '{anchor_text}'")

        return flags

    def _check_target_url(self, article_text: str, target_url: str) -> List[str]:
        """
        Check if target URL is present in article.

        Args:
            article_text: Article content
            target_url: Expected target URL

        Returns:
            list: QA flags
        """
        flags = []

        if target_url not in article_text:
            flags.append("target_url_missing")
            logger.warning(f"Target URL not found: {target_url}")

        return flags

    def _check_structure(self, article_text: str) -> List[str]:
        """
        Check basic article structure.

        Validates:
        - Has H1 heading
        - Has at least 2 H2 headings
        - Has paragraphs

        Args:
            article_text: Article content

        Returns:
            list: QA flags
        """
        flags = []

        # Check for H1
        if not re.search(r'^#\s+.+', article_text, re.MULTILINE):
            flags.append("missing_h1")

        # Check for H2s
        h2_count = len(re.findall(r'^##\s+.+', article_text, re.MULTILINE))
        if h2_count < 2:
            flags.append(f"insufficient_h2_headings_{h2_count}")

        # Check for paragraphs
        paragraphs = [
            p for p in article_text.split('\n\n')
            if p.strip() and not p.strip().startswith('#')
        ]
        if len(paragraphs) < 3:
            flags.append(f"insufficient_paragraphs_{len(paragraphs)}")

        return flags

    # ========================================================================
    # STATUS DETERMINATION
    # ========================================================================

    def _determine_qa_status(self, flags: List[str]) -> QAStatus:
        """
        Determine QA status based on flags.

        Logic:
        - No flags → APPROVED
        - Only warnings → PENDING_REVIEW
        - Critical errors → NEEDS_CHANGES

        Args:
            flags: List of QA flags

        Returns:
            QAStatus: Determined status
        """
        if not flags:
            return QAStatus.APPROVED

        # Critical flags that require changes
        critical_flags = [
            "anchor_text_missing",
            "target_url_missing",
            "word_count_too_low",
            "word_count_too_high",
            "missing_h1",
        ]

        has_critical = any(
            any(flag.startswith(critical) for critical in critical_flags)
            for flag in flags
        )

        if has_critical:
            return QAStatus.NEEDS_CHANGES
        else:
            return QAStatus.PENDING_REVIEW

    # ========================================================================
    # MANUAL QA OPERATIONS
    # ========================================================================

    def set_qa_status(
        self,
        job_id: str,
        new_status: QAStatus,
        comment: Optional[str] = None,
        reviewed_by: Optional[str] = None
    ) -> QARecord:
        """
        Manually set QA status for an article.

        This is called by human reviewers to approve or reject articles.

        Args:
            job_id: Job/article identifier
            new_status: New QA status
            comment: Optional reviewer comment
            reviewed_by: Optional reviewer identifier

        Returns:
            QARecord: QA record with updated status

        Note:
            In v1, this just creates the record. In future versions,
            this should also update the storage layer.
        """
        logger.info(
            f"Setting QA status for {job_id}: {new_status} "
            f"(reviewer: {reviewed_by})"
        )

        qa_record = QARecord(
            job_id=job_id,
            status=new_status,
            auto_flags=[],  # Flags were set during initial evaluation
            manual_comment=comment,
            reviewed_by=reviewed_by,
            reviewed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )

        # TODO: Integrate with storage layer to persist QA updates
        logger.warning(
            "QA record created but not persisted - "
            "integrate with storage layer in future version"
        )

        return qa_record

    def approve_article(
        self,
        job_id: str,
        reviewed_by: Optional[str] = None
    ) -> QARecord:
        """
        Approve an article (shorthand for set_qa_status).

        Args:
            job_id: Job/article identifier
            reviewed_by: Reviewer identifier

        Returns:
            QARecord: Approval record
        """
        return self.set_qa_status(
            job_id=job_id,
            new_status=QAStatus.APPROVED,
            comment="Article approved",
            reviewed_by=reviewed_by
        )

    def reject_article(
        self,
        job_id: str,
        reason: str,
        reviewed_by: Optional[str] = None
    ) -> QARecord:
        """
        Reject an article (shorthand for set_qa_status).

        Args:
            job_id: Job/article identifier
            reason: Rejection reason
            reviewed_by: Reviewer identifier

        Returns:
            QARecord: Rejection record
        """
        return self.set_qa_status(
            job_id=job_id,
            new_status=QAStatus.REJECTED,
            comment=reason,
            reviewed_by=reviewed_by
        )

    def request_changes(
        self,
        job_id: str,
        requested_changes: str,
        reviewed_by: Optional[str] = None
    ) -> QARecord:
        """
        Request changes to an article (shorthand for set_qa_status).

        Args:
            job_id: Job/article identifier
            requested_changes: Description of needed changes
            reviewed_by: Reviewer identifier

        Returns:
            QARecord: Request record
        """
        return self.set_qa_status(
            job_id=job_id,
            new_status=QAStatus.NEEDS_CHANGES,
            comment=requested_changes,
            reviewed_by=reviewed_by
        )

    # ========================================================================
    # REPORTING
    # ========================================================================

    def get_qa_summary(self, article_record: ArticleRecord) -> dict:
        """
        Get human-readable QA summary.

        Args:
            article_record: Article to summarize

        Returns:
            dict: QA summary
        """
        return {
            "article_id": article_record.id,
            "qa_status": article_record.qa_status,
            "total_flags": len(article_record.qa_flags),
            "flags": article_record.qa_flags,
            "word_count": article_record.word_count,
            "word_count_status": self._get_word_count_status(article_record.word_count),
            "has_anchor": "anchor_text_missing" not in article_record.qa_flags,
            "has_target_url": "target_url_missing" not in article_record.qa_flags,
            "recommendation": self._get_recommendation(article_record),
        }

    def _get_word_count_status(self, word_count: Optional[int]) -> str:
        """Get word count status label."""
        if not word_count:
            return "unknown"
        elif word_count < WORD_COUNT_WARNING_MIN:
            return "too_low"
        elif word_count > WORD_COUNT_WARNING_MAX:
            return "too_high"
        elif WORD_COUNT_MIN <= word_count <= WORD_COUNT_MAX:
            return "optimal"
        else:
            return "acceptable"

    def _get_recommendation(self, article_record: ArticleRecord) -> str:
        """Get QA recommendation."""
        if article_record.qa_status == QAStatus.APPROVED:
            return "Article is ready for publication"
        elif article_record.qa_status == QAStatus.NEEDS_CHANGES:
            return "Article requires changes before publication"
        else:
            return "Article needs manual review"


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_qa_service() -> QAService:
    """
    Create QA service instance.

    Returns:
        QAService: Configured service instance
    """
    return QAService()
