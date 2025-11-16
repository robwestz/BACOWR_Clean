BACOWR_SYSTEM_DESIGN.md` 

---

## 1. Flowchart: hela vägen från Hoppscotch/GUI till färdig artikel

Tänk dig de här noderna som boxar i Eraser / XMind:

**Översiktliga noder**

1. Client (Hoppscotch / GUI / CLI)
2. API Gateway (FastAPI)
3. Job Orchestrator
4. Preflight Engine
5. LLM Generator
6. Storage Layer
7. QA & Status
8. Response / Dashboard

### Textversion som du kan mata till en flowchart-generator

```text
Start: User in GUI or Hoppscotch
  ↓
User fills in: publisher_domain, target_url, anchor_text
  ↓
User triggers:
  - in GUI: clicks "Generate Article"
  - in Hoppscotch: runs POST /jobs/full-run
  ↓
Client sends HTTP POST /jobs/full-run to API Gateway
  ↓
API Gateway:
  - validates JSON body
  - creates a Job object (single job or part of a batch)
  - forwards job to Job Orchestrator
  ↓
Job Orchestrator:
  - logs job start
  - calls Preflight Engine with (publisher, target, anchor, mode)
  ↓
Preflight Engine:
  - (Heavy or Light mode)
  - fetches target HTML
  - builds publisher_profile
  - builds target_profile
  - optionally calls SERP service
  - produces research_prompt + preflight_metadata
  ↓
Job Orchestrator:
  - calls LLM Generator with research_prompt
  ↓
LLM Generator:
  - sends request to external LLM API (Claude/GPT)
  - receives article_markdown + model_metadata
  ↓
Job Orchestrator:
  - combines preflight_metadata + article + job info
  - passes data to Storage Layer
  ↓
Storage Layer:
  - writes article_markdown to articles table or .md file
  - writes research_prompt to prompts storage
  - writes metadata (job, batch, customer, model, cost)
  ↓
QA & Status:
  - sets initial QA status = "pending_review"
  - updates job status to "generated"
  ↓
API Gateway builds response DTO:
  - includes article_markdown
  - minimal metadata (job_id, batch_id, model, wordcount)
  ↓
Client receives response:
  - Hoppscotch: shows raw JSON
  - GUI: renders article in editor with buttons "Copy" and "Download .md"
End
```

För **batch-läget** är flödet samma, men med en extra loop:

```text
User (GUI) creates batch via POST /batches/create
  ↓
API creates Batch with N jobs
  ↓
User triggers POST /batches/{id}/run
  ↓
Batch Orchestrator iterates jobs:
   for each job:
     run same full flow: Preflight → LLM → Storage → QA
  ↓
Batch status updated continuously
  ↓
