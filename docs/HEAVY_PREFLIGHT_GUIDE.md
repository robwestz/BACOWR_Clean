# Heavy Preflight Guide (v2.0)

Komplett guide för BACOWR Heavy Preflight - avancerad intent-driven innehållsstrategi.

## Översikt

Heavy Preflight implementerar det kompletta "Variabelgiftermål"-ramverket där **alla fyra komponenter är lika viktiga**:

1. **Publisher** - Publikationssajtens naturliga roll
2. **Anchor** - Ankartextens implicerade intention
3. **Target** - Målsidans faktiska innehåll och funktion
4. **Intention** - SERP-signaler och faktisk sökarintention

## Skillnader mot Light Preflight

| Aspekt | Light Preflight | Heavy Preflight |
|--------|----------------|-----------------|
| **SERP-analys** | Ingen | Komplett intent-modellering |
| **Intent-validering** | Ingen | Publisher↔Anchor↔Target↔SERP alignment |
| **Bridge-strategi** | Enkel | Strong/Pivot/Wrapper baserat på alignment |
| **Trust-hierarki** | Ingen | T1-T4 prioritering |
| **LSI-optimering** | Ingen | 6-10 termer i närfönster |
| **QC-extension** | Ingen | Anchor risk, readability, autofix-tracking |
| **Promptkomplexitet** | Grundläggande | Avancerad med alla signals |

## Användn

ing

### API-anrop med Heavy Mode

```bash
curl -X POST http://localhost:8000/jobs/full-run \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "modernalivet.se",
    "target_url": "https://www.rusta.com/sv-se/hem-och-inredning/belysning",
    "anchor_text": "bästa lamporna för",
    "preflight_mode": "heavy"
  }'
```

Notera: `"preflight_mode": "heavy"` aktiverar Heavy Preflight.

### Response med Heavy Extensions

Heavy Preflight returnerar alla standard-fält PLUS:

```json
{
  "id": "...",
  "article_markdown": "...",

  "intent_extension": {
    "serp_intent_primary": "commercial_research",
    "target_page_intent": "transactional - product purchase",
    "anchor_implied_intent": "commercial research",
    "publisher_role_intent": "content hub - informational/editorial",
    "intent_alignment": {
      "anchor_vs_serp": "aligned",
      "target_vs_serp": "partial",
      "publisher_vs_serp": "aligned",
      "overall": "partial"
    },
    "recommended_bridge_type": "pivot",
    "recommended_article_angle": "Thematic bridge connecting publisher focus with...",
    "required_subtopics": ["belysning", "inredning", "produktjämförelse"],
    "forbidden_angles": []
  },

  "serp_research_extension": {
    "main_query": "bästa lamporna för",
    "cluster_queries": ["belysning hemma", "lampor inredning"],
    "serp_sets": [...]
  },

  "links_extension": {
    "bridge_type": "pivot",
    "bridge_theme": "Thematic bridge...",
    "anchor_swap": {
      "performed": false
    },
    "trust_policy": {
      "level": "T3_industry",
      "fallback_used": false
    },
    "compliance": {
      "disclaimers_injected": []
    }
  },

  "qc_extension": {
    "anchor_risk": "low",
    "readability": {
      "lix": null,
      "target_range": "35–45"
    },
    "notes_observability": {
      "signals_used": ["target_entities", "SERP_intent", "trust_source"]
    }
  }
}
```

## Bridge Types

### Strong Bridge

**När:** Alla komponenter är alignade (publisher↔anchor↔target↔SERP)

**Strategi:**
- Direkt semantisk koppling
- Placera länken tidigt i första relevanta sektion
- Minimal "bridge-building" behövs

**Exempel:**
```
Publisher: fitnessmagasin.se
Anchor: "bästa löpskorna 2024"
Target: Sportbutik med löpskor
SERP Intent: Commercial research
→ STRONG: Alla alignade
```

### Pivot Bridge

**När:** Minst en komponent är "partial" men kan bryggås

**Strategi:**
- Etablera tematisk pivot först
- Koppla publisher-fokus med target-tema
- 1-2 stycken kontext innan länk

