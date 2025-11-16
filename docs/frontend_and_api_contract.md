# BACOWR Frontend & API Contract Specification

Detta dokument definierar API-kontraktet för BACOWR och visar hur externa klienter (GUI, Hoppscotch, CLI) ska interagera med systemet.

## Innehållsförteckning

1. [API Endpoints](#api-endpoints)
2. [Request/Response Format](#requestresponse-format)
3. [Hoppscotch Setup](#hoppscotch-setup)
4. [Frontend GUI Specifikation](#frontend-gui-specifikation)
5. [Exempel och Use Cases](#exempel-och-use-cases)

---

## API Endpoints

### Base URL

```
http://localhost:8000
```

För produktion, ersätt med din faktiska domän.

### Tillgängliga Endpoints

#### 1. Health Check

**GET** `/health`

Kontrollera att API:t är igång.

**Response:**
```json
{
  "status": "healthy",
  "service": "BACOWR API",
  "version": "1.0.0"
}
```

---

#### 2. Generate Single Article (Main Endpoint)

**POST** `/jobs/full-run`

Generera en komplett SEO-artikel med backlink.

**Request Body:**
```json
{
  "publisher_domain": "modernalivet.se",
  "target_url": "https://www.rusta.com/sv-se/hem-och-inredning/belysning",
  "anchor_text": "bästa lamporna för",
  "preflight_mode": "light"
}
```

**Response (201 Created):**
```json
{
  "id": "a7f3e2c1-4b8d-4e3f-9a1c-8d7e6f5a4b3c",
  "job_id": "a7f3e2c1-4b8d-4e3f-9a1c-8d7e6f5a4b3c",
  "batch_id": null,
  "article_markdown": "# Så väljer du rätt belysning för ditt hem\n\nAtt skapa...",
  "job_input": {
    "publisher_domain": "modernalivet.se",
    "target_url": "https://www.rusta.com/sv-se/hem-och-inredning/belysning",
    "anchor_text": "bästa lamporna för",
    "preflight_mode": "light"
  },
  "qa_status": "approved",
  "qa_flags": [],
  "word_count": 1053,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:00Z"
}
```

---

## Hoppscotch Setup

### Endpoint: Generate Article

```
Method: POST
URL: http://localhost:8000/jobs/full-run
Headers:
  Content-Type: application/json

Body (JSON):
{
  "publisher_domain": "modernalivet.se",
  "target_url": "https://www.rusta.com/sv-se/hem-och-inredning/belysning",
  "anchor_text": "bästa lamporna för",
  "preflight_mode": "light"
}
```

---

## Frontend GUI Specifikation

En minimal intern GUI för skribenterna.

### Minimal HTML Implementation

Se fullständig implementation i projektets dokumentation.

**Tre huvudfält:**
1. Publisher Domain (text input)
2. Target URL (URL input)
3. Anchor Text (text input)

**Resultatvy:**
- Visa word count
- Visa QA status
- Visa artikel i preview
- Knappar: Copy Markdown, Download .md, New Article

---

För fullständig dokumentation och exempel, se projektets GitHub-repository.
