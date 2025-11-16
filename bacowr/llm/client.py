"""
BACOWR LLM Client

Handles all communication with external LLM APIs (Claude, GPT, etc.).
Provides a clean interface for article generation with error handling and retries.

Key principles:
- Provider-agnostic interface (easy to switch between Claude/GPT)
- Automatic retries on transient errors
- Token usage tracking
- Cost estimation when possible
- No SEO logic here (that's in Preflight)
"""

import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

import httpx

from bacowr.domain.models import LLMResult

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"  # Claude
    OPENAI = "openai"        # GPT
    # Add more providers as needed


# Provider-specific endpoints
PROVIDER_ENDPOINTS = {
    LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
    LLMProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
}

# Default models
DEFAULT_MODELS = {
    LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    LLMProvider.OPENAI: "gpt-4o",
}

# Cost per 1M tokens (approximate, update as pricing changes)
COSTS_PER_MILLION = {
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
}


# ============================================================================
# LLM CLIENT
# ============================================================================

class LLMClient:
    """
    Universal LLM client supporting multiple providers.

    Handles API communication, retries, and result formatting.
    """

    def __init__(
        self,
        api_key: str,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        model: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        timeout: int = 120,
        max_retries: int = 3,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: API key for the provider
            provider: Which LLM provider to use
            model: Specific model name (uses default if not specified)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            timeout: Request timeout in seconds
            max_retries: Number of retries on transient errors
        """
        self.api_key = api_key
        self.provider = provider
        self.model = model or DEFAULT_MODELS[provider]
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

        logger.info(
            f"LLMClient initialized: provider={provider}, "
            f"model={self.model}, max_tokens={max_tokens}"
        )

    # ========================================================================
    # MAIN GENERATION METHOD
    # ========================================================================

    def generate_article(self, prompt: str) -> LLMResult:
        """
        Generate article using LLM.

        Args:
            prompt: Complete structured prompt from Preflight

        Returns:
            LLMResult: Generated article with metadata

        Raises:
            Exception: On API errors or invalid responses
        """
        logger.info(f"Starting article generation with {self.model}")

        start_time = time.time()

        try:
            # Make API call with retries
            response_data = self._call_api_with_retries(prompt)

            # Extract article text and metadata
            article_text = self._extract_article_text(response_data)
            token_usage = self._extract_token_usage(response_data)
            cost_estimate = self._calculate_cost(token_usage)

            elapsed = time.time() - start_time
            logger.info(
                f"Article generated successfully in {elapsed:.2f}s - "
                f"{token_usage.get('output', 0)} tokens"
            )

            return LLMResult(
                article_markdown=article_text,
                used_model=self.model,
                token_usage=token_usage,
                cost_estimate=cost_estimate,
                model_metadata={
                    "provider": self.provider,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "generation_time_seconds": round(elapsed, 2),
                },
                created_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Article generation failed: {str(e)}", exc_info=True)
            raise

    # ========================================================================
    # API COMMUNICATION
    # ========================================================================

    def _call_api_with_retries(self, prompt: str) -> Dict[str, Any]:
        """
        Call LLM API with automatic retries on transient errors.

        Args:
            prompt: Prompt to send

        Returns:
            dict: API response data

        Raises:
            Exception: On persistent errors after all retries
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"API call attempt {attempt}/{self.max_retries}")
                return self._call_api(prompt)

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Timeout on attempt {attempt}: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff

            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    logger.error(f"Client error {e.response.status_code}: {e.response.text}")
                    raise

                # Retry on server errors (5xx)
                last_error = e
                logger.warning(
                    f"Server error {e.response.status_code} on attempt {attempt}"
                )
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {str(e)}")
                raise

        # All retries exhausted
        raise Exception(f"API call failed after {self.max_retries} attempts: {last_error}")

    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """
        Make single API call to LLM provider.

        Args:
            prompt: Prompt to send

        Returns:
            dict: Parsed JSON response

        Raises:
            httpx.HTTPStatusError: On HTTP errors
            httpx.TimeoutException: On timeout
        """
        if self.provider == LLMProvider.ANTHROPIC:
            return self._call_anthropic(prompt)
        elif self.provider == LLMProvider.OPENAI:
            return self._call_openai(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    # ========================================================================
    # PROVIDER-SPECIFIC IMPLEMENTATIONS
    # ========================================================================

    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """
        Call Anthropic Claude API.

        API docs: https://docs.anthropic.com/claude/reference/messages_post
        """
        url = PROVIDER_ENDPOINTS[LLMProvider.ANTHROPIC]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            return response.json()

    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """
        Call OpenAI GPT API.

        API docs: https://platform.openai.com/docs/api-reference/chat
        """
        url = PROVIDER_ENDPOINTS[LLMProvider.OPENAI]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Du är en skicklig SEO-skribent som skriver högkvalitativa artiklar på svenska."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            return response.json()

    # ========================================================================
    # RESPONSE PARSING
    # ========================================================================

    def _extract_article_text(self, response_data: Dict[str, Any]) -> str:
        """
        Extract article text from API response.

        Args:
            response_data: Raw API response

        Returns:
            str: Article text in Markdown

        Raises:
            ValueError: If response format is unexpected
        """
        if self.provider == LLMProvider.ANTHROPIC:
            # Anthropic format: response.content[0].text
            try:
                content = response_data.get("content", [])
                if not content:
                    raise ValueError("Empty content in response")

                text = content[0].get("text", "")
                if not text:
                    raise ValueError("Empty text in response content")

                return text.strip()

            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected Anthropic response format: {e}")

        elif self.provider == LLMProvider.OPENAI:
            # OpenAI format: response.choices[0].message.content
            try:
                choices = response_data.get("choices", [])
                if not choices:
                    raise ValueError("Empty choices in response")

                message = choices[0].get("message", {})
                text = message.get("content", "")
                if not text:
                    raise ValueError("Empty content in message")

                return text.strip()

            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected OpenAI response format: {e}")

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _extract_token_usage(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token usage from API response.

        Args:
            response_data: Raw API response

        Returns:
            dict: Token usage with 'input' and 'output' keys
        """
        try:
            if self.provider == LLMProvider.ANTHROPIC:
                usage = response_data.get("usage", {})
                return {
                    "input": usage.get("input_tokens", 0),
                    "output": usage.get("output_tokens", 0),
                }

            elif self.provider == LLMProvider.OPENAI:
                usage = response_data.get("usage", {})
                return {
                    "input": usage.get("prompt_tokens", 0),
                    "output": usage.get("completion_tokens", 0),
                }

        except Exception as e:
            logger.warning(f"Could not extract token usage: {e}")

        return {"input": 0, "output": 0}

    def _calculate_cost(self, token_usage: Dict[str, int]) -> Optional[float]:
        """
        Calculate estimated cost based on token usage.

        Args:
            token_usage: Token counts

        Returns:
            float: Estimated cost in USD, or None if unknown
        """
        if self.model not in COSTS_PER_MILLION:
            logger.warning(f"No cost data for model {self.model}")
            return None

        try:
            costs = COSTS_PER_MILLION[self.model]
            input_cost = (token_usage["input"] / 1_000_000) * costs["input"]
            output_cost = (token_usage["output"] / 1_000_000) * costs["output"]
            total_cost = input_cost + output_cost

            logger.info(f"Estimated cost: ${total_cost:.4f}")
            return round(total_cost, 4)

        except Exception as e:
            logger.warning(f"Could not calculate cost: {e}")
            return None


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_llm_client_from_env() -> LLMClient:
    """
    Create LLM client from environment variables.

    Expected env vars:
    - LLM_PROVIDER: "anthropic" or "openai" (default: anthropic)
    - LLM_API_KEY: API key (required)
    - LLM_MODEL: Model name (optional, uses default)
    - LLM_MAX_TOKENS: Max tokens (optional, default: 4000)
    - LLM_TEMPERATURE: Temperature (optional, default: 0.7)

    Returns:
        LLMClient: Configured client instance

    Raises:
        ValueError: If required env vars missing
    """
    import os

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable is required")

    provider_str = os.getenv("LLM_PROVIDER", "anthropic")
    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        raise ValueError(f"Invalid LLM_PROVIDER: {provider_str}")

    model = os.getenv("LLM_MODEL")  # Optional
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4000"))
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    return LLMClient(
        api_key=api_key,
        provider=provider,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
