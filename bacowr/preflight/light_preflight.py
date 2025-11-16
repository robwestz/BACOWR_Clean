"""
BACOWR Preflight Engine - Light Version

The Light Preflight Engine performs basic research and prompt building:
1. Fetch HTML from target URL
2. Extract metadata (title, meta description, H1, paragraphs)
3. Build publisher and target profiles
4. Generate structured research prompt for LLM

This is v1 - no SERP analysis yet (that's Heavy Preflight in future).

Key principles:
- No LLM calls here (only data gathering)
- Clean error handling for HTTP/parsing failures
- Structured output ready for LLM generation
"""

import logging
from typing import List, Optional
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from bacowr.domain.models import (
    JobInput,
    PreflightResult,
    PublisherProfile,
    TargetProfile,
    PreflightMode,
)

logger = logging.getLogger(__name__)


class LightPreflightEngine:
    """
    Light-weight preflight engine for basic research and prompt building.

    Fetches target page, extracts metadata, and creates structured prompt.
    """

    def __init__(
        self,
        timeout: int = 30,
        max_paragraphs: int = 3,
        user_agent: Optional[str] = None
    ):
        """
        Initialize the preflight engine.

        Args:
            timeout: HTTP request timeout in seconds
            max_paragraphs: Maximum number of paragraphs to extract
            user_agent: Custom User-Agent header (optional)
        """
        self.timeout = timeout
        self.max_paragraphs = max_paragraphs
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; BACOWR/1.0; +https://bacowr.io)"
        )

        logger.info("LightPreflightEngine initialized")

    # ========================================================================
    # MAIN EXECUTION
    # ========================================================================

    def run(self, job_input: JobInput) -> PreflightResult:
        """
        Execute light preflight research.

        Args:
            job_input: Job specification

        Returns:
            PreflightResult: Complete preflight data with research prompt

        Raises:
            Exception: On critical errors (HTTP failure, parsing errors)
        """
        target_url = str(job_input.target_url)
        logger.info(f"Starting light preflight for: {target_url}")

        try:
            # ================================================================
            # STEP 1: Fetch HTML from target
            # ================================================================
            html_content = self._fetch_html(target_url)

            # ================================================================
            # STEP 2: Extract metadata from HTML
            # ================================================================
            metadata = self._extract_metadata(html_content, target_url)

            # ================================================================
            # STEP 3: Build profiles
            # ================================================================
            publisher_profile = self._build_publisher_profile(job_input.publisher_domain)
            target_profile = self._build_target_profile(target_url, metadata)

            # ================================================================
            # STEP 4: Generate research prompt
            # ================================================================
            research_prompt = self._build_research_prompt(
                job_input=job_input,
                publisher_profile=publisher_profile,
                target_profile=target_profile
            )

            # ================================================================
            # STEP 5: Create and return PreflightResult
            # ================================================================
            result = PreflightResult(
                publisher_profile=publisher_profile,
                target_profile=target_profile,
                serp_profile=None,  # Not used in Light mode
                research_prompt=research_prompt,
                mode=PreflightMode.LIGHT,
                bridge_type="informativ",  # Default bridge type
                required_subtopics=[],  # Will be populated in Heavy mode
                created_at=datetime.utcnow()
            )

            logger.info(f"Light preflight complete for: {target_url}")
            return result

        except Exception as e:
            logger.error(f"Preflight failed for {target_url}: {str(e)}", exc_info=True)
            raise

    # ========================================================================
    # HTML FETCHING
    # ========================================================================

    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL.

        Args:
            url: Target URL to fetch

        Returns:
            str: HTML content

        Raises:
            Exception: On HTTP errors or timeout
        """
        logger.info(f"Fetching HTML from: {url}")

        try:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
            }

            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                logger.info(
                    f"HTML fetched successfully: {len(response.text)} chars, "
                    f"status {response.status_code}"
                )

                return response.text

        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching {url}: {str(e)}")
            raise Exception(f"Request timeout for {url}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
            raise Exception(f"HTTP {e.response.status_code} for {url}")
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

    # ========================================================================
    # METADATA EXTRACTION
    # ========================================================================

    def _extract_metadata(self, html: str, url: str) -> dict:
        """
        Extract key metadata from HTML.

        Args:
            html: HTML content
            url: Source URL (for logging)

        Returns:
            dict: Extracted metadata
        """
        logger.info(f"Extracting metadata from HTML")

        try:
            soup = BeautifulSoup(html, 'html.parser')

            metadata = {
                "title": self._extract_title(soup),
                "meta_description": self._extract_meta_description(soup),
                "h1": self._extract_h1(soup),
                "paragraphs": self._extract_paragraphs(soup),
            }

            logger.info(
                f"Metadata extracted: "
                f"title={bool(metadata['title'])}, "
                f"h1={bool(metadata['h1'])}, "
                f"paragraphs={len(metadata['paragraphs'])}"
            )

            return metadata

        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            # Return minimal metadata on parsing errors
            return {
                "title": None,
                "meta_description": None,
                "h1": None,
                "paragraphs": [],
            }

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        return None

    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        meta_tag = soup.find('meta', attrs={'name': 'description'}) or \
                    soup.find('meta', attrs={'property': 'og:description'})
        if meta_tag and meta_tag.get('content'):
            return meta_tag['content'].strip()
        return None

    def _extract_h1(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract first H1 heading."""
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        return None

    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract first N paragraphs from main content.

        Returns:
            List of paragraph texts
        """
        paragraphs = []

        # Find all paragraph tags
        for p_tag in soup.find_all('p'):
            text = p_tag.get_text(strip=True)

            # Skip empty or very short paragraphs
            if len(text) < 50:
                continue

            paragraphs.append(text)

            # Limit to max_paragraphs
            if len(paragraphs) >= self.max_paragraphs:
                break

        return paragraphs

    # ========================================================================
    # PROFILE BUILDING
    # ========================================================================

    def _build_publisher_profile(self, domain: str) -> PublisherProfile:
        """
        Build publisher profile from domain.

        In v1, this is basic. In future versions, we might:
        - Fetch publisher metadata from database
        - Analyze publisher's existing content
        - Use domain categorization service

        Args:
            domain: Publisher domain name

        Returns:
            PublisherProfile: Publisher information
        """
        # Default Swedish lifestyle publisher profile
        # TODO: Enhance with database lookup or config in future versions
        return PublisherProfile(
            domain=domain,
            category="lifestyle",  # Default assumption
            tone="informell, vänlig, engagerande",
            audience="svenska konsumenter intresserade av livsstil, hem och inredning",
            notes="Profilen är genererad automatiskt. Uppdatera manuellt vid behov."
        )

    def _build_target_profile(self, url: str, metadata: dict) -> TargetProfile:
        """
        Build target profile from extracted metadata.

        Args:
            url: Target URL
            metadata: Extracted metadata dict

        Returns:
            TargetProfile: Target information
        """
        return TargetProfile(
            url=url,
            title=metadata.get("title"),
            meta_description=metadata.get("meta_description"),
            h1=metadata.get("h1"),
            first_paragraphs=metadata.get("paragraphs", []),
            entities=None  # Will be populated in Heavy mode with NER
        )

    # ========================================================================
    # RESEARCH PROMPT BUILDING
    # ========================================================================

    def _build_research_prompt(
        self,
        job_input: JobInput,
        publisher_profile: PublisherProfile,
        target_profile: TargetProfile
    ) -> str:
        """
        Build structured research prompt for LLM.

        This is the core prompt that guides article generation.

        Args:
            job_input: Original job input
            publisher_profile: Publisher information
            target_profile: Target page information

        Returns:
            str: Complete structured prompt
        """
        # Build target context section
        target_context = self._build_target_context(target_profile)

        prompt = f"""# UPPDRAG: Skriv SEO-optimerad backlink-artikel

