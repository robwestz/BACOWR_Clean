"""
BACOWR Job & Batch Orchestrator

The orchestrator is the "brain" of BACOWR. It coordinates the entire pipeline:
1. Preflight (research & prompt building)
2. LLM generation
3. Storage
4. QA evaluation

Key principles:
- No HTTP code here (that's in API Gateway)
- No direct LLM calls (that's in LLM Client)
- No HTML/SERP logic (that's in Preflight)
- Pure orchestration and coordination
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from bacowr.domain.models import (
    JobInput,
    Job,
    ArticleRecord,
    JobStatus,
    BatchStatus,
    PreflightResult,
    LLMResult,
    QAStatus,
)

logger = logging.getLogger(__name__)


class JobOrchestrator:
    """
    Central orchestrator for article generation jobs.

    Coordinates the flow: Preflight → LLM → Storage → QA
    """

    def __init__(
        self,
        preflight_engine=None,
        llm_client=None,
        storage=None,
        qa_service=None
    ):
        """
        Initialize orchestrator with dependencies.

        Args:
            preflight_engine: Preflight engine instance (T4)
            llm_client: LLM client instance (T5)
            storage: Storage layer instance (T6)
            qa_service: QA service instance (T7)

        Note:
            All dependencies are optional during development.
            They will be required once respective modules are implemented.
        """
        self.preflight_engine = preflight_engine
        self.llm_client = llm_client
        self.storage = storage
        self.qa_service = qa_service

        logger.info("JobOrchestrator initialized")

    # ========================================================================
    # SINGLE JOB EXECUTION
    # ========================================================================

    def run_single_job(self, job_input: JobInput) -> ArticleRecord:
        """
        Execute complete pipeline for a single article generation job.

        Flow:
        1. Create job record
        2. Run preflight (research & prompt)
        3. Generate article via LLM
        4. Save to storage
        5. Run QA evaluation
        6. Return complete article record

        Args:
            job_input: Job specification from client

        Returns:
            ArticleRecord: Complete article with metadata

        Raises:
            ValueError: If required dependencies not available
            Exception: On processing errors
        """
        job_id = str(uuid.uuid4())
        logger.info(f"Starting job {job_id} for publisher: {job_input.publisher_domain}")

        try:
            # ================================================================
            # STEP 1: Create and save initial job record
            # ================================================================
            job = Job(
                id=job_id,
                job_input=job_input,
                status=JobStatus.CREATED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            if self.storage:
                logger.info(f"[{job_id}] Saving initial job record")
                job = self.storage.create_job(job_input)
            else:
                logger.warning(f"[{job_id}] Storage not available - using in-memory job")

            # ================================================================
            # STEP 2: Run Preflight (research & prompt building)
            # ================================================================
            logger.info(f"[{job_id}] Starting preflight ({job_input.preflight_mode})")
            job.status = JobStatus.PREFLIGHT_RUNNING
            if self.storage:
                self.storage.update_job(job)

            if self.preflight_engine:
                preflight_result = self.preflight_engine.run(job_input)
                logger.info(f"[{job_id}] Preflight complete")
            else:
                # TODO: Remove this placeholder after T4 is implemented
                logger.warning(f"[{job_id}] Preflight engine not available - using placeholder")
                preflight_result = self._create_placeholder_preflight(job_input)

            job.status = JobStatus.PREFLIGHT_COMPLETE
            if self.storage:
                self.storage.update_job(job)

            # ================================================================
            # STEP 3: Generate article via LLM
            # ================================================================
            logger.info(f"[{job_id}] Starting LLM generation")
            job.status = JobStatus.LLM_RUNNING
            if self.storage:
                self.storage.update_job(job)

            if self.llm_client:
                llm_result = self.llm_client.generate_article(
                    preflight_result.research_prompt
                )
                logger.info(f"[{job_id}] LLM generation complete ({llm_result.used_model})")
            else:
                # TODO: Remove this placeholder after T5 is implemented
                logger.warning(f"[{job_id}] LLM client not available - using placeholder")
                llm_result = self._create_placeholder_llm_result()

            job.status = JobStatus.GENERATED
            if self.storage:
                self.storage.update_job(job)

            # ================================================================
            # STEP 4: Create article record and save
            # ================================================================
            logger.info(f"[{job_id}] Creating article record")

            # Calculate word count
            word_count = len(llm_result.article_markdown.split())

            article_record = ArticleRecord(
                id=job_id,
                job_id=job_id,
                batch_id=job.batch_id,
                article_markdown=llm_result.article_markdown,
                job_input=job_input,
                preflight_result=preflight_result,
                llm_result=llm_result,
                qa_status=QAStatus.PENDING_REVIEW,
                qa_flags=[],
                word_count=word_count,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            if self.storage:
                logger.info(f"[{job_id}] Saving article to storage")
                article_record = self.storage.save_article_record(article_record)
            else:
                logger.warning(f"[{job_id}] Storage not available - article not persisted")

            # ================================================================
            # STEP 5: Run QA evaluation
            # ================================================================
            logger.info(f"[{job_id}] Running QA evaluation")
            job.status = JobStatus.QA_PENDING

            if self.qa_service:
                article_record = self.qa_service.initial_qa_evaluation(article_record)
                logger.info(
                    f"[{job_id}] QA complete - status: {article_record.qa_status}, "
                    f"flags: {article_record.qa_flags}"
                )
            else:
                # TODO: Remove this placeholder after T7 is implemented
                logger.warning(f"[{job_id}] QA service not available - using basic checks")
                article_record = self._basic_qa_check(article_record)

            # Update final job status
            if article_record.qa_status == QAStatus.APPROVED:
                job.status = JobStatus.QA_APPROVED
            elif article_record.qa_status == QAStatus.NEEDS_CHANGES:
                job.status = JobStatus.QA_NEEDS_CHANGES
            else:
                job.status = JobStatus.QA_PENDING

            if self.storage:
                self.storage.update_job(job)
                # Save updated article record with QA results
                self.storage.save_article_record(article_record)

            # ================================================================
            # DONE: Return complete article record
            # ================================================================
            logger.info(
                f"[{job_id}] Job complete - "
                f"{word_count} words, "
                f"QA: {article_record.qa_status}"
            )

            return article_record

        except Exception as e:
            # Handle errors
            logger.error(f"[{job_id}] Job failed: {str(e)}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            if self.storage:
                self.storage.update_job(job)
            raise

    # ========================================================================
    # BATCH EXECUTION (Future - T9+)
    # ========================================================================

    def run_batch(self, batch_id: str) -> BatchStatus:
        """
        Execute all jobs in a batch.

        NOTE: This is a placeholder for future implementation.
        Batch processing will be added in modules T9+.

        Args:
            batch_id: ID of the batch to execute

        Returns:
            BatchStatus: Final batch status

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        logger.warning(f"Batch execution requested for {batch_id} but not yet implemented")
        raise NotImplementedError(
            "Batch execution is planned for future modules (T9+). "
            "Use run_single_job() for individual articles."
        )

    # ========================================================================
    # PLACEHOLDER METHODS (Remove after T4-T7 are complete)
    # ========================================================================

    def _create_placeholder_preflight(self, job_input: JobInput) -> PreflightResult:
        """
        Create a minimal preflight result for testing.

        TODO: Remove this after T4 is implemented.
        """
        from bacowr.domain.models import PublisherProfile, TargetProfile

        return PreflightResult(
            publisher_profile=PublisherProfile(
                domain=job_input.publisher_domain,
                tone="informell, vänlig",
                audience="svenska konsumenter"
            ),
            target_profile=TargetProfile(
                url=str(job_input.target_url),
                title="[Placeholder - implement T4 for real data]",
                h1="[Placeholder]",
                first_paragraphs=[]
            ),
            research_prompt=f"""
# UPPDRAG
Skriv en SEO-optimerad artikel (900-1200 ord) för {job_input.publisher_domain}.

# PUBLISHER
- Domän: {job_input.publisher_domain}
- Målgrupp: svenska konsumenter
- Ton: informell, vänlig

# TARGET
- URL: {job_input.target_url}
- Anchor text: {job_input.anchor_text}

# STRUKTURKRAV
- Titel med SEO-fokus
- Introduktion (100-150 ord)
- 3-4 huvudavsnitt
- Naturlig länk med anchor text: {job_input.anchor_text}
- Sammanfattning

[PLACEHOLDER PROMPT - implement T4 for full research-based prompt]
            """.strip(),
            mode=job_input.preflight_mode,
            bridge_type="informativ",
            required_subtopics=[],
            created_at=datetime.utcnow()
        )

    def _create_placeholder_llm_result(self) -> LLMResult:
        """
        Create a minimal LLM result for testing.

        TODO: Remove this after T5 is implemented.
        """
        return LLMResult(
            article_markdown="""
# Placeholder Article

This is a placeholder article generated by the orchestrator.

Implement T5 (LLM Client) to generate real articles using Claude or GPT.

The article should be 900-1200 words with proper structure and SEO optimization.

## Section 1

Lorem ipsum dolor sit amet, consectetur adipiscing elit.

## Section 2

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

## Sammanfattning

This is a test article.
            """.strip(),
            used_model="placeholder-v1",
            token_usage={"input": 0, "output": 0},
            cost_estimate=0.0,
            model_metadata={"note": "Placeholder - implement T5 for real generation"},
            created_at=datetime.utcnow()
        )

    def _basic_qa_check(self, article_record: ArticleRecord) -> ArticleRecord:
        """
        Run basic QA checks when QA service is not available.

        TODO: Remove this after T7 is implemented.
        """
        flags = []

        # Check word count
        if article_record.word_count and article_record.word_count < 800:
            flags.append("word_count_low")

        # Check if anchor text is in article
        anchor = article_record.job_input.anchor_text.lower()
        article_text = article_record.article_markdown.lower()
        if anchor not in article_text:
            flags.append("anchor_text_missing")

        article_record.qa_flags = flags

        # Set status based on flags
        if len(flags) == 0:
            article_record.qa_status = QAStatus.APPROVED
        else:
            article_record.qa_status = QAStatus.NEEDS_CHANGES

        return article_record
