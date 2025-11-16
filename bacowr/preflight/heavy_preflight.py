"""
BACOWR Heavy Preflight Engine

Advanced preflight with SERP research, intent analysis, and strategic planning.
Implements the complete "Variabelgiftermål" framework:
- Publisher + Anchor + Target + **Intention** (all equally important)
- Bridge type decision (strong/pivot/wrapper)
- Trust source hierarchy (T1-T4)
- LSI quality and near-window optimization
- Intent alignment validation

Key principles:
- Intent is derived from: target content, SERP signals, publisher role
- Never rely solely on anchor text or manual brief
- All decisions calibrated against modeled intention
"""

import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from bacowr.domain.models import (
    JobInput,
    PreflightResult,
    PublisherProfile,
    TargetProfile,
    PreflightMode,
    # Heavy Preflight models
    IntentExtension,
    IntentAlignment,
    SERPResearchExtension,
    SERPSet,
    SERPResultSample,
    LinksExtension,
    QCExtension,
    # Enums
    BridgeType,
    SERPIntent,
    AnchorType,
    TrustLevel,
    AlignmentStatus,
    AnchorRisk,
    DataConfidence,
    PageArchetype,
    # Sub-models
    AnchorSwap,
    Placement,
    NearWindow,
    TrustPolicy,
    Compliance,
    ReadabilityMetrics,
    NotesObservability,
)

logger = logging.getLogger(__name__)


