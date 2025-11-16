# BACOWR Deployment Guide

Komplett guide för att bygga, köra och hosta BACOWR-systemet.

## Innehållsförteckning

1. [Snabbstart (Lokal utveckling)](#snabbstart-lokal-utveckling)
2. [Docker Deployment](#docker-deployment)
3. [Produktions-deployment](#produktions-deployment)
4. [Konfiguration](#konfiguration)
5. [Felsökning](#felsökning)

---

## Snabbstart (Lokal utveckling)

### Förutsättningar

- Python 3.11 eller senare
- pip (Python package manager)
- Ett Claude API-key ELLER OpenAI API-key

### Steg 1: Klona och förbered projektet

```bash
# Klona repot (eller använd befintligt)
cd BACOWR_Clean

# Skapa virtuell miljö
python3 -m venv venv

# Aktivera virtuell miljö
# På macOS/Linux:
source venv/bin/activate
# På Windows:
venv\Scripts\activate

# Installera beroenden
pip install -r requirements.txt
```

### Steg 2: Konfigurera miljövariabler

```bash
# Kopiera exempel-konfigurationen
cp .env.example .env

# Redigera .env och lägg till din API-nyckel
# Öppna .env i din favorit-editor och uppdatera:
# LLM_API_KEY=din_riktiga_api_nyckel_här
```

**Viktigt:** Du MÅSTE sätta `LLM_API_KEY` för att systemet ska fungera.

### Steg 3: Starta servern

```bash
# Metod 1: Använd main.py (rekommenderat)
python -m bacowr.main

# Metod 2: Använd uvicorn direkt
uvicorn bacowr.api.server:app --reload --host 0.0.0.0 --port 8000
```

### Steg 4: Verifiera att det fungerar

Öppna din webbläsare och gå till:

- **API Docs (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

Du bör se ett JSON-svar:
```json
{
  "status": "healthy",
  "service": "BACOWR API",
  "version": "1.0.0"
}
```

### Steg 5: Testa artikel-generering

#### Med Curl:

```bash
curl -X POST http://localhost:8000/jobs/full-run \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "modernalivet.se",
    "target_url": "https://www.rusta.com/sv-se/hem-och-inredning/belysning",
    "anchor_text": "bästa lamporna för",
    "preflight_mode": "light"
  }'
```

#### Med Hoppscotch:

Se [docs/frontend_and_api_contract.md](docs/frontend_and_api_contract.md) för fullständig Hoppscotch-konfiguration.

---

## Docker Deployment

### Förutsättningar

- Docker
- Docker Compose (valfritt men rekommenderat)

### Metod 1: Docker Compose (Enklast)

#### Steg 1: Konfigurera miljövariabler

```bash
# Skapa .env fil
cp .env.example .env

# Redigera .env och lägg till din API-nyckel
nano .env  # eller din favorit-editor
```

#### Steg 2: Starta med Docker Compose

```bash
# Bygg och starta i bakgrunden
docker-compose up -d

# Visa loggar
docker-compose logs -f

# Stoppa
docker-compose down
```

API:t kommer vara tillgängligt på: http://localhost:8000

#### Steg 3: Verifiera deployment

```bash
# Kolla hälsostatus
curl http://localhost:8000/health

# Kolla container-status
docker-compose ps

# Inspektera loggar
docker-compose logs bacowr
```

### Metod 2: Manuell Docker build

```bash
# Bygg image
docker build -t bacowr:latest .

# Kör container
docker run -d \
  --name bacowr \
  -p 8000:8000 \
  -e LLM_API_KEY="din_api_nyckel" \
  -e LLM_PROVIDER="anthropic" \
  -v $(pwd)/output:/app/output \
  bacowr:latest

# Visa loggar
docker logs -f bacowr

# Stoppa och ta bort
docker stop bacowr
docker rm bacowr
```

---

## Produktions-deployment

### Rekommenderade inställningar för produktion

#### 1. Miljövariabler

```bash
# .env för produktion
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...  # Din riktiga nyckel
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_MAX_TOKENS=4000
LLM_TEMPERATURE=0.7

STORAGE_PATH=/app/output

API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false  # VIKTIGT: false i produktion

LOG_LEVEL=INFO

PREFLIGHT_TIMEOUT=30
PREFLIGHT_MAX_PARAGRAPHS=3
```

#### 2. Med Docker Compose + Nginx (Rekommenderat)

Skapa `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  bacowr:
    image: bacowr:latest
    restart: always
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_API_KEY=${LLM_API_KEY}
      - LOG_LEVEL=INFO
      - API_RELOAD=false
    volumes:
      - ./output:/app/output
    networks:
      - bacowr-net

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - bacowr
    networks:
      - bacowr-net

networks:
  bacowr-net:
    driver: bridge
```

Skapa `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream bacowr {
        server bacowr:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://bacowr;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeout för långvariga requests
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }
    }
}
```

Starta produktion:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### 3. Systemd Service (Linux server utan Docker)

Skapa `/etc/systemd/system/bacowr.service`:

```ini
[Unit]
Description=BACOWR API Service
After=network.target

[Service]
Type=simple
User=bacowr
WorkingDirectory=/opt/bacowr
Environment="PATH=/opt/bacowr/venv/bin"
EnvironmentFile=/opt/bacowr/.env
ExecStart=/opt/bacowr/venv/bin/python -m bacowr.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Aktivera och starta:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bacowr
sudo systemctl start bacowr
sudo systemctl status bacowr
```

---

## Konfiguration

### Miljövariabler (fullständig referens)

| Variabel | Beskrivning | Standard | Obligatorisk |
|----------|-------------|----------|--------------|
| `LLM_PROVIDER` | LLM-provider (`anthropic` eller `openai`) | `anthropic` | Nej |
| `LLM_API_KEY` | API-nyckel för LLM-provider | - | **JA** |
| `LLM_MODEL` | Specifik modell att använda | Provider-default | Nej |
| `LLM_MAX_TOKENS` | Max tokens per artikel | `4000` | Nej |
| `LLM_TEMPERATURE` | Temperature för generation (0-1) | `0.7` | Nej |
| `STORAGE_PATH` | Sökväg för fillagring | `./output` | Nej |
| `API_HOST` | API server host | `0.0.0.0` | Nej |
| `API_PORT` | API server port | `8000` | Nej |
| `API_RELOAD` | Auto-reload vid utveckling | `false` | Nej |
| `LOG_LEVEL` | Loggningsnivå | `INFO` | Nej |
| `PREFLIGHT_TIMEOUT` | HTTP timeout (sekunder) | `30` | Nej |
| `PREFLIGHT_MAX_PARAGRAPHS` | Max paragraf att extrahera | `3` | Nej |

### Hämta API-nycklar

#### Anthropic (Claude)
1. Gå till https://console.anthropic.com/
2. Skapa ett konto
3. Navigera till "API Keys"
4. Skapa ny nyckel
5. Kopiera och sätt som `LLM_API_KEY`

#### OpenAI (GPT)
1. Gå till https://platform.openai.com/
2. Logga in eller skapa konto
3. Gå till "API keys"
4. Skapa ny nyckel
5. Kopiera och sätt som `LLM_API_KEY`
6. Sätt `LLM_PROVIDER=openai`

---

## Felsökning

### Problem: "LLM_API_KEY environment variable is required"

**Lösning:**
```bash
# Kontrollera att .env finns
cat .env

# Verifiera att LLM_API_KEY är satt
echo $LLM_API_KEY

# Om tom, lägg till i .env:
echo "LLM_API_KEY=din_nyckel" >> .env
```

### Problem: "Connection refused" när du anropar API:t

**Lösning:**
```bash
# Kontrollera att servern körs
curl http://localhost:8000/health

# Kolla portar
netstat -tuln | grep 8000

# Om inget svar, starta om servern
docker-compose restart  # för Docker
# eller
systemctl restart bacowr  # för systemd
```

### Problem: "Article generation failed: HTTP 401"

**Orsak:** Ogiltig API-nyckel

**Lösning:**
```bash
# Verifiera att din API-nyckel är korrekt
# För Anthropic:
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $LLM_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'

# Om fel: uppdatera LLM_API_KEY i .env
```

### Problem: Artiklar genereras inte (timeout)

**Lösning:**
```bash
# Öka timeout-värden
# I .env:
PREFLIGHT_TIMEOUT=60  # Öka från 30
LLM_MAX_TOKENS=3000   # Minska för snabbare svar

# I nginx.conf (om du använder nginx):
proxy_read_timeout 600s;
```

### Problem: Diskutrymme fylls upp

**Orsak:** Artiklar sparas lokalt i `output/`

**Lösning:**
```bash
# Kontrollera diskutrymme
du -sh output/

# Rensa gamla artiklar (var försiktig!)
find output/articles -type f -mtime +30 -delete  # Raderar > 30 dagar gamla

# Eller flytta till annan lagring
mv output/ /backup/bacowr-output-$(date +%Y%m%d)/
mkdir output
```

### Loggar och diagnostik

```bash
# Docker
docker-compose logs -f bacowr

# Systemd
journalctl -u bacowr -f

# Direkt körning
# Loggarna visas direkt i terminalen

# Kontrollera systemstatus
curl http://localhost:8000/config
```

---

## Backup och underhåll

### Backup av genererade artiklar

```bash
# Skapa backup
tar -czf bacowr-backup-$(date +%Y%m%d).tar.gz output/

# Återställ backup
tar -xzf bacowr-backup-20240115.tar.gz
```

### Uppdatera systemet

```bash
# Med Git
git pull origin main

# Installera nya beroenden
pip install -r requirements.txt

# Starta om
docker-compose restart  # Docker
# eller
systemctl restart bacowr  # systemd
```

---

## Support

För frågor och support, se:
- **README.md** - Projektöversikt
- **docs/frontend_and_api_contract.md** - API-dokumentation
- **API Docs:** http://localhost:8000/docs

---

**BACOWR är nu redo för produktion!** 🚀
