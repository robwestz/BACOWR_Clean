# BACOWR – Modules & Tasks (Master Specification)

Detta dokument beskriver ALLA moduler som ska byggas i projektet samt uppdraget för varje modul.
Varje modul är avsedd att kunna implementeras helt självständigt av en LLM, så länge detta dokument och `BACOWR_ARCHITECTURE.md` tillhandahålls i prompten.

Ingen modul får lägga till funktionalitet utanför sin scope.
Ingen modul får ändra arkitekturen.
Ingen modul får implementera framtida features (det lämnas till T9–T20).

---

## 0. SYSTEMKONTEXT

BACOWR är ett backend-system som automatiserar backlink-artiklar baserat på:
- publisher_domain
- target_url
- anchor_text

Pipeline:
1. Preflight (Light → Heavy senare)
2. LLM-generator (Claude/GPT)
3. Storage
4. QA
5. API för GUI/Hoppscotch
6. Batch-hantering (senare)

Systemet är API-first. CLI, GUI och Hoppscotch anropar samma backend.

Alla moduler följer dessa principer:
- tydlig separering av ansvar
- DTOs/Pydantic-modeller används som gränssnitt
- inga cirkulära beroenden
- moduler pratar genom rena Python-anrop
- inget får implementeras som tillhör en annan modul

---

## T1 – DOMAIN MODELS & DTOs

**Syfte**  
Definiera alla centrala Pydantic-modeller som används överallt i systemet.

**Kontext**  
- Paketet heter `bacowr/`.
- Alla andra moduler importerar modeller härifrån.
- Detta är fundamentet för hela projektet.

**Din uppgift**  
Skapa `bacowr/domain/models.py` med:
- `JobInput`
- `PreflightResult`
- `LLMResult`
- `ArticleRecord`
- `Batch`
- `JobStatus`
- `BatchStatus`

Alla ska ha tydliga docstrings och användningsbeskrivningar.

**Krav**
- Använd Pydantic (v1 eller v2 — välj en).
- Använd korrekta datatyper.
- Inga sidoeffekter, ingen logik.

**Done when**
- Alla modeller finns.
- Andra moduler kan importera dem utan cirkulära beroenden.
- Dokumentation/docstrings finns i varje modell.

---

## T2 – API GATEWAY (FASTAPI)

**Syfte**  
Tillhandahålla systemets externa API. All trafik går genom denna modul.

**Kontext**
- DTOs finns från T1.
- Orkestrator (T3) kommer att implementeras senare.

**Din uppgift**
Skapa `bacowr/api/server.py`:
- initiera FastAPI
- skapa endpoint: `POST /jobs/full-run`
- läs `JobInput` från body
- vidarebefordra anropet till `run_single_job` (dummy tills T3)
- returnera JSON baserat på `ArticleRecord`

**Krav**
- Inga LLM-anrop i denna modul.
- Inga preflight-anrop.
- Endast routing + validering.

**Done when**
- `/jobs/full-run` accepterar JSON och returnerar korrekt struktur.
- `get_app()` finns för ASGI.

---

## T3 – JOB & BATCH ORCHESTRATOR

**Syfte**  
Koppla ihop preflight, LLM och storage. Detta ÄR systemets "hjärna".

**Kontext**
- Anropas från T2.
- Placerad i `bacowr/services/orchestrator.py`.
- Preflight (T4), LLM (T5), Storage (T6) implementeras senare.

**Din uppgift**
Implementera:
- `run_single_job(job_input: JobInput) -> ArticleRecord`
  - anropa preflight (placeholder)
  - anropa LLM (placeholder)
  - anropa storage (placeholder)
  - returnera `ArticleRecord`

- skapa signatur (inte implementation) för:
  - `run_batch(batch_id: int) -> BatchStatus`

**Krav**
- Ingen HTTP-kod.
- Ingen logik utanför orkestrering.
- Dokumentera TODOs där moduler T4–T6 ska kopplas in.

**Done when**
- Orkestratorn kan anropas utan att krascha (även om placeholder lyfter NotImplemented).
- Alla beroenden är tydligt definierade.

---

## T4 – PREFLIGHT ENGINE (LIGHT VERSION)

**Syfte**  
Förbereda data inför LLM: hämta HTML, extrahera metadata, skapa research_prompt.

**Kontext**
- DTOs finns (T1).
- Orkestratorn kommer anropa `run_light_preflight`.