GUI shows progress + links to each article
```

---

## 2. Hur Hoppscotch passar in (konkret)

Hoppscotch är i praktiken **“developer GUI”** mot API:t. Bra för dig när du:

* testar endpoints
* debugger single job / preflight
* kör manuella batchar innan full GUI.

### Hoppscotch-collection (förslag)

Grupper:

1. `Jobs`

   * `POST /jobs/full-run`
   * `GET /jobs/{id}`

2. `Batches`

   * `POST /batches/create`
   * `POST /batches/{id}/run`
   * `GET /batches/{id}`
   * `GET /batches/{id}/jobs`

3. `Diagnostics`

   * `GET /health`
   * `GET /config`
   * `GET /stats/summary`

Exempel request i Hoppscotch för single job:

```json
POST /jobs/full-run
{
  "publisher": "modernalivet.se",
  "target": "https://www.rusta.com/sv-se/hem-och-inredning/belysning",
  "anchor": "bästa lamporna för",
  "mode": "heavy_preflight"
}
```

---

## 3. 8 självständiga moduler (perfekt för “en LLM per del”)

Här är en uppdelning där varje modul kan implementeras separat om du ger den respektive kontrakt. Tanken: alla moduler pratar i princip bara JSON och interna Python-klasser.

---

### **Modul 1 – Contracts & Domain Models**

**Ansvar:**
Definiera allting som gemensamma typer / DTOs:

* `JobInput` (publisher, target, anchor, mode)
* `PreflightResult`
* `LLMResult`
* `ArticleRecord`
* `Batch` / `Job` / `QAStatus`

**Inputs:** ingen (det här är biblioteket).
**Outputs:** Python-klasser + Pydantic-modeller.

👉 *Det här är det första du kan låta en LLM skapa – resten bygger på dessa modeller.*

---

### **Modul 2 – API Gateway (FastAPI app)**

**Ansvar:**

* expose REST-endpoints:

  * `POST /jobs/full-run`
  * `POST /batches/create`
  * `POST /batches/{id}/run`
  * `GET  /jobs/{id}`
  * `GET  /batches/{id}` osv.
* input-validering
* konvertera HTTP↔Domain Models

**Inputs:**

* HTTP requests med JSON (från GUI / Hoppscotch)
* `JobInput`-modell från Modul 1

**Outputs:**

* Anropar Modul 3 (Job Orchestrator)
* Returnerar HTTP-responses med artikel + metadata

---

### **Modul 3 – Job & Batch Orchestrator**

**Ansvar:**

* “Hjärnan” som kopplar samman preflight, LLM och storage
* två huvudsätt:

  * `run_single_job(job_input: JobInput) -> ArticleRecord`
  * `run_batch(batch_id: int) -> BatchStatus`

**Inputs:**

* `JobInput` från Modul 2
* Batchinfo från Modul 5 (Storage)

**Outputs:**

* Preflight-anrop → Modul 4
* LLM-anrop → Modul 5
* Sparar → Modul 6
* Returnerar `ArticleRecord` och batch-status

*En LLM kan bygga denna modul ren som orkestreringskod utan att känna till HTTP eller DB-detaljerna – bara kalla funktioner från andra moduler.*

---

### **Modul 4 – Preflight Engine**

**Ansvar:**

* implementera både Heavy & Light preflight
* kapsla allt som har med SERP / HTML / metadata att göra

**Inputs:**

* `JobInput` (publisher, target, anchor, mode)

**Outputs:**

* `PreflightResult`:

  * `publisher_profile`
  * `target_profile`
  * `serp_profile` (om heavy)
  * `bridge_type`
  * `required_subtopics`
  * `lsi_window`
  * `research_prompt` (strukturerad prompttext)

**Extern koppling:**

* SERP-API / scraper (kan vara egen sub-modul senare)

---

### **Modul 5 – LLM Client**

**Ansvar:**

* prata med Claude/GPT/Gemini via API
* hålla koll på:

  * modellnamn
  * max_tokens
  * retries
  * kostnadsloggning (valfritt)

**Inputs:**

* `research_prompt` (string)
* LLM-konfiguration (modell, max_tokens, temperatur…)

**Outputs:**

* `LLMResult`:

  * `article_markdown`
  * `used_model`
  * `token_usage`
  * ev. `short_summary`

*Kan göras helt generisk – en LLM att skriva en bra python-klient, en annan LLM använder den.*

---

### **Modul 6 – Storage Layer (DB + Filesystem)**

**Ansvar:**

* abstraktion mot databas + filer:

  * spara/läsa `Job`, `Batch`, `ArticleRecord`
  * ev. samband tabeller (customers, publishers…)

**Inputs:**

* `ArticleRecord` från Modul 3
* `Job`/`Batch` data

**Outputs:**

* primärnycklar / id:n
* query-metoder:

  * `get_job(id)`
  * `get_batch(id)`
  * `list_jobs_for_batch(id)`

*Detta kan du låta en LLM göra från bara datamodellerna – resten behöver inte bry sig om om det är SQLite, Postgres eller DuckDB.*

---

### **Modul 7 – QA & Status Service**

**Ansvar:**

* sätta och uppdatera QA-status
* enkla auto-checks:

  * ordlängd
  * täckning av required subtopics
  * om ankaret används korrekt
* lagra manuella QA-beslut (approved / needs_changes)

**Inputs:**

* `ArticleRecord`
* QA-events från GUI (approve/reject)

**Outputs:**

* QA-flaggar
* uppdaterad artikelstatus i DB

---

### **Modul 8 – Frontend & Hoppscotch Integration**

**Ansvar:**

* intern webbapp för skribenter:

  * formulär för single job
  * vy för batchar
  * artikelvisning + QA-knappar
* Hoppscotch-collection:

  * definiera alla endpoints, exempel, auth etc.

**Inputs:**

* API-kontrakt från Modul 2
* JSON-responses (`ArticleRecord`, `BatchStatus`)

**Outputs:**

* UX för skrivteamet
* tester via Hoppscotch under utveckling

---

## 4. Ordning att bygga (om du vill maxa “saker blir faktiskt färdiga”)

Du kan ge varje LLM ett *väldigt avgränsat uppdrag* i denna ordning:

1. **Modul 1 – Contracts & Domain models**
   → Pydantic-modeller + docstrings.

2. **Modul 4 – Preflight Engine v1**
   → Först Light-version (metadata only). Heavy kan komma sen.

3. **Modul 5 – LLM Client**
   → “given a prompt, return text”.

4. **Modul 3 – Job Orchestrator**
   → glue mellan 1,4,5,6. Kan först bara skriva till filer.

5. **Modul 6 – Storage Layer v1 (filesystem)**
   → skriv `.md` + `.json`.

6. **Modul 2 – API Gateway**
   → `POST /jobs/full-run` som anropar Modul 3.

7. **Modul 8 – Hoppscotch & Minimal GUI**
   → bygga formulär som träffar `/jobs/full-run`.

8. **Modul 7 – QA & Batch Engine**
   → bygga ut batch-endpoints och QA-status.

Då kan du redan efter steg 4–5 köra **hela kedjan** från CLI.
Efter steg 6 kan du använda Hoppscotch.
Efter steg 8 har du ett fullt “contentteam-system”.

---

Om du vill kan jag i nästa svar skriva en **kort “spec per modul”** i formen:

* “Uppdrag till LLM för Modul 1”
* “Uppdrag till LLM för Modul 2”
  osv, som du kan klistra direkt in i olika chattfönster.

---

## 🔭 Övergripande syfte för BACOWR-projektet

> **Syfte (övergripande):**
> Bygga ett API-först, modulärt system (“BACOWR – Backlink Content Writer”) som automatiskt genererar SEO-optimerade backlink-artiklar baserat på tre inputs per länk: publisher-domän, target-URL och anchor-text.
> Systemet ska klara både enskilda jobb och stora batchar (t.ex. 175 artiklar/månad), med konsekvent kvalitet, tydlig QA-process och så låg teknisk friktion som möjligt för skribenterna (allt via GUI/API, inget Python för dem).

---

## 🧩 Modul 1 – Contracts & Domain Models

**Syfte:**
Skapa den gemensamma “vokabulären” i koden – tydliga datamodeller för jobb, batchar, preflight, LLM-resultat, artiklar och QA-status. Allt annat bygger på detta.

**Scope:**
✅ Pydantic-modeller / dataklasser
✅ Grundläggande enum: t.ex. `PreflightMode`, `QAStatus`
❌ Ingen business-logik
❌ Ingen DB/HTTP-kod

**Inputs:**

* Övergripande arkitektur (det du redan har)
* Dina egna fältönskemål (du kan lägga till dem före du kör prompten)

**Outputs:**

* `bacowr/domain/models.py` (eller liknande)
* Dokumenterade modeller med type hints

**Done when:**

* Alla centrala begrepp har en modell: JobInput, Job, Batch, PreflightResult, LLMResult, ArticleRecord, QAStatus.
* Modellerna är konsekventa och återanvändbara i övriga moduler.

**Uppdrag till LLM – Modul 1**

```text
Uppdrag: Modul 1 – Domain Models & Contracts

