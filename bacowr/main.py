"""
BACOWR Main Application

This module initializes and configures all BACOWR components.
It serves as the main entry point for the application.
"""

import os
import logging
from typing import Optional

from dotenv import load_dotenv

from bacowr.llm.client import LLMClient, LLMProvider
from bacowr.preflight.light_preflight import LightPreflightEngine
from bacowr.preflight.heavy_preflight import HeavyPreflightEngine
from bacowr.storage.filesystem import FileSystemStorage
from bacowr.qa.service import QAService
from bacowr.services.orchestrator import JobOrchestrator

# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

_llm_client: Optional[LLMClient] = None
_light_preflight: Optional[LightPreflightEngine] = None
_heavy_preflight: Optional[HeavyPreflightEngine] = None
_storage: Optional[FileSystemStorage] = None
_qa_service: Optional[QAService] = None
_orchestrator: Optional[JobOrchestrator] = None


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def get_llm_client() -> LLMClient:
    """
    Get or create LLM client instance.

    Returns:
        LLMClient: Configured LLM client

    Raises:
        ValueError: If LLM_API_KEY is not set
    """
    global _llm_client

    if _llm_client is None:
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            raise ValueError(
                "LLM_API_KEY environment variable is required. "
                "Please set it in .env file or environment."
            )

        provider_str = os.getenv("LLM_PROVIDER", "anthropic")
        try:
            provider = LLMProvider(provider_str)
        except ValueError:
            logger.warning(f"Invalid LLM_PROVIDER '{provider_str}', defaulting to anthropic")
            provider = LLMProvider.ANTHROPIC

        model = os.getenv("LLM_MODEL") or None
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4000"))
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

        _llm_client = LLMClient(
            api_key=api_key,
            provider=provider,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        logger.info(f"LLM client initialized: {provider} / {_llm_client.model}")

    return _llm_client


def get_light_preflight() -> LightPreflightEngine:
    """
    Get or create Light Preflight Engine instance.

    Returns:
        LightPreflightEngine: Configured light preflight engine
    """
    global _light_preflight

    if _light_preflight is None:
        timeout = int(os.getenv("PREFLIGHT_TIMEOUT", "30"))
        max_paragraphs = int(os.getenv("PREFLIGHT_MAX_PARAGRAPHS", "3"))
        user_agent = os.getenv("PREFLIGHT_USER_AGENT")

        _light_preflight = LightPreflightEngine(
            timeout=timeout,
            max_paragraphs=max_paragraphs,
            user_agent=user_agent,
        )

        logger.info("Light preflight engine initialized")

    return _light_preflight


def get_heavy_preflight() -> HeavyPreflightEngine:
    """
    Get or create Heavy Preflight Engine instance.

    Returns:
        HeavyPreflightEngine: Configured heavy preflight engine
    """
    global _heavy_preflight

    if _heavy_preflight is None:
        timeout = int(os.getenv("PREFLIGHT_TIMEOUT", "30"))
        max_paragraphs = int(os.getenv("PREFLIGHT_MAX_PARAGRAPHS", "5"))
        user_agent = os.getenv("PREFLIGHT_USER_AGENT")
        serp_api_key = os.getenv("SERP_API_KEY")  # Optional for future

        _heavy_preflight = HeavyPreflightEngine(
            timeout=timeout,
            max_paragraphs=max_paragraphs,
            user_agent=user_agent,
            serp_api_key=serp_api_key,
        )

        logger.info("Heavy preflight engine initialized")

    return _heavy_preflight


def get_storage() -> FileSystemStorage:
    """
    Get or create Storage instance.

    Returns:
        FileSystemStorage: Configured storage layer
    """
    global _storage

    if _storage is None:
        base_path = os.getenv("STORAGE_PATH", "./output")
        _storage = FileSystemStorage(base_path=base_path)
        logger.info(f"Storage initialized: {base_path}")

    return _storage


def get_qa_service() -> QAService:
    """
    Get or create QA Service instance.

    Returns:
        QAService: Configured QA service
    """
    global _qa_service

    if _qa_service is None:
        _qa_service = QAService()
        logger.info("QA service initialized")

    return _qa_service


def get_orchestrator() -> JobOrchestrator:
    """
    Get or create Job Orchestrator instance.

    This function initializes the orchestrator with all required dependencies.

    Returns:
        JobOrchestrator: Configured orchestrator

    Raises:
        ValueError: If required configuration is missing
    """
    global _orchestrator

    if _orchestrator is None:
        # Initialize all dependencies
        llm_client = get_llm_client()
        light_preflight = get_light_preflight()
        heavy_preflight = get_heavy_preflight()
        storage = get_storage()
        qa_service = get_qa_service()

        _orchestrator = JobOrchestrator(
            light_preflight=light_preflight,
            heavy_preflight=heavy_preflight,
            llm_client=llm_client,
            storage=storage,
            qa_service=qa_service,
        )

        logger.info("Job orchestrator initialized with all dependencies (light + heavy preflight)")

    return _orchestrator


# =============================================================================
# APPLICATION INITIALIZATION
# =============================================================================

def initialize_app() -> None:
    """
    Initialize the BACOWR application.

    This function should be called at application startup to ensure
    all components are properly configured.
    """
    logger.info("Initializing BACOWR application...")

    # Validate critical configuration
    if not os.getenv("LLM_API_KEY"):
        logger.warning(
            "LLM_API_KEY not set. "
            "The API will start but article generation will fail. "
            "Please configure .env file."
        )

    # Initialize orchestrator (this will initialize all dependencies)
    try:
        get_orchestrator()
        logger.info("BACOWR application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        logger.warning("API will start but may not be fully functional")


def shutdown_app() -> None:
    """
    Clean shutdown of the BACOWR application.

    This function should be called on application shutdown to clean up resources.
    """
    logger.info("Shutting down BACOWR application...")

    # Reset singleton instances
    global _llm_client, _light_preflight, _heavy_preflight, _storage, _qa_service, _orchestrator
    _llm_client = None
    _light_preflight = None
    _heavy_preflight = None
    _storage = None
    _qa_service = None
    _orchestrator = None

    logger.info("BACOWR application shutdown complete")


# =============================================================================
# CLI ENTRY POINT (for future CLI functionality)
# =============================================================================

def main():
    """
    Main CLI entry point.

    Currently just starts the API server.
    Future versions may include CLI commands for batch processing, etc.
    """
    import uvicorn
    from bacowr.api.server import app

    # Initialize application
    initialize_app()

    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"

    logger.info(f"Starting BACOWR API server on {host}:{port}")

    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