class HeavyPreflightEngine:
    """
    Heavy Preflight Engine with full SERP research and intent analysis.

    This is the advanced version that implements the complete
    "Variabelgiftermål" framework for SEO content strategy.
    """

    def __init__(
        self,
        timeout: int = 30,
        max_paragraphs: int = 5,
        user_agent: Optional[str] = None,
        serp_api_key: Optional[str] = None,  # Future: real SERP API
    ):
        """
        Initialize Heavy Preflight Engine.

        Args:
            timeout: HTTP timeout in seconds
            max_paragraphs: Max paragraphs to extract from target
            user_agent: Custom User-Agent
            serp_api_key: API key for SERP service (future)
        """
        self.timeout = timeout
        self.max_paragraphs = max_paragraphs
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; BACOWR-Heavy/2.0)"
        )
        self.serp_api_key = serp_api_key

        logger.info("HeavyPreflightEngine initialized")

    # ========================================================================
    # MAIN EXECUTION
    # ========================================================================

    def run(self, job_input: JobInput) -> PreflightResult:
        """
        Execute heavy preflight research with full intent analysis.

        This is the main entry point that orchestrates:
        1. SERP research and intent modeling
        2. Target page deep analysis
        3. Publisher-fit assessment
        4. Bridge type determination
        5. Trust source identification
        6. LSI optimization
        7. QC metadata generation

        Args:
            job_input: Job specification

        Returns:
            PreflightResult: Complete preflight with all extensions

        Raises:
            Exception: On critical errors
        """
        target_url = str(job_input.target_url)
        logger.info(f"Starting HEAVY preflight for: {target_url}")

        try:
            # ================================================================
            # STEP 1: Fetch and analyze target page
            # ================================================================
            html_content = self._fetch_html(target_url)
            target_metadata = self._extract_deep_metadata(html_content, target_url)

            # ================================================================
            # STEP 2: SERP Research (simulated for now - can add real API)
            # ================================================================
            serp_research = self._perform_serp_research(
                anchor_text=job_input.anchor_text,
                target_url=target_url,
                target_metadata=target_metadata
            )

            # ================================================================
            # STEP 3: Intent Analysis - THE CORE OF HEAVY PREFLIGHT
            # ================================================================
            intent_ext = self._analyze_intent(
                job_input=job_input,
                target_metadata=target_metadata,
                serp_research=serp_research
            )

            # ================================================================
            # STEP 4: Determine Bridge Type based on Intent
            # ================================================================
            bridge_type = intent_ext.recommended_bridge_type

            # ================================================================
            # STEP 5: Build Publisher Profile
            # ================================================================
            publisher_profile = self._build_publisher_profile(
                job_input.publisher_domain,
                intent_ext
            )

            # ================================================================
            # STEP 6: Build Target Profile
            # ================================================================
            target_profile = self._build_target_profile(
                target_url,
                target_metadata
            )

            # ================================================================
            # STEP 7: Trust Source Identification
            # ================================================================
            links_ext = self._build_links_extension(
                job_input=job_input,
                bridge_type=bridge_type,
                intent_ext=intent_ext,
                target_metadata=target_metadata
            )

            # ================================================================
            # STEP 8: QC Extension
            # ================================================================
            qc_ext = self._build_qc_extension(
                job_input=job_input,
                intent_ext=intent_ext,
                links_ext=links_ext
            )

            # ================================================================
            # STEP 9: Generate Research Prompt
            # ================================================================
            research_prompt = self._build_research_prompt(
                job_input=job_input,
                publisher_profile=publisher_profile,
                target_profile=target_profile,
                intent_ext=intent_ext,
                links_ext=links_ext,
                serp_research=serp_research
            )

            # ================================================================
            # STEP 10: Assemble Complete PreflightResult
            # ================================================================
            result = PreflightResult(
                publisher_profile=publisher_profile,
                target_profile=target_profile,
                serp_profile=None,  # Legacy field - data is in serp_research_extension
                research_prompt=research_prompt,
                mode=PreflightMode.HEAVY,
                bridge_type=bridge_type.value,
                required_subtopics=intent_ext.required_subtopics,
                created_at=datetime.utcnow(),
                # Heavy Preflight Extensions
                intent_extension=intent_ext,
                serp_research_extension=serp_research,
                links_extension=links_ext,
                qc_extension=qc_ext,
            )

            logger.info(
                f"Heavy preflight complete: bridge_type={bridge_type.value}, "
                f"intent_primary={intent_ext.serp_intent_primary.value}, "
                f"alignment={intent_ext.intent_alignment.overall.value}"
            )

            return result

        except Exception as e:
            logger.error(f"Heavy preflight failed: {str(e)}", exc_info=True)
            raise

    # ========================================================================
    # HTML FETCHING & METADATA EXTRACTION
    # ========================================================================

    def _fetch_html(self, url: str) -> str:
        """Fetch HTML from URL (same as Light Preflight)."""
        logger.info(f"Fetching HTML from: {url}")

        try:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
            }

            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.text

        except Exception as e:
            logger.error(f"Error fetching HTML: {e}")
            raise

    def _extract_deep_metadata(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract deep metadata from target page.

        Beyond basic title/description, also extract:
        - Key entities and topics
        - Content structure
        - Page type indicators
        - Commercial signals
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Basic metadata
        metadata = {
            "title": self._extract_title(soup),
            "meta_description": self._extract_meta_description(soup),
            "h1": self._extract_h1(soup),
            "h2s": self._extract_h2s(soup),
            "paragraphs": self._extract_paragraphs(soup),
            "entities": self._extract_entities(soup, url),
            "commercial_signals": self._detect_commercial_signals(soup),
            "page_type": self._classify_page_type(soup, url),
        }

        return metadata

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.string.strip() if title_tag and title_tag.string else None

    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        meta = soup.find('meta', attrs={'name': 'description'}) or \
               soup.find('meta', attrs={'property': 'og:description'})
        return meta['content'].strip() if meta and meta.get('content') else None

    def _extract_h1(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract H1."""
        h1 = soup.find('h1')
        return h1.get_text(strip=True) if h1 else None

    def _extract_h2s(self, soup: BeautifulSoup) -> List[str]:
        """Extract all H2 headings."""
        h2s = soup.find_all('h2', limit=10)
        return [h2.get_text(strip=True) for h2 in h2s]

    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Extract first N paragraphs."""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) >= 50:
                paragraphs.append(text)
            if len(paragraphs) >= self.max_paragraphs:
                break
        return paragraphs

    def _extract_entities(self, soup: BeautifulSoup, url: str) -> List[str]:
        """
        Extract key entities/topics from page.

        Simple heuristic-based extraction (can be enhanced with NER).
        """
        entities = []

        # Extract from URL path
        path = urlparse(url).path
        path_parts = [p for p in path.split('/') if p and len(p) > 3]
        entities.extend(path_parts[:3])

        # Extract from title and H1/H2s
        title = self._extract_title(soup)
        h1 = self._extract_h1(soup)

        for text in [title, h1]:
            if text:
                # Simple: split and take capitalized words
                words = re.findall(r'\b[A-ZÅÄÖ][a-zåäö]{2,}\b', text)
                entities.extend(words[:5])

        return list(set(entities))[:10]  # Unique, max 10

    def _detect_commercial_signals(self, soup: BeautifulSoup) -> List[str]:
        """Detect commercial intent signals on page."""
        signals = []

        text_lower = soup.get_text().lower()

        # Commercial keywords
        if any(word in text_lower for word in ['köp', 'beställ', 'pris', 'erbjudande']):
            signals.append("transactional_keywords")

        if any(word in text_lower for word in ['jämför', 'bäst', 'topp', 'review']):
            signals.append("comparison_intent")

        # Product indicators
        if soup.find('button', string=re.compile(r'köp|beställ|lägg till', re.I)):
            signals.append("buy_button")

        if soup.find(attrs={"itemprop": "price"}):
            signals.append("structured_pricing")

        return signals

    def _classify_page_type(self, soup: BeautifulSoup, url: str) -> PageArchetype:
        """Classify page type based on content."""
        url_lower = url.lower()
        text_lower = soup.get_text().lower()

        if '/produkt/' in url_lower or '/product/' in url_lower:
            return PageArchetype.PRODUCT

        if any(word in text_lower for word in ['guide', 'how to', 'steg för steg']):
            return PageArchetype.GUIDE

        if any(word in url_lower for word in ['jamfor', 'vs', 'compare']):
            return PageArchetype.COMPARISON

        if '/kategori/' in url_lower or '/category/' in url_lower:
            return PageArchetype.CATEGORY

        return PageArchetype.OTHER

    # ========================================================================
    # SERP RESEARCH (Simulated for now - can integrate real API)
    # ========================================================================

    def _perform_serp_research(
        self,
        anchor_text: str,
        target_url: str,
        target_metadata: Dict[str, Any]
    ) -> SERPResearchExtension:
        """
        Perform SERP research to understand search intent.

        NOTE: This is currently simulated based on target metadata.
        In production, integrate with real SERP API (e.g., Dataforseo, SerpApi).
        """
        logger.info(f"Performing SERP research for: {anchor_text}")

        # Main query is the anchor text
        main_query = anchor_text

        # Generate cluster queries based on anchor + target
        cluster_queries = self._generate_cluster_queries(anchor_text, target_metadata)

        # Simulate SERP analysis
        serp_sets = [
            self._analyze_query_serp(main_query, target_metadata, is_main=True)
        ]

        # Add cluster query analyses
        for cluster_q in cluster_queries[:2]:  # Max 2 cluster queries
            serp_sets.append(
                self._analyze_query_serp(cluster_q, target_metadata, is_main=False)
            )

        return SERPResearchExtension(
            main_query=main_query,
            cluster_queries=cluster_queries,
            queries_rationale=(
                f"Main query from anchor text. Cluster queries derived from "
                f"target page entities and H2 structure."
            ),
            serp_sets=serp_sets,
            derived_links={
                "intent_profile_ref": "intent_extension.serp_intent_primary",
                "required_subtopics_merged_ref": "intent_extension.required_subtopics",
                "data_confidence": "medium"  # Since simulated
            }
        )

    def _generate_cluster_queries(
        self,
        anchor_text: str,
        target_metadata: Dict[str, Any]
    ) -> List[str]:
        """Generate related cluster queries."""
        clusters = []

        # From H2s
        h2s = target_metadata.get("h2s", [])
        if h2s:
            clusters.append(h2s[0])  # First H2 as cluster

        # From entities
        entities = target_metadata.get("entities", [])
        if entities:
            clusters.append(f"{anchor_text} {entities[0]}")

        return clusters[:3]

    def _analyze_query_serp(
        self,
        query: str,
        target_metadata: Dict[str, Any],
        is_main: bool = True
    ) -> SERPSet:
        """
        Analyze SERP for a query (simulated).

        In production: call real SERP API and analyze top 10 results.
        """
        # Determine intent based on query keywords
        dominant_intent = self._classify_query_intent(query)

        # Determine page archetypes likely to rank
        page_archetypes = self._predict_page_archetypes(query, dominant_intent)

        # Extract required subtopics from target metadata
        required_subtopics = self._extract_required_subtopics(
            target_metadata,
            query
        )

        # Simulate top results
        top_results = self._simulate_serp_results(
            query,
            dominant_intent,
            page_archetypes
        )

        return SERPSet(
            query=query,
            dominant_intent=dominant_intent,
            secondary_intents=[],
            page_archetypes=page_archetypes,
            required_subtopics=required_subtopics,
            top_results_sample=top_results
        )

    def _classify_query_intent(self, query: str) -> SERPIntent:
        """Classify search intent from query."""
        q_lower = query.lower()

        # Transactional signals
        if any(word in q_lower for word in ['köp', 'pris', 'billig', 'bäst att köpa']):
            return SERPIntent.TRANSACTIONAL

        # Commercial research
        if any(word in q_lower for word in ['bäst', 'topp', 'jämför', 'review', 'test']):
            return SERPIntent.COMMERCIAL_RESEARCH

        # Navigational
        if any(word in q_lower for word in ['logga in', 'hemsida', 'kontakt']):
            return SERPIntent.NAVIGATIONAL_BRAND

        # Default to informational
        return SERPIntent.INFO_PRIMARY

    def _predict_page_archetypes(
        self,
        query: str,
        intent: SERPIntent
    ) -> List[PageArchetype]:
        """Predict which page types rank for this intent."""
        archetypes = []

        if intent == SERPIntent.INFO_PRIMARY:
            archetypes = [PageArchetype.GUIDE, PageArchetype.FAQ]
        elif intent == SERPIntent.COMMERCIAL_RESEARCH:
            archetypes = [PageArchetype.COMPARISON, PageArchetype.REVIEW]
        elif intent == SERPIntent.TRANSACTIONAL:
            archetypes = [PageArchetype.PRODUCT, PageArchetype.CATEGORY]

        return archetypes

    def _extract_required_subtopics(
        self,
        target_metadata: Dict[str, Any],
        query: str
    ) -> List[str]:
        """Extract required subtopics from target page."""
        subtopics = []

        # Use H2s as subtopics
        h2s = target_metadata.get("h2s", [])
        subtopics.extend(h2s[:5])

        # Add entities as potential subtopics
        entities = target_metadata.get("entities", [])
        subtopics.extend(entities[:3])

        return list(set(subtopics))[:8]

    def _simulate_serp_results(
        self,
        query: str,
        intent: SERPIntent,
        archetypes: List[PageArchetype]
    ) -> List[SERPResultSample]:
        """
        Simulate SERP results (placeholder).

        In production: replace with real SERP API data.
        """
        # Return minimal placeholder
        return [
            SERPResultSample(
                rank=1,
                url="https://example.com/simulated",
                title=f"Simulated result for: {query}",
                detected_page_type=archetypes[0] if archetypes else PageArchetype.OTHER,
                snippet="This is a simulated SERP result. Integrate real SERP API for production.",
                content_signals=["simulated"],
                key_entities=[],
                key_subtopics=[]
            )
        ]

    # ========================================================================
    # INTENT ANALYSIS - THE CORE
    # ========================================================================

    def _analyze_intent(
        self,
        job_input: JobInput,
        target_metadata: Dict[str, Any],
        serp_research: SERPResearchExtension
    ) -> IntentExtension:
        """
        Analyze and model intent from all sources.

        This is the CORE of Heavy Preflight - "Variabelgiftermål".
        Intent MUST be derived from:
        1. Target page actual content
        2. SERP signals (what ranks for related queries)
        3. Publisher's natural role
        4. Anchor text (but NOT relied on alone)
        """
        # 1. SERP Intent (from research)
        serp_intent_primary = serp_research.serp_sets[0].dominant_intent

        # 2. Target Page Intent
        target_page_intent = self._infer_target_intent(target_metadata)

        # 3. Anchor Implied Intent
        anchor_implied_intent = self._infer_anchor_intent(job_input.anchor_text)

        # 4. Publisher Role Intent
        publisher_role_intent = self._infer_publisher_intent(job_input.publisher_domain)

        # 5. Alignment Analysis
        intent_alignment = self._analyze_intent_alignment(
            anchor_implied=anchor_implied_intent,
            target_intent=target_page_intent,
            publisher_intent=publisher_role_intent,
            serp_primary=serp_intent_primary
        )

        # 6. Determine Bridge Type based on alignment
        bridge_type = self._determine_bridge_type(intent_alignment)

        # 7. Recommended angle
        article_angle = self._recommend_article_angle(
            bridge_type,
            intent_alignment,
            serp_research
        )

        # 8. Required subtopics (merged from SERP)
        required_subtopics = self._merge_required_subtopics(serp_research)

        # 9. Forbidden angles (anti-patterns)
        forbidden_angles = self._identify_forbidden_angles(
            intent_alignment,
            target_metadata
        )

        return IntentExtension(
            serp_intent_primary=serp_intent_primary,
            serp_intent_secondary=[],
            target_page_intent=target_page_intent,
            anchor_implied_intent=anchor_implied_intent,
            publisher_role_intent=publisher_role_intent,
            intent_alignment=intent_alignment,
            recommended_bridge_type=bridge_type,
            recommended_article_angle=article_angle,
            required_subtopics=required_subtopics,
            forbidden_angles=forbidden_angles,
            notes={
                "rationale": (
                    f"Intent modeled from: target ({target_page_intent}), "
                    f"SERP ({serp_intent_primary.value}), "
                    f"publisher ({publisher_role_intent}), "
                    f"anchor ({anchor_implied_intent}). "
                    f"Overall alignment: {intent_alignment.overall.value}"
                ),
                "data_confidence": DataConfidence.MEDIUM.value
            }
        )

    def _infer_target_intent(self, metadata: Dict[str, Any]) -> str:
        """Infer intent from target page content."""
        commercial_signals = metadata.get("commercial_signals", [])
        page_type = metadata.get("page_type")

        if "buy_button" in commercial_signals or page_type == PageArchetype.PRODUCT:
            return "transactional - product purchase"

        if "comparison_intent" in commercial_signals:
            return "commercial research - product comparison"

        if page_type == PageArchetype.GUIDE:
            return "informational - how-to guide"

        return "informational - general content"

    def _infer_anchor_intent(self, anchor_text: str) -> str:
        """Infer intent from anchor text."""
        a_lower = anchor_text.lower()

        if any(word in a_lower for word in ['köp', 'beställ', 'pris']):
            return "transactional"

        if any(word in a_lower for word in ['bäst', 'topp', 'jämför']):
            return "commercial research"

        if any(word in a_lower for word in ['hur', 'guide', 'tips']):
            return "informational how-to"

        return "informational"

    def _infer_publisher_intent(self, domain: str) -> str:
        """Infer publisher's natural role/intent."""
        d_lower = domain.lower()

        if any(word in d_lower for word in ['blog', 'magazine', 'tidning']):
            return "content hub - informational/editorial"

        if any(word in d_lower for word in ['shop', 'store', 'butik']):
            return "commerce - transactional"

        return "general publisher - informational"

    def _analyze_intent_alignment(
        self,
        anchor_implied: str,
        target_intent: str,
        publisher_intent: str,
        serp_primary: SERPIntent
    ) -> IntentAlignment:
        """
        Analyze alignment between all intent sources.

        This determines if we can use STRONG bridge or need PIVOT/WRAPPER.
        """
        # Simple heuristic: check if key words align
        def get_intent_category(intent_str: str) -> str:
            if 'transactional' in intent_str.lower():
                return 'transactional'
            if 'commercial' in intent_str.lower():
                return 'commercial'
            return 'informational'

        anchor_cat = get_intent_category(anchor_implied)
        target_cat = get_intent_category(target_intent)
        publisher_cat = get_intent_category(publisher_intent)
        serp_cat = get_intent_category(serp_primary.value)

        # Anchor vs SERP
        anchor_vs_serp = (
            AlignmentStatus.ALIGNED if anchor_cat == serp_cat
            else AlignmentStatus.PARTIAL if anchor_cat in serp_cat or serp_cat in anchor_cat
            else AlignmentStatus.OFF
        )

        # Target vs SERP
        target_vs_serp = (
            AlignmentStatus.ALIGNED if target_cat == serp_cat
            else AlignmentStatus.PARTIAL if target_cat in serp_cat or serp_cat in target_cat
            else AlignmentStatus.OFF
        )

        # Publisher vs SERP
        publisher_vs_serp = (
            AlignmentStatus.ALIGNED if publisher_cat == serp_cat
            else AlignmentStatus.PARTIAL
        )

        # Overall
        if all(s == AlignmentStatus.ALIGNED for s in [anchor_vs_serp, target_vs_serp, publisher_vs_serp]):
            overall = AlignmentStatus.ALIGNED
        elif AlignmentStatus.OFF in [anchor_vs_serp, target_vs_serp, publisher_vs_serp]:
            overall = AlignmentStatus.OFF
        else:
            overall = AlignmentStatus.PARTIAL

        return IntentAlignment(
            anchor_vs_serp=anchor_vs_serp,
            target_vs_serp=target_vs_serp,
            publisher_vs_serp=publisher_vs_serp,
            overall=overall
        )

    def _determine_bridge_type(self, alignment: IntentAlignment) -> BridgeType:
        """
        Determine bridge type based on intent alignment.

        Rules from spec:
        - STRONG: only if no component is 'off'
        - PIVOT: when at least one is 'partial' but can bridge
        - WRAPPER: when overall is 'off' - need meta-frame
        """
        if alignment.overall == AlignmentStatus.ALIGNED:
            return BridgeType.STRONG

        if alignment.overall == AlignmentStatus.OFF:
            return BridgeType.WRAPPER

        return BridgeType.PIVOT

    def _recommend_article_angle(
        self,
        bridge_type: BridgeType,
        alignment: IntentAlignment,
        serp_research: SERPResearchExtension
    ) -> str:
        """Recommend article angle based on bridge type and alignment."""
        if bridge_type == BridgeType.STRONG:
            return f"Direct informational piece focused on {serp_research.main_query}"

        if bridge_type == BridgeType.PIVOT:
            return f"Thematic bridge connecting publisher focus with {serp_research.main_query}"

        # WRAPPER
        return f"Meta-framework (methodology/risk/innovation) that contextualizes {serp_research.main_query}"

    def _merge_required_subtopics(
        self,
        serp_research: SERPResearchExtension
    ) -> List[str]:
        """Merge required subtopics from all SERP sets."""
        all_subtopics = []
        for serp_set in serp_research.serp_sets:
            all_subtopics.extend(serp_set.required_subtopics)

        return list(set(all_subtopics))[:10]

    def _identify_forbidden_angles(
        self,
        alignment: IntentAlignment,
        target_metadata: Dict[str, Any]
    ) -> List[str]:
        """Identify angles to avoid."""
        forbidden = []

        if alignment.overall == AlignmentStatus.OFF:
            forbidden.append("Direct product promotion without context")

        if "transactional_keywords" in target_metadata.get("commercial_signals", []):
            forbidden.append("Pure editorial without acknowledging commercial nature")

        return forbidden

    # ========================================================================
    # LINKS EXTENSION
    # ========================================================================

    def _build_links_extension(
        self,
        job_input: JobInput,
        bridge_type: BridgeType,
        intent_ext: IntentExtension,
        target_metadata: Dict[str, Any]
    ) -> LinksExtension:
        """Build links extension with trust policy and placement."""
        # Determine trust level needed
        trust_level = self._determine_trust_level(bridge_type, intent_ext)

        # Anchor swap analysis
        anchor_swap = self._analyze_anchor_swap(
            job_input.anchor_text,
            bridge_type,
            intent_ext
        )

        return LinksExtension(
            bridge_type=bridge_type,
            bridge_theme=(
                intent_ext.recommended_article_angle
                if bridge_type in [BridgeType.PIVOT, BridgeType.WRAPPER]
                else None
            ),
            anchor_swap=anchor_swap,
            placement=Placement(
                paragraph_index_in_section=1,
                offset_chars=0,
                near_window=NearWindow(
                    unit="sentence",
                    radius=2,
                    lsi_count=8  # Target 6-10 LSI terms
                )
            ),
            trust_policy=TrustPolicy(
                level=trust_level,
                fallback_used=False,
                unresolved=[]
            ),
            compliance=Compliance(
                disclaimers_injected=self._identify_disclaimers(target_metadata)
            )
        )

    def _determine_trust_level(
        self,
        bridge_type: BridgeType,
        intent_ext: IntentExtension
    ) -> TrustLevel:
        """Determine required trust level."""
        if bridge_type == BridgeType.WRAPPER:
            return TrustLevel.T1_PUBLIC  # Highest trust for wrapper

        if intent_ext.serp_intent_primary in [
            SERPIntent.TRANSACTIONAL,
            SERPIntent.COMMERCIAL_RESEARCH
        ]:
            return TrustLevel.T3_INDUSTRY

        return TrustLevel.T4_MEDIA

    def _analyze_anchor_swap(
        self,
        anchor_text: str,
        bridge_type: BridgeType,
        intent_ext: IntentExtension
    ) -> AnchorSwap:
        """Analyze if anchor swap is recommended."""
        # Classify current anchor type
        current_type = self._classify_anchor_type(anchor_text)

        # Determine if swap is beneficial
        if bridge_type == BridgeType.WRAPPER and current_type == AnchorType.EXACT:
            # Wrapper often benefits from generic anchor
            return AnchorSwap(
                performed=True,
                from_type=current_type,
                to_type=AnchorType.GENERIC,
                rationale="Generic anchor more natural in wrapper/meta-frame context"
            )

        return AnchorSwap(performed=False)

    def _classify_anchor_type(self, anchor_text: str) -> AnchorType:
        """Classify anchor text type."""
        # Simple heuristic
        if len(anchor_text.split()) == 1 and anchor_text[0].isupper():
            return AnchorType.BRAND

        if any(word in anchor_text.lower() for word in ['här', 'klicka', 'läs mer']):
            return AnchorType.GENERIC

        if len(anchor_text.split()) <= 3:
            return AnchorType.EXACT

        return AnchorType.PARTIAL

    def _identify_disclaimers(self, target_metadata: Dict[str, Any]) -> List[str]:
        """Identify required disclaimers."""
        disclaimers = []

        # Check for regulated content
        text = " ".join(target_metadata.get("paragraphs", [])).lower()

        if any(word in text for word in ['gambling', 'casino', 'betting']):
            disclaimers.append("gambling")

        if any(word in text for word in ['investment', 'trading', 'crypto']):
            disclaimers.append("finance")

        if any(word in text for word in ['health', 'medical', 'treatment']):
            disclaimers.append("health")

        return disclaimers

    # ========================================================================
    # QC EXTENSION
    # ========================================================================

    def _build_qc_extension(
        self,
        job_input: JobInput,
        intent_ext: IntentExtension,
        links_ext: LinksExtension
    ) -> QCExtension:
        """Build QC extension with risk assessment."""
        # Assess anchor risk
        anchor_risk = self._assess_anchor_risk(
            job_input.anchor_text,
            links_ext.bridge_type,
            intent_ext.intent_alignment
        )

        return QCExtension(
            anchor_risk=anchor_risk,
            readability=ReadabilityMetrics(
                lix=None,  # Will be calculated post-generation
                target_range="35–45"
            ),
            thresholds_version="A1",
            notes_observability=NotesObservability(
                signals_used=[
                    "target_entities",
                    "publisher_profile",
                    "SERP_intent",
                    "trust_source"
                ],
                autofix_done=False
            )
        )

    def _assess_anchor_risk(
        self,
        anchor_text: str,
        bridge_type: BridgeType,
        alignment: IntentAlignment
    ) -> AnchorRisk:
        """Assess risk level of anchor placement."""
        # High risk if:
        # - Exact match + misaligned intent
        # - Wrapper bridge with commercial anchor
        anchor_type = self._classify_anchor_type(anchor_text)

        if anchor_type == AnchorType.EXACT and alignment.overall == AlignmentStatus.OFF:
            return AnchorRisk.HIGH

        if bridge_type == BridgeType.WRAPPER and anchor_type == AnchorType.EXACT:
            return AnchorRisk.MEDIUM

        return AnchorRisk.LOW

    # ========================================================================
    # PROFILE BUILDING
    # ========================================================================

    def _build_publisher_profile(
        self,
        domain: str,
        intent_ext: IntentExtension
    ) -> PublisherProfile:
        """Build publisher profile considering intent."""
        return PublisherProfile(
            domain=domain,
            category="lifestyle",  # Could be enhanced with lookup
            tone="informell, vänlig, engagerande",
            audience="svenska konsumenter",
            notes=f"Intent-baserad profil: {intent_ext.publisher_role_intent}"
        )

    def _build_target_profile(
        self,
        url: str,
        metadata: Dict[str, Any]
    ) -> TargetProfile:
        """Build enhanced target profile."""
        return TargetProfile(
            url=url,
            title=metadata.get("title"),
            meta_description=metadata.get("meta_description"),
            h1=metadata.get("h1"),
            first_paragraphs=metadata.get("paragraphs", []),
            entities=metadata.get("entities")
        )

    # ========================================================================
    # RESEARCH PROMPT BUILDING
    # ========================================================================

    def _build_research_prompt(
        self,
        job_input: JobInput,
        publisher_profile: PublisherProfile,
        target_profile: TargetProfile,
        intent_ext: IntentExtension,
        links_ext: LinksExtension,
        serp_research: SERPResearchExtension
    ) -> str:
        """
        Build comprehensive research prompt with all Heavy Preflight data.

        This is the prompt that goes to the LLM for article generation.
        """
        bridge_instructions = self._get_bridge_instructions(links_ext.bridge_type)

        prompt = f"""# UPPDRAG: Skriv SEO-optimerad artikel enligt Heavy Preflight-specifikation

## VARIABELGIFTERMÅL (Alla lika viktiga)

**Publisher:** {publisher_profile.domain}
**Anchor Text:** {job_input.anchor_text}
**Target URL:** {target_profile.url}
**Intention:** {intent_ext.serp_intent_primary.value}

## INTENT-ANALYS

**SERP Primary Intent:** {intent_ext.serp_intent_primary.value}
**Target Page Intent:** {intent_ext.target_page_intent}
**Anchor Implied Intent:** {intent_ext.anchor_implied_intent}
**Publisher Role Intent:** {intent_ext.publisher_role_intent}

**Intent Alignment:**
- Anchor ↔ SERP: {intent_ext.intent_alignment.anchor_vs_serp.value}
- Target ↔ SERP: {intent_ext.intent_alignment.target_vs_serp.value}
- Publisher ↔ SERP: {intent_ext.intent_alignment.publisher_vs_serp.value}
- **Overall: {intent_ext.intent_alignment.overall.value}**

## BRIDGE-STRATEGI: {links_ext.bridge_type.value.upper()}

{bridge_instructions}

**Rekommenderad vinkel:** {intent_ext.recommended_article_angle}

## MÅLSIDA (TARGET)

**Titel:** {target_profile.title or "N/A"}
**H1:** {target_profile.h1 or "N/A"}
**Meta Description:** {target_profile.meta_description or "N/A"}

**Nyckelentiteter från målsidan:**
{self._format_list(target_profile.entities or [])}

## SERP RESEARCH

**Huvudquery:** {serp_research.main_query}
**Klusterqueries:** {', '.join(serp_research.cluster_queries)}

**Required Subtopics (från SERP-analys):**
{self._format_list(intent_ext.required_subtopics)}

**Förbjudna vinklar:**
{self._format_list(intent_ext.forbidden_angles) if intent_ext.forbidden_angles else "Inga specifika"}

## STRUKTURKRAV

**Längd:** 900-1200 ord

**LSI-kvalitet:**
- 6-10 relevanta semantiska termer i närfönster (±2 meningar runt länken)
- Blanda begreppstyper: process, mått/teori, felkällor
- Täck required subtopics naturligt

**Länkplacering:**
- Placera [[LINK]] i mittpunkt/huvudsektion
- Efter att kontext etablerats
- Omgiven av LSI-termer
- Naturlig integration enligt {links_ext.bridge_type.value}-strategi

**Trust-källor:**
- Trust-nivå: {links_ext.trust_policy.level.value}
- Använd [[TRUST:url]] för referenser
- Prioritera: Myndigheter (T1) > Akademi (T2) > Bransch (T3) > Media (T4)

**Stil & Ton:**
- Ton: {publisher_profile.tone}
- Målgrupp: {publisher_profile.audience}
- Röst: Enligt publisher role - {intent_ext.publisher_role_intent}

**Compliance:**
{self._format_disclaimers(links_ext.compliance.disclaimers_injected)}

## OUTPUT-FORMAT

Ren Markdown med:
- H1 för huvudrubrik
- H2 för sektioner
- Naturliga stycken
- [[LINK]] för backlink (exakt en gång)
- [[TRUST:url]] för trustlänkar
- Ev. disclaimer i avslut

Börja direkt med artikeln - ingen meta-text.
"""

        return prompt.strip()

    def _get_bridge_instructions(self, bridge_type: BridgeType) -> str:
        """Get specific instructions for each bridge type."""
        if bridge_type == BridgeType.STRONG:
            return """
**STRONG Bridge:**
- Direkt semantisk koppling mellan publisher, anchor och target
- Placera länken tidigt i första relevanta huvudsektion
- Minimal "bridge-building" behövs
- Fokusera på substantiell information
"""

        if bridge_type == BridgeType.PIVOT:
            return """
**PIVOT Bridge:**
- Etablera tematisk pivot/övergripande frågeställning först
- Koppla samman publisher-fokus med target-tema
- Bygg semantic bridge innan länkplacering
- 1-2 stycken kontext, sedan länk
"""

        # WRAPPER
        return """
**WRAPPER Bridge:**
- Bygg neutral meta-ram (metodik/risk/innovation/etik)
- Etablera "wrapper context" FÖRST (200-300 ord)
- Placera länken EFTER att ramen är etablerad
- Använd högsta trust-nivå (T1/T2)
- Triangulering: Publisher ↔ TRUST ↔ Target
"""

    def _format_list(self, items: List[str]) -> str:
        """Format list for prompt."""
        if not items:
            return "- (Ingen data)"
        return "\n".join(f"- {item}" for item in items)

    def _format_disclaimers(self, disclaimers: List[str]) -> str:
        """Format disclaimers for prompt."""
        if not disclaimers:
            return "Inga specifika disclaimers krävs."

        disclaimer_texts = {
            "gambling": "Spel om pengar kan skapa beroende. Spela ansvarsfullt.",
            "finance": "Detta är inte finansiell rådgivning. Konsultera expert.",
            "health": "Detta ersätter inte medicinsk rådgivning. Kontakta vårdgivare.",
        }

        return "\n".join(
            f"- {disclaimer_texts.get(d, d)}"
            for d in disclaimers
        )