Syfte:
Definiera alla centrala datamodeller och kontrakt för BACOWR-systemet (Backlink Content Writer).
Dessa modeller ska användas av alla andra moduler (API, Orchestrator, Preflight, LLM-klient, Storage, QA).

Gör så här:
1. Läs igenom projektbeskrivningen (BACOWR_ARCHITECTURE.md) och förstå vilka objekt som finns.
2. Skapa en Python-modul, t.ex. bacowr/domain/models.py, som innehåller:
   - Pydantic-modeller (eller dataclasses + pydantic BaseSettings om du vill) för:
     - JobInput (publisher, target, anchor, preflight_mode)
     - Job (id, input, status, created_at, batch_id, etc.)
     - Batch (id, name, status, number_of_jobs, created_at, etc.)
     - PreflightResult (publisher_profile, target_profile, serp_profile, research_prompt, mode, etc.)
     - LLMResult (article_markdown, used_model, token_usage, cost_estimate, etc.)
     - ArticleRecord (id, job_id, batch_id, markdown, metadata)
     - QAStatus / QARecord (status enum + ev. kommentar)
   - Relevanta Enum-klasser: t.ex. JobStatus, BatchStatus, PreflightMode, QAStatus.

Krav:
- Alla modeller ska ha tydliga type hints.
- Lägg in korta docstrings per modell (på engelska eller svenska) som förklarar syftet.
- Inga databas- eller HTTP-detaljer här – detta är rena domänmodeller.
- Inga beroenden på FastAPI eller SQLAlchemy.