**Exempel:**
```
Publisher: modernalivet.se (lifestyle)
Anchor: "löparskor"
Target: Sportbutik
SERP Intent: Commercial research
→ PIVOT: Publisher partial aligned, behöver brygga lifestyle→sport
```

### Wrapper Bridge

**När:** Overall alignment är "off" - ingen direkt koppling

**Strategi:**
- Bygg meta-ram först (metodik/risk/innovation/etik)
- 200-300 ord kontext innan länk
- Högsta trust-nivå (T1/T2)
- Triangulering: Publisher ↔ TRUST ↔ Target

**Exempel:**
```
Publisher: nyheter.se (allmän nyhetssajt)
Anchor: "kryptovaluta"
Target: Kryptohandelsplattform
SERP Intent: Transactional
→ WRAPPER: Ingen natural fit, behöver meta-ram om "digital ekonomi" eller "teknologirisker"
```

## Trust Hierarchy (T1-T4)

### T1_public - Högsta prioritet
- Myndigheter (Konsumentverket, Bolagsverket)
- Standardiseringsorgan (ISO, W3C)
- Officiella riktlinjer
- **Svenska prioriteras**

### T2_academic
- Universitet och högskolor
- Forskningsdatabaser
- Peer-reviewed publikationer

### T3_industry
- Branschorganisationer
- Whitepapers
- Tekniska standarder

### T4_media
- Respekterade nyhetshus
- **Endast om T1-T3 saknas**

### Regler
- Aldrig länka till direkta konkurrenter till target
- Undvik user-generated content som primär trust
- Föredra svenska källor för SE-case
- Trust ska stödja dominant SERP intent

## Intent Alignment

Heavy Preflight analyserar alignment mellan alla komponenter:

```
anchor_vs_serp:     ALIGNED | PARTIAL | OFF
target_vs_serp:     ALIGNED | PARTIAL | OFF
publisher_vs_serp:  ALIGNED | PARTIAL | OFF
→ overall:          ALIGNED | PARTIAL | OFF
```

### Besluts-regler

**Overall = ALIGNED:**
- Alla komponenter alignade
- Använd STRONG bridge
- Direkt approach

**Overall = PARTIAL:**
- Minst en är "partial"
- Använd PIVOT bridge
- Bygg tematisk brygga

**Overall = OFF:**
- Minst en är "off"
- Använd WRAPPER bridge
- Kräver meta-ram

## LSI-kvalitet och Närfönster

### Konfiguration
```
Window: ±2 meningar runt länken
Target: 6-10 relevanta termer
```

### Kvalitetskrav
- **Blanda begreppstyper:**
  - Process (t.ex. "verifiering", "optimering")
  - Mått/teori (t.ex. "sannolikhet", "effektivitet")
  - Felkällor (t.ex. "bias", "tolerance")

- **Undvik:**
  - Upprepning av samma rotord
  - Överoptimering runt ankaret
  - Endast synonymer

### Sourcing
1. Hämta från target_url (huvudtema + 3-6 nyckelentiteter)
2. Lägg till pivot-termer om bridge_type är pivot/wrapper
3. Spegla "required_subtopics" från SERP

## Anchor Risk Assessment

### Low Risk
- Brand/generic ankare i naturlig kontext
- LSI-termer och trust i närheten
- Alignment är "aligned"

### Medium Risk
- Generic-ankare utan trust
- Partial-ankare med tveksam passform
- Wrapper bridge med exact match

### High Risk
- Exact match + OFF alignment
- Stark kommersiell intent i svag kontext
- Upprepning av samma ankare

## Autofix Matrix

### Tillåtet utan sign-off:
- Flytta [[LINK]] inom sektion för naturlig placering
- Byta ankartyp (exact→generic, partial→brand)
- Lägga till/byta [[TRUST]]
- Injicera 6-10 LSI-termer
- Infoga branschdisclaimers
- Justera mikrocopy enligt intent

### Kräver sign-off:
- Ändra H1, titel eller metatitel
- Byta huvudtema
- Ta bort sektioner

### Aldrig:
- Fabricera siffror eller citat
- Länka till konkurrerande målsidor
- Ändra intent så att det strider mot overall alignment

## SERP Research (Nuvarande vs Framtid)