Du ska skriva en artikel som publiceras på **{publisher_profile.domain}** och som naturligt länkar till målet med given anchor text.

## PUBLISHER-PROFIL

**Domän:** {publisher_profile.domain}
**Kategori:** {publisher_profile.category or 'lifestyle'}
**Ton:** {publisher_profile.tone}
**Målgrupp:** {publisher_profile.audience}

## MÅL-URL & ANCHOR TEXT

**Mål-URL:** {target_profile.url}
**Anchor text:** {job_input.anchor_text}

## INFORMATION OM MÅLET

{target_context}

## STRUKTURKRAV

**Längd:** 900-1200 ord

**Struktur:**
1. **Rubrik** (H1) - Ska vara SEO-optimerad och engagerande
2. **Introduktion** (100-150 ord) - Sätt kontexten, väck intresse
3. **Huvudavsnitt** (3-4 stycken med H2-rubriker)
   - Varje avsnitt 150-250 ord
   - Praktisk, relevant information
   - Naturligt flöde mellan avsnitt
4. **Länk-integration**
   - Integrera länken naturligt i löpande text
   - Använd exakt anchor text: "{job_input.anchor_text}"
   - Länka till: {target_profile.url}
   - Länken ska passa kontextuellt och ge läsaren värde
5. **Avslutning** (100-150 ord) - Sammanfatta key points

**Stil & Ton:**
- {publisher_profile.tone}
- Skriv för {publisher_profile.audience}
- Använd "du"-form
- Undvik övertydlig marknadsföring
- Fokusera på värde för läsaren

**SEO:**
- Använd relevanta nyckelord naturligt
- Variera meningar och styckelängd
- Inkludera konkreta exempel och tips
- Skriv för både läsare och sökmotorer

## OUTPUT-FORMAT

Returnera artikeln i ren Markdown:
- H1 för huvudrubrik
- H2 för underrubriker
- Naturlig text med korrekt formatering
- Markdown-länk: [anchor text](url)

Börja direkt med artikeln - ingen inledande text som "Här kommer artikeln" etc.
"""

        return prompt.strip()

    def _build_target_context(self, target_profile: TargetProfile) -> str:
        """
        Build target context section for prompt.

        Args:
            target_profile: Target information

        Returns:
            str: Formatted target context
        """
        sections = []

        if target_profile.title:
            sections.append(f"**Titel:** {target_profile.title}")

        if target_profile.h1:
            sections.append(f"**H1:** {target_profile.h1}")

        if target_profile.meta_description:
            sections.append(f"**Beskrivning:** {target_profile.meta_description}")

        if target_profile.first_paragraphs:
            sections.append("\n**Utdrag från målsidan:**")
            for i, para in enumerate(target_profile.first_paragraphs, 1):
                # Truncate very long paragraphs
                para_text = para if len(para) <= 300 else para[:297] + "..."
                sections.append(f"{i}. {para_text}")

        if not sections:
            sections.append("*(Ingen metadata tillgänglig från målsidan)*")

        return "\n".join(sections)