Output:
- Visa hela filen bacowr/domain/models.py.
- Om du behöver göra antaganden, kommentera dessa kort i docstrings.
```

---

## 🌐 Modul 2 – API Gateway (FastAPI)

**Syfte:**
Exponera ett stabilt API-lager där GUI/Hoppscotch/CLI kan anropa samma logik (framför allt `/jobs/full-run`).

**Scope:**
✅ FastAPI-app
✅ Endpoints för single job + hämtning av job/batch
❌ Ingen business-logik (den ligger i Orchestrator)
❌ Ingen DB-implementation (använder abstraktioner)

**Inputs:**

* Domain models från Modul 1
* Planerade endpoints (t.ex. `/jobs/full-run`)

**Outputs:**

* `bacowr/api/main.py` eller liknande

**Done when:**

* `POST /jobs/full-run` tar emot JobInput, anropar Orchestrator och returnerar artikel + metadata.
* `GET /jobs/{id}` returnerar job + artikel om finns.

**Uppdrag till LLM – Modul 2**

```text
Uppdrag: Modul 2 – API Gateway (FastAPI)

Syfte:
Skapa en FastAPI-applikation som exponerar BACOWR-funktionalitet via ett rent REST-API.
All business-logik ska ligga i Orchestrator-lagret, inte här.

Gör så här:
1. Använd domänmodellerna i bacowr/domain/models.py.
2. Skapa en FastAPI-app, t.ex. i bacowr/api/main.py.
3. Implementera följande endpoints:
   - POST /jobs/full-run
       Input: JobInput (publisher, target, anchor, preflight_mode)
       Beteende: anropa JobOrchestrator.run_single_job(job_input) och returnera ArticleRecord + metadata.
   - GET /jobs/{job_id}
       Beteende: hämta information om ett jobb (via Storage/Orchestrator) och returnera status + ev. artikel.
4. Lämna hook-punkter för Batch-endpoints men implementera inte batch-logik här (det kommer i en annan modul).

Krav:
- Använd Pydantic-modeller från Modul 1 som request/response.
- Hantera enkla valideringsfel (400) och interna fel (500) med strukturerade svar.
- Flytta all tyngre logik till en JobOrchestrator-klass (som vi bygger i en egen modul); här räcker det att du visar anropet.

Output:
- Visa hela FastAPI-koden (main.py) inklusive import av modeller och orchestrator-gränssnitt.
```

---

## 🧠 Modul 3 – Job & Batch Orchestrator

**Syfte:**
Hjärnan som syr ihop Preflight → LLM → Storage för ett jobb, och loopar det för batchar.

**Scope:**
✅ Synkron körning av single job
✅ Grundstruktur för batch-körning
❌ Ingen HTML/SERP-logik (Preflight)
❌ Ingen LLM-API-kod (LLM Client)
❌ Ingen rå DB-kod (Storage Layer-interface används)

**Inputs:**

* Domain models
* Preflight-interface
* LLM-client-interface
* Storage-interface

**Outputs:**

* `bacowr/orchestration/job_orchestrator.py`

**Done when:**

* `run_single_job(JobInput) -> ArticleRecord` fungerar på abstraktionsnivå (anrop till andra moduler).

**Uppdrag till LLM – Modul 3**

```text
Uppdrag: Modul 3 – Job & Batch Orchestrator

Syfte:
Implementera en central orkestreringsmodul som kopplar ihop Preflight Engine, LLM-klient och Storage.
Den ska kunna köra ett enskilt jobb (single job) och innehålla grundstruktur för batcher.

Gör så här:
1. Skapa filen bacowr/orchestration/job_orchestrator.py.
2. Implementera klassen JobOrchestrator med:
   - __init__(self, preflight_engine, llm_client, storage)
   - run_single_job(self, job_input: JobInput) -> ArticleRecord
       Flöde:
         a) skapa Job-objekt och spara initial status via storage
         b) kör preflight_engine.run(job_input) → PreflightResult
         c) kör llm_client.generate_article(preflight_result.research_prompt) → LLMResult
         d) skapa ArticleRecord, spara via storage
         e) uppdatera jobstatus till "generated"
         f) returnera ArticleRecord
   - (valfritt skelett) run_batch(self, batch_id: int) för framtida implementering.

Krav:
- Använd domänmodeller från Modul 1.
- Inga hårdkodade beroenden – ta preflight_engine, llm_client och storage som abstraktioner (interfaces/protokoll).
- Lägg in tydliga logg-rader (placeholder) för varje steg (preflight, llm, storage).

