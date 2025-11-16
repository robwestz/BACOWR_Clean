# BACOWR_ARCHITECTURE

## Syfte

BACOWR (Backlink Content Writer) är ett API-first backend-system som automatiserar skapandet av SEO-optimerade backlink-artiklar.

**Input:**  
- publisher_domain  
- target_url  
- anchor_text  

**Output:**  
- 900–1200 ord lång artikel i Markdown  
- metadata om preflight, LLM och QA-status  

Systemet ska fungera likadant för:
- enskilda körningar (single job)
- batchar (t.ex. 175 länkar per månad)
- både CLI, GUI och Hoppscotch som klienter.

## Översiktligt flöde

1. Klient (GUI / Hoppscotch / CLI) skickar `JobInput` till `POST /jobs/full-run`.
2. API Gateway (FastAPI) validerar input och skickar den till Job Orchestrator.
3. Job Orchestrator anropar Preflight Engine (Light eller Heavy).
4. Preflight Engine hämtar HTML, extraherar metadata och bygger en strukturerad research-prompt.
5. Job Orchestrator skickar research-prompten till LLM-klienten.
6. LLM-klienten pratar med externt LLM-API (Claude/GPT) och får tillbaka artikeln.
7. Job Orchestrator sparar resultatet via Storage-lagret.
8. QA-servicen sätter initial QA-status och flaggar ev. problem.
9. API Gateway returnerar artikel + metadata till klienten.

## Huvudmoduler

- **Domain Models & DTOs** – gemensamma Pydantic-modeller.
- **API Gateway** – FastAPI-app med endpoints.
- **Job & Batch Orchestrator** – kopplar ihop preflight, LLM, storage och QA.
- **Preflight Engine** – Light (metadata) nu, Heavy (SERP) senare.
- **LLM Client** – kapslar alla anrop till Claude/GPT.
- **Storage Layer** – först filesystem, senare Postgres.
- **QA Service** – första lagret av automatiserad kvalitetssäkring.
- **Frontend & Hoppscotch Spec** – dokumenterar hur systemet används externt.

## Tekniska principer

- Python 3.11+.
- FastAPI för HTTP-API.
- Pydantic för datamodeller.
- Rena moduler med tydliga gränssnitt.
- Ingen modul får blanda HTTP, LLM och DB – dessa hålls separata.