**Din uppgift**
Skapa `bacowr/preflight/light_preflight.py`:
- `run_light_preflight(job: JobInput) -> PreflightResult`
  - hämta HTML från `job.target`
  - extrahera titel, meta description, H1, 1–3 stycken
  - skapa enkla publisher/target-profiler
  - bygg `research_prompt` med tydlig struktur

**Krav**
- Använd `requests` eller `httpx`.
- Hantera fel vid HTML-hämtning.
- Ingen SERP ännu (det är Heavy Preflight i framtiden).
- Ingen LLM i denna modul.

**Done when**
- `PreflightResult` fylls med riktiga värden.
- `research_prompt` är färdig att skickas till LLM.

---

## T5 – LLM CLIENT

**Syfte**  
Kapsla alla anrop till Claude/GPT. Systemet ska kunna generera artiklar via en enskild funktion.

**Kontext**
- `PreflightResult` används som input.
- Orkestratorn (T3) anropar denna modul.

**Din uppgift**
Skapa `bacowr/llm/client.py`:
- `generate_article(preflight: PreflightResult, model_name: str = "claude-sonnet") -> LLMResult`

Implementera:
- bygg API-request baserat på `research_prompt`
- skicka request
- returhantering
- error handling + retry på transient errors
- token-usage när det är tillgängligt

**Krav**
- API-nyckel i environment.
- Ingen preflight, ingen storage här.
- Modul ska vara ren och lätt att byta modell i.

**Done when**
- En enda funktion genererar artikel från prompt.
- Output returneras som korrekt `LLMResult`.

---

## T6 – STORAGE LAYER (FILESYSTEM v1)

**Syfte**  
Lagra allt på disk tills DB implementeras i framtida moduler.

**Kontext**
- Orkestratorn (T3) behöver spara/läsa `ArticleRecord`.

**Din uppgift**
Skapa `bacowr/storage/filesystem.py`:
- `save_article_record(record: ArticleRecord) -> ArticleRecord`
- `load_article_record(id: str) -> ArticleRecord`

Spara:
- `article_markdown` → `output/articles/{id}.md`
- `preflight` → `output/preflight/{id}.json`
- `llm_result` → `output/llm/{id}.json`
- `metadata` → `output/metadata/{id}.json`

**Krav**
- Använd `pathlib.Path`.
- UTF-8.
- Skapa mappar automatiskt.

**Done when**
- Orkestratorn kan spara och läsa artiklar fullt fungerande.

---

## T7 – QA & STATUS SERVICE (V1)

**Syfte**  
Ge systemet första lagret av kvalitetskontroll.

**Kontext**
- Storage finns (T6).
- QA-resultat ska sparas i metadata.

**Din uppgift**
Skapa `bacowr/qa/service.py`:
- `initial_qa_evaluation(record: ArticleRecord) -> ArticleRecord`
  - räkna ord
  - kontrollera anchor-användning
  - sätt `qa_status` och `auto_flags`

- `set_qa_status(record_id: str, new_status: str, comment: Optional[str]) -> None`

**Krav**
- Ingen LLM.
- Ren Python.
- Flaggar sparas i metadata via storage-modulen.

**Done when**
- Varje artikel får QA-status “pending_review” och flaggar.
- Status kan uppdateras manuellt.

---

## T8 – FRONTEND & HOPPSCOTCH SPEC (DOCS)

**Syfte**  
Beskriva API-kontraktet och en minimal frontendlayout så att Hoppscotch och en utvecklare kan använda systemet.

**Kontext**
- `/jobs/full-run` finns.

**Din uppgift**
Skapa `docs/frontend_and_api_contract.md`:
- request/response-exempel för `/jobs/full-run`
- Hoppscotch-exempel
- GUI-skisser (text)
  - tre fält + resultatvy

**Krav**
- Ingen kod, bara dokumentation.
- Ska vara tillräckligt komplett för att någon kan bygga UI utan att fråga dig.

**Done when**
- Dokumentet kan läsas av en utvecklare och användas direkt.

---

## FUTURE MODULES (T9–T20)

Här definieras nya moduler senare, t.ex.:

- Heavy Preflight
- Batch Engine
- Postgres Storage
- LLM Routing Optimizer
- Dashboard
- Customer Portal
- Auto Anchor/Text Generator

Men **ingen av dessa får implementeras innan T1–T8 är klara.**