Output:
- Visa hela koden för JobOrchestrator-klassen.
```

---

## 🔍 Modul 4 – Preflight Engine (Light v1)

**Syfte:**
Minimal version som hämtar HTML, extraherar metadata + struktur och bygger `PreflightResult` + `research_prompt` utan full SERP-pipeline.

**Scope:**
✅ Fetch HTML
✅ Plocka `<title>`, meta description, H1, första paragrafer
✅ Konstruera `PreflightResult` + research_prompt
❌ Ingen SERP-API (kan läggas i Heavy-mode senare)

**Inputs:**

* JobInput
* HTTP-client (requests/httpx)

**Outputs:**

* `bacowr/preflight/light_preflight.py`
* Funktion/class: `run(job_input: JobInput) -> PreflightResult`

**Uppdrag till LLM – Modul 4**

```text
Uppdrag: Modul 4 – Preflight Engine (Light Mode)

Syfte:
Bygga en första, förenklad Preflight Engine som:
- hämtar HTML från target_url
- extraherar viktig metadata
- konstruerar ett PreflightResult-objekt och en strukturerad research_prompt
utan att använda SERP-API eller avancerad klustring.

Gör så här:
1. Skapa filen bacowr/preflight/light_preflight.py.
2. Implementera en klass LightPreflightEngine med:
   - __init__(self, http_client=... valfritt)
   - run(self, job_input: JobInput) -> PreflightResult
3. Steg i run():
   - hämta HTML från job_input.target
   - extrahera:
       • title
       • meta description (om finns)
       • H1
       • de 2–3 första p-taggarna
   - skapa en enkel target_profile (entities kan vara placeholder/None i v1).
   - skapa publisher_profile som placeholder baserat på domain string.
   - bygg research_prompt som en tydlig text med sektioner:
       • UPPDRAG
       • PUBLISHER
       • TARGET
       • STRUKTURKRAV
4. Returnera PreflightResult med:
   - publisher_profile
   - target_profile
   - serp_profile=None (v1)
   - research_prompt (sträng)
   - mode="light"

Krav:
- Använd domänmodellerna från Modul 1.
- Hantera fel (t.ex. HTML-fel) med rimliga placeholders och loggning.
- Inga SERP-anrop i denna modul.

Output:
- Visa hela filen light_preflight.py.
```

---

## 🤖 Modul 5 – LLM Client

**Syfte:**
Ett rent lager som pratar med Claude/GPT osv. Tar en prompt → ger tillbaka artikeltext + metadata.

**Scope:**
✅ HTTP-anrop till LLM
✅ Modellkonfiguration (modellnamn, max_tokens)
❌ Ingen SEO-logik
❌ Ingen prompt-byggnad (kommer från Preflight)

**Uppdrag till LLM – Modul 5**

```text
Uppdrag: Modul 5 – LLM Client

Syfte:
Skapa en ren klientmodul som anropar en LLM API (Claude/GPT) med en given prompt och returnerar artikeltext + metadata.

Gör så här:
1. Skapa filen bacowr/llm/client.py.
2. Implementera klassen LLMClient med:
   - __init__(self, api_key: str, base_url: str, model: str, max_tokens: int = 3000)
   - generate_article(self, prompt: str) -> LLMResult
3. generate_article ska:
   - bygga en request-body för vald LLM (du kan anta t.ex. Claude Messages API eller OpenAI Chat API; välj en och håll den ren).
   - skicka HTTP POST
   - hantera statuskoder, ev. retries (enkel variant)
   - skriva ut/returnera LLMResult med:
       • article_markdown (själva texten)
       • used_model
       • token_usage (om finns)
       • cost_estimate (kan vara None i v1)

Krav:
- Ingen SEO-logik.
- Alla API-nycklar ska komma utifrån (env-var eller parameter), inte hårdkodas.
- Lägg till TODO-kommentar om hur man byter mellan olika modeller (Claude/GPT) i framtiden.

Output:
- Visa hela filen client.py.
```

---

## 💾 Modul 6 – Storage Layer (v1 – Filesystem)

**Syfte:**
Första version som inte kräver DB, bara sparar / hämtar jobb + artiklar till filer.

**Scope:**
✅ Skriva `.md`, `.json`
✅ Grundläggande `Job`/`ArticleRecord`-lagring
❌ Ingen riktig DB (det kommer senare)

**Uppdrag till LLM – Modul 6**

```text
Uppdrag: Modul 6 – Storage Layer (Filesystem v1)

