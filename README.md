# BACOWR – Backlink Content Writer (Skeleton)

Detta repo är startpunkten för BACOWR – ett API-first backend-system som automatiserar skapandet av SEO-optimerade backlink-artiklar.

## Vad som ingår

- `BACOWR_ARCHITECTURE.md` – övergripande systembeskrivning
- `MODULES_AND_TASKS.md` – detaljerad tasklista (T1–T8)
- Grundläggande Python-paketsstruktur i `bacowr/`
- Tomma `docs/` och `tools/`-mappar
- En enkel task-runner i `tools/run_task.py` (se nedan)

## Snabbstart

1. Skapa och aktivera ett virtualenv.
2. Installera basberoenden:

   ```bash
   pip install fastapi uvicorn pydantic httpx
   ```

3. Öppna `MODULES_AND_TASKS.md` och börja med T1.

## Task Runner

`tools/run_task.py` kan hjälpa dig att generera en prompt till en LLM för en specifik task.

Exempel:

```bash
python tools/run_task.py T3
```

Detta skriver ut:

- systemkontext
- hela `MODULES_AND_TASKS.md`
- markering att aktuell task är T3

Du kan kopiera outputen och klistra in i Claude/GPT som startprompt.
