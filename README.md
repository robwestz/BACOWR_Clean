# BACOWR – Backlink Content Writer

**Ett komplett API-first backend-system för att automatisera skapandet av SEO-optimerade backlink-artiklar.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🚀 Översikt

BACOWR automatiserar hela processen för att skapa högkvalitativa backlink-artiklar:

1. **Preflight Research** – Hämtar och analyserar målsidan
2. **LLM Generation** – Genererar SEO-optimerad artikel med Claude/GPT
3. **Quality Assurance** – Automatisk kvalitetskontroll
4. **Storage** – Sparar artiklar och metadata

**Input:** Publisher-domän, target-URL, anchor text
**Output:** Färdig artikel på 900-1200 ord i Markdown-format

---

## ✨ Funktioner

- ✅ **API-first design** – Kör från GUI, CLI eller Hoppscotch
- ✅ **Multi-LLM support** – Fungerar med både Claude och GPT
- ✅ **Automatisk QA** – Kontrollerar ordantal, anchor-text, struktur
- ✅ **Filbaserad lagring** – Ingen databas krävs (v1)
- ✅ **Docker-ready** – Enkel deployment med Docker Compose
- ✅ **Production-ready** – Komplett med logging, error handling och dokumentation

---

## 📦 Snabbstart

### 1. Klona och installera

```bash
# Klona projektet
git clone <your-repo-url>
cd BACOWR_Clean

# Skapa virtuell miljö
python3 -m venv venv
source venv/bin/activate  # På Windows: venv\Scripts\activate

# Installera beroenden
pip install -r requirements.txt
```

### 2. Konfigurera

```bash
# Kopiera miljövariabel-mallen
cp .env.example .env

# Redigera .env och lägg till din API-nyckel
# LLM_API_KEY=din_api_nyckel_här
```

### 3. Starta servern

```bash
# Starta API-servern
python -m bacowr.main
```

API:t är nu tillgängligt på: **http://localhost:8000**

### 4. Testa

```bash
# Health check
curl http://localhost:8000/health

# Generera en artikel
curl -X POST http://localhost:8000/jobs/full-run \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "modernalivet.se",
    "target_url": "https://www.rusta.com/sv-se/hem-och-inredning/belysning",
    "anchor_text": "bästa lamporna för",
    "preflight_mode": "light"
  }'
```

---

## 🐳 Docker

```bash
# Starta med Docker Compose
docker-compose up -d

# Visa loggar
docker-compose logs -f

# Stoppa
docker-compose down
```

---

## 📚 Dokumentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** – Fullständig deployment-guide
- **[docs/frontend_and_api_contract.md](docs/frontend_and_api_contract.md)** – API-dokumentation och Hoppscotch-setup
- **[BACOWR_ARCHITECTURE.md](BACOWR_ARCHITECTURE.md)** – Systemarkitektur
- **[MODULES_AND_TASKS.md](MODULES_AND_TASKS.md)** – Detaljerad modulbeskrivning
- **API Docs (Swagger):** http://localhost:8000/docs

---

## 🏗️ Arkitektur

```
┌─────────────┐
│   Client    │ (GUI / Hoppscotch / CLI)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API Gateway │ FastAPI
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Orchestrator│ Koordinerar pipeline
└──────┬──────┘
       │
       ├─────► Preflight Engine (HTML-hämtning, metadata)
       ├─────► LLM Client (Claude/GPT)
       ├─────► Storage Layer (Filsystem)
       └─────► QA Service (Kvalitetskontroll)
```

---

## 🛠️ Teknisk stack

- **Python 3.11+**
- **FastAPI** – Modern webb-ramverk
- **Pydantic** – Datavalidering
- **httpx** – HTTP-klient
- **BeautifulSoup4** – HTML-parsing
- **Claude/GPT** – LLM-integration

---

## 📋 Systemkrav

- Python 3.11 eller senare
- 512 MB RAM (minimum)
- 1 GB diskutrymme för artikellagring
- Internetanslutning för LLM API-anrop

---

## 🔑 API-nycklar

Du behöver en API-nyckel från någon av dessa providers:

- **Anthropic (Claude):** https://console.anthropic.com/
- **OpenAI (GPT):** https://platform.openai.com/

Lägg till nyckeln i `.env`:
```bash
LLM_API_KEY=din_nyckel
LLM_PROVIDER=anthropic  # eller "openai"
```

---

## 📝 Projektstruktur

```
BACOWR_Clean/
├── bacowr/                 # Huvudpaket
│   ├── api/               # FastAPI routes
│   ├── domain/            # Datamodeller
│   ├── llm/               # LLM-klient
│   ├── preflight/         # Research engine
│   ├── qa/                # Quality assurance
│   ├── services/          # Orchestrator
│   ├── storage/           # Fillagring
│   └── main.py            # Entry point
├── docs/                   # Dokumentation
├── output/                 # Genererade artiklar (skapas automatiskt)
├── requirements.txt        # Python-beroenden
├── pyproject.toml         # Projektkonfiguration
├── Dockerfile             # Docker image
├── docker-compose.yml     # Docker Compose
├── .env.example           # Miljövariabel-mall
└── README.md              # Denna fil
```

---

## 🎯 Use Cases

### Single Article Generation
Perfekt för att snabbt generera enskilda backlink-artiklar.

### Batch Processing (Framtida)
Hantera 100+ artiklar per månad (planerat i v2.0).

### API Integration
Integrera i befintliga CMS eller content-workflows.

---

## 🐛 Felsökning

**Problem:** "LLM_API_KEY environment variable is required"
**Lösning:** Sätt `LLM_API_KEY` i `.env`-filen

**Problem:** API svarar inte
**Lösning:** Kontrollera att servern körs: `curl http://localhost:8000/health`

**Problem:** Artiklar genereras inte
**Lösning:** Verifiera din API-nyckel är giltig och har kredit

Se [DEPLOYMENT.md](DEPLOYMENT.md) för mer felsökning.

---

## 📈 Roadmap

### v1.0 (Nuvarande) ✅
- [x] Single job generation
- [x] Light preflight
- [x] Basic QA
- [x] Filesystem storage
- [x] Docker support

### v2.0 (Planerat)
- [ ] Batch processing
- [ ] Heavy preflight med SERP
- [ ] PostgreSQL storage
- [ ] Dashboard
- [ ] Advanced QA metrics

---

## 🤝 Bidrag

Bidrag är välkomna! Öppna en issue eller pull request.

---

## 📄 Licens

MIT License - se LICENSE-filen för detaljer.

---

## ⭐ Kom igång nu!

```bash
# 1. Installera
pip install -r requirements.txt

# 2. Konfigurera
cp .env.example .env
# Lägg till din LLM_API_KEY i .env

# 3. Kör
python -m bacowr.main

# 4. Testa
curl http://localhost:8000/health
```

**BACOWR är redo att användas!** 🚀