### v2.0 (Nu)
- **Simulerad SERP-data** baserat på target metadata
- Intent klassificeras från anchor och target
- Subtopics från H2s och entities
- Fungerar utan extern SERP API

### v2.1 (Framtid)
- Integration med riktig SERP API (SerpApi, Dataforseo)
- Verklig top 10-analys
- Entitetsextraktion från ranking pages
- Konkurrensanalys

För att aktivera riktig SERP i framtiden:
```bash
# .env
SERP_API_KEY=din_serp_api_nyckel
```

## Testexempel

### Exempel 1: Strong Bridge
```bash
curl -X POST http://localhost:8000/jobs/full-run \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "techbloggen.se",
    "target_url": "https://example.com/ai-verktyg",
    "anchor_text": "bästa AI-verktyg 2024",
    "preflight_mode": "heavy"
  }'
```

**Förväntat:**
- `intent_alignment.overall`: "aligned" (tech publisher + tech target + commercial intent)
- `recommended_bridge_type`: "strong"
- Direkt approach i prompten

### Exempel 2: Pivot Bridge
```bash
curl -X POST http://localhost:8000/jobs/full-run \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "heminredning.se",
    "target_url": "https://example.com/smart-home-teknik",
    "anchor_text": "smart teknik",
    "preflight_mode": "heavy"
  }'
```

**Förväntat:**
- `intent_alignment.overall`: "partial" (lifestyle publisher + tech target)
- `recommended_bridge_type`: "pivot"
- Brygga via "smarta hem-lösningar"

### Exempel 3: Wrapper Bridge
```bash
curl -X POST http://localhost:8000/jobs/full-run \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "nyhetssajt.se",
    "target_url": "https://example.com/kryptovaluta-trading",
    "anchor_text": "handla krypto",
    "preflight_mode": "heavy"
  }'
```

**Förväntat:**
- `intent_alignment.overall`: "off" (news + transactional trading)
- `recommended_bridge_type`: "wrapper"
- Meta-ram om "digitala finansmarknader" eller "teknologirisker"

## Felsökning

### Problem: "Heavy preflight not available - falling back to light"

**Lösning:** Kontrollera att Heavy Preflight är korrekt initierad i main.py. Servern ska logga:
```
Job orchestrator initialized with all dependencies (light + heavy preflight)
```

### Problem: Intent alignment alltid "off"

**Orsak:** Simulerad SERP kan ha svårt att klassificera vissa queries.

**Lösning:**
1. Använd tydligare anchor text
2. Vänta på riktig SERP API-integration (v2.1)
3. Kontrollera att target_url är tillgänglig

### Problem: Inga required_subtopics

**Orsak:** Target-sidan saknar H2s eller entities kunde inte extraheras.

**Lösning:** Verifiera att target_url har strukturerat innehåll.

## Best Practices

1. **Använd Heavy mode för:**
   - Komplexa Publisher-Target-relationer
   - När anchor och target inte är uppenbart alignade
   - Transaktionella targets på informativa publishers
   - Reguljerade branscher (finans, gambling, hälsa)

2. **Använd Light mode för:**
   - Enkla, direkta kopplingar
   - Samma nisch (publisher ≈ target)
   - Snabba bulk-jobb där intent är känd

3. **Trust sources:**
   - Alltid inkludera minst 1 trust-källa
   - Wrapper bridge: 2-3 sources
   - Verifiera att källor är svenska om möjligt

4. **QC:**
   - Kontrollera `anchor_risk` i response
   - Vid "high": överväg anchor_swap eller annan vinkel
   - Använd `qc_extension.notes_observability` för debugging

## Kommande Features (v2.1+)

- [ ] Riktig SERP API-integration
- [ ] NER (Named Entity Recognition) för bättre entity extraction
- [ ] LIX-beräkning automatiskt efter generation
- [ ] Batch Heavy Preflight
- [ ] A/B-test av bridge types
- [ ] Publisher voice-profiler från faktiska artiklar

---

**Heavy Preflight är nu redo att användas!**

För support, se huvuddokumentation i [README.md](../README.md) och [DEPLOYMENT.md](../DEPLOYMENT.md).
