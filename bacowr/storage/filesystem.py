"""
BACOWR Storage Layer - Filesystem v1

Simple file-based storage for development and small-scale deployments.
This is v1 - production systems should migrate to PostgreSQL (future module).

Storage structure:
  output/
    ├── jobs/{job_id}.json          # Job records
    ├── articles/{job_id}.md         # Generated articles (Markdown)
    ├── prompts/{job_id}.txt         # Research prompts
    └── metadata/{job_id}.json       # Article metadata

Key principles:
- All writes are atomic (write to temp, then rename)
- UTF-8 encoding everywhere
- Directories created automatically
- Clean error handling
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

from bacowr.domain.models import (
    Job,
    JobInput,
    ArticleRecord,
    JobStatus,
)

logger = logging.getLogger(__name__)


class FileSystemStorage:
    """
    File-based storage implementation.

    Stores jobs, articles, and metadata as files on disk.
    """

    def __init__(self, base_path: str = "./output"):
        """
        Initialize filesystem storage.

        Args:
            base_path: Root directory for all storage (default: ./output)
        """
        self.base_path = Path(base_path)

        # Define subdirectories
        self.jobs_dir = self.base_path / "jobs"
        self.articles_dir = self.base_path / "articles"
        self.prompts_dir = self.base_path / "prompts"
        self.metadata_dir = self.base_path / "metadata"

        # Create all directories
        self._ensure_directories()

        logger.info(f"FileSystemStorage initialized at: {self.base_path.absolute()}")

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def _ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        for directory in [
            self.jobs_dir,
            self.articles_dir,
            self.prompts_dir,
            self.metadata_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    # ========================================================================
    # JOB OPERATIONS
    # ========================================================================

    def create_job(self, job_input: JobInput) -> Job:
        """
        Create a new job record.

        Args:
            job_input: Job specification

        Returns:
            Job: Created job with generated ID
        """
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()

        job = Job(
            id=job_id,
            job_input=job_input,
            status=JobStatus.CREATED,
            batch_id=None,
            created_at=now,
            updated_at=now,
        )

        self._save_job(job)
        logger.info(f"Created job: {job_id}")

        return job

    def update_job(self, job: Job) -> Job:
        """
        Update an existing job record.

        Args:
            job: Job to update

        Returns:
            Job: Updated job
        """
        job.updated_at = datetime.utcnow()
        self._save_job(job)
        logger.debug(f"Updated job: {job.id} - status: {job.status}")

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Retrieve a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job if found, None otherwise
        """
        job_path = self.jobs_dir / f"{job_id}.json"

        if not job_path.exists():
            logger.warning(f"Job not found: {job_id}")
            return None

        try:
            with open(job_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Job(**data)

        except Exception as e:
            logger.error(f"Error reading job {job_id}: {e}", exc_info=True)
            return None

    def _save_job(self, job: Job) -> None:
        """
        Save job to file.

        Args:
            job: Job to save
        """
        job_path = self.jobs_dir / f"{job.id}.json"
        self._write_json(job_path, job.model_dump(mode='json'))

    # ========================================================================
    # ARTICLE OPERATIONS
    # ========================================================================

    def save_article_record(self, record: ArticleRecord) -> ArticleRecord:
        """
        Save complete article record.

        Saves to multiple files:
        - articles/{id}.md - The article content
        - prompts/{id}.txt - The research prompt (if available)
        - metadata/{id}.json - Complete metadata

        Args:
            record: Article record to save

        Returns:
            ArticleRecord: Saved record (unchanged)
        """
        article_id = record.id
        logger.info(f"Saving article record: {article_id}")

        try:
            # Save article Markdown
            article_path = self.articles_dir / f"{article_id}.md"
            self._write_text(article_path, record.article_markdown)

            # Save research prompt if available
            if record.preflight_result:
                prompt_path = self.prompts_dir / f"{article_id}.txt"
                self._write_text(prompt_path, record.preflight_result.research_prompt)

            # Save complete metadata
            metadata_path = self.metadata_dir / f"{article_id}.json"
            metadata = self._build_metadata(record)
            self._write_json(metadata_path, metadata)

            logger.info(
                f"Article saved successfully: {article_id} "
                f"({record.word_count} words)"
            )

            return record

        except Exception as e:
            logger.error(f"Error saving article {article_id}: {e}", exc_info=True)
            raise

    def get_article(self, article_id: str) -> Optional[ArticleRecord]:
        """
        Retrieve an article record by ID.

        Args:
            article_id: Article identifier

        Returns:
            ArticleRecord if found, None otherwise
        """
        metadata_path = self.metadata_dir / f"{article_id}.json"

        if not metadata_path.exists():
            logger.warning(f"Article metadata not found: {article_id}")
            return None

        try:
            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Reconstruct ArticleRecord
            return ArticleRecord(**data)

        except Exception as e:
            logger.error(f"Error reading article {article_id}: {e}", exc_info=True)
            return None

    def load_article_record(self, record_id: str) -> Optional[ArticleRecord]:
        """
        Alias for get_article() for compatibility.

        Args:
            record_id: Article record identifier

        Returns:
            ArticleRecord if found, None otherwise
        """
        return self.get_article(record_id)

    # ========================================================================
    # METADATA HELPERS
    # ========================================================================

    def _build_metadata(self, record: ArticleRecord) -> dict:
        """
        Build metadata dictionary from article record.

        Args:
            record: Article record

        Returns:
            dict: Serializable metadata
        """
        return record.model_dump(mode='json')

    # ========================================================================
    # FILE I/O HELPERS
    # ========================================================================

    def _write_text(self, path: Path, content: str) -> None:
        """
        Write text file atomically.

        Args:
            path: Target file path
            content: Text content to write
        """
        # Write to temporary file first
        temp_path = path.with_suffix(path.suffix + '.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Atomic rename
            temp_path.replace(path)
            logger.debug(f"Wrote text file: {path}")

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def _write_json(self, path: Path, data: dict) -> None:
        """
        Write JSON file atomically.

        Args:
            path: Target file path
            data: Data to serialize
        """
        # Write to temporary file first
        temp_path = path.with_suffix(path.suffix + '.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            # Atomic rename
            temp_path.replace(path)
            logger.debug(f"Wrote JSON file: {path}")

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_all_job_ids(self) -> list[str]:
        """
        Get list of all job IDs.

        Returns:
            list: Job IDs
        """
        job_files = self.jobs_dir.glob("*.json")
        return [f.stem for f in job_files]

    def get_all_article_ids(self) -> list[str]:
        """
        Get list of all article IDs.

        Returns:
            list: Article IDs
        """
        article_files = self.articles_dir.glob("*.md")
        return [f.stem for f in article_files]

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            dict: Storage stats (job count, article count, etc.)
        """
        return {
            "total_jobs": len(list(self.jobs_dir.glob("*.json"))),
            "total_articles": len(list(self.articles_dir.glob("*.md"))),
            "total_prompts": len(list(self.prompts_dir.glob("*.txt"))),
            "storage_path": str(self.base_path.absolute()),
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_storage_from_env() -> FileSystemStorage:
    """
    Create storage instance from environment variables.

    Expected env vars:
    - STORAGE_PATH: Base path for file storage (default: ./output)

    Returns:
        FileSystemStorage: Configured storage instance
    """
    import os

    base_path = os.getenv("STORAGE_PATH", "./output")
    return FileSystemStorage(base_path=base_path)