Syfte:
Implementera en enkel lagringsmodul som sparar prompts, artiklar och metadata till filer.
Detta är v1 innan vi lägger på en riktig databas.

Gör så här:
1. Skapa filen bacowr/storage/filesystem.py.
2. Implementera klassen FileSystemStorage med metoder:
   - create_job(job_input: JobInput) -> Job
   - update_job(job: Job) -> Job
   - save_article(job: Job, preflight: PreflightResult, llm: LLMResult) -> ArticleRecord
   - get_job(job_id: str) -> Job | None
   - get_article(job_id: str) -> ArticleRecord | None
3. Lagringsstruktur:
   - root: ./output/
     - jobs/{job_id}.json
     - prompts/{job_id}.txt
     - articles/{job_id}.md
     - metadata/{job_id}.json

Krav:
- Använd domänmodeller (Job, ArticleRecord, etc.).
- Se till att kataloger skapas automatiskt.
- Ingen databaskod – allt är filer.

Output:
- Visa hela filen filesystem.py.
```

---

## 🧪 Modul 7 – QA & Status Service (v1)

**Syfte:**
Ge varje artikel en QA-status + enkla auto-kontroller.

**Scope:**
✅ QA-statusfält
✅ Enkla automatiska checks (ordlängd, anchor finns)
❌ Ingen GUI här (det kommer i frontend)

**Uppdrag till LLM – Modul 7**

```text
Uppdrag: Modul 7 – QA & Status Service (v1)

Syfte:
Införa en första QA-nivå där varje artikel får:
- en status (pending, approved, needs_changes)
- enkla auto-checks (t.ex. ordlängd, att anchor-texten finns i artikeln).

Gör så här:
1. Skapa filen bacowr/qa/service.py.
2. Implementera klassen QAService med:
   - auto_evaluate(article: ArticleRecord, job: Job, preflight: PreflightResult) -> QARecord
   - set_status(job_id: str, status: QAStatus, comment: Optional[str]) -> QARecord
3. Auto-checks (v1):
   - markera warning om ordantal < 800.
   - markera error om anchor_text inte förekommer i article_markdown.
   - ev. enkla notiser (TODO: SERP-basera QA senare).

Krav:
- Använd domänmodeller (QAStatus, QARecord).
- Inga beroenden på GUI.

Output:
- Visa hela filen service.py.
```

---

## 🖼 Modul 8 – Frontend & Hoppscotch Spec (API-kontrakt)

**Syfte:**
Definiera exakt hur GUI och Hoppscotch ska prata med API:t. Inte full frontendkod, utan en tydlig specifikation + ev. enkel HTML/JS-mock.

**Scope:**
✅ OpenAPI-/JSON-kontrakt
✅ Exempelrequest/response
✅ Enkel HTML-mock om du vill
❌ Inget stort frontendramverk ännu

**Uppdrag till LLM – Modul 8**

```text
Uppdrag: Modul 8 – Frontend & Hoppscotch Spec

Syfte:
Definiera hur en enkel intern GUI samt Hoppscotch ska anropa BACOWR-API:t.
Målet är att en skribent ska kunna:
- fylla i publisher, target, anchor
- klicka "Generate Article"
- se färdig artikel.

Gör så här:
1. Skapa en specifikationsfil, t.ex. docs/frontend_api_spec.md.
2. Beskriv:
   - Endpoint: POST /jobs/full-run
     - Request JSON-exempel
     - Response JSON-exempel (article_markdown, job_id, metadata)
   - Endpoint: GET /jobs/{id}
   - Hur en minimal HTML-form skulle se ut (3 inputs + submit) och vilket fetch-anrop den gör.
3. (Valfritt) Skapa en enkel statisk HTML-sida i src/frontend/mock.html som:
   - har 3 input-fält
   - gör ett fetch-anrop till /jobs/full-run
   - visar resultatet i en <textarea> eller <pre>.

Krav:
- Fokus på kontrakt, inte styling.
- Gör det lätt att sätta upp en riktig frontend senare (React/Vue/whatever).

Output:
- Visa innehållet i docs/frontend_api_spec.md.
- Visa ev. mock.html om du skapar den.
```

---

Vill du, kan jag nästa steg:

* paketera allt detta till **ett komplett `MODULES_AND_TASKS.md`** så du bara behöver lägga filen i repot och börja beta av modul för modul.
