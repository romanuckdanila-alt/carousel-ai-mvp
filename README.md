# carousel-ai

Production-style MVP for generating Instagram carousel posts from source text/video, editing slide content and design, and exporting final slides as a ZIP archive of PNG images.

## What the product does
- Creates carousel drafts from user source input.
- Runs async AI slide generation.
- Shows preview with thumbnail navigation.
- Provides editor with template/background/text/layout controls.
- Exports slides as `1080x1350` PNGs zipped in MinIO with download URL.

## Architecture overview
`carousel-ai` is a single-repo full-stack app with 4 runtime services:

- `frontend` (Nuxt 3): product UI and user flow.
- `backend` (FastAPI): REST API, orchestration, async jobs.
- `postgres`: persistent data store.
- `minio`: S3-compatible object storage for assets and exports.

Generation and export are orchestrated by backend services:
- `LLMService` for OpenRouter calls and JSON normalization.
- `ExportService` for Playwright rendering + ZIP upload.

## Tech stack
- FastAPI
- Nuxt 3 (Vue 3)
- PostgreSQL
- MinIO
- Docker Compose
- SQLAlchemy
- Playwright
- OpenRouter (via OpenAI Python SDK)

## Project structure
```text
carousel-ai/
  backend/
    app/
      config.py
      db.py
      models.py
      schemas.py
      services/
        llm.py
        export.py
        storage.py
    main.py
  frontend/
    app.vue
    assets/css/main.css
    composables/useApi.ts
    pages/
      index.vue
      create.vue
      preview/[id].vue
      editor/[id].vue
  docker-compose.yml
  README.md
  README_RU.md
```

## Quick start
```bash
docker compose up --build
```

Open:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Demo flow
1. Create carousel
2. Generate slides
3. Preview
4. Edit
5. Export ZIP

## API endpoints overview
- `GET /health`
- `/carousels`
  - `GET /carousels`
  - `POST /carousels`
  - `GET /carousels/{id}`
  - `DELETE /carousels/{id}`
- `/slides`
  - `GET /carousels/{id}/slides`
  - `PATCH /carousels/{id}/slides/{slide_id}`
- `/design`
  - `PATCH /carousels/{id}/design`
- `/generations`
  - `POST /generations`
  - `GET /generations/{id}`
- `/assets`
  - `POST /assets/upload`
- `/exports`
  - `POST /exports`
  - `GET /exports/{id}`

## API examples (curl)
Health check:
```bash
curl http://localhost:8000/health
```

Create carousel:
```bash
curl -X POST http://localhost:8000/carousels \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI onboarding checklist",
    "source_type": "text",
    "source_payload": {"text": "A practical onboarding framework for AI teams"},
    "slides_count": 6,
    "language": "EN",
    "style_hint": "clear tactical"
  }'
```

Start async generation:
```bash
curl -X POST http://localhost:8000/generations \
  -H "Content-Type: application/json" \
  -d '{"carousel_id":"<CAROUSEL_ID>"}'
```

Poll generation status:
```bash
curl http://localhost:8000/generations/<GENERATION_ID>
```

Patch design settings:
```bash
curl -X PATCH http://localhost:8000/carousels/<CAROUSEL_ID>/design \
  -H "Content-Type: application/json" \
  -d '{
    "template":"Bold",
    "background_color":"#EAF2FF",
    "dark_overlay":true,
    "dark_overlay_opacity":0.35,
    "content_padding":64,
    "horizontal_alignment":"left",
    "vertical_alignment":"center"
  }'
```

Export ZIP:
```bash
curl -X POST http://localhost:8000/exports \
  -H "Content-Type: application/json" \
  -d '{"carousel_id":"<CAROUSEL_ID>"}'
```

## AI generation pipeline
1. User creates a carousel (`POST /carousels`).
2. UI starts generation (`POST /generations`).
3. FastAPI schedules background task (`BackgroundTasks`) and returns immediately.
4. LLM service calls OpenRouter chat completions endpoint.
5. Backend validates JSON payload structure and slide count.
6. If response JSON is malformed, backend attempts lightweight JSON repair.
7. Only if request/validation fails, backend falls back to local placeholder slides.
8. Generated slides are persisted into Postgres and exposed via `/carousels/{id}/slides`.

Provider details:
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Model (default): `openai/gpt-4o-mini`

## JSON validation and repair fallback
`backend/app/services/llm.py` includes:
- strict extraction of `choices[0].message.content`
- JSON parsing with schema-like checks (`slides` list, required fields)
- repair pass for common malformed patterns (trailing commas / missing closing braces)
- fallback to local slides only when OpenRouter request or JSON validation cannot be recovered

## Async generation architecture
Generation is non-blocking for API clients:
- `/generations` returns job metadata immediately (`pending`/`running`/`completed`/`failed`).
- Worker logic runs in background task and updates DB status.
- Frontend polls `/generations/{id}` and transitions UI states (`queued`, `running`, `done`, `failed`).

## Export pipeline
1. Client triggers export (`POST /exports`).
2. Backend loads carousel slides.
3. Playwright renders each slide to `1080x1350` PNG.
4. PNGs are zipped with names:
   - `slide_01.png`
   - `slide_02.png`
   - ...
5. ZIP is uploaded to MinIO (`carousel-exports` bucket).
6. API returns presigned download URL.
7. Frontend shows progress and auto-opens ZIP when ready.

## Demo seed data
On backend startup, if DB is empty:
- creates one demo carousel titled `AI Startup Onboarding Guide`
- creates 6 readable demo slides
- marks status as `ready`

## Environment variables
```bash
OPENROUTER_API_KEY=YOUR_KEY
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini

DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/carousel_ai

MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
```

## Tools used
- Cursor
- ChatGPT
- Codex

## Estimated development time
- MVP implementation: ~9 hours
- Product polish + UX alignment + debugging: ~6 hours
- Total: ~15 hours

## Token usage estimate
Per one generation run (6–10 slides):
- Prompt/input: ~900–1,700 tokens
- Completion/output: ~350–1,200 tokens
- Total: ~1,250–2,900 tokens

Actual token usage depends on source text size, slide count, and model behavior.

## Limitations (MVP scope)
- No authentication or user workspaces yet.
- Async jobs use FastAPI `BackgroundTasks` (no distributed queue/worker).
- Design settings are stored in `source_payload.design` JSON.
- Export is triggered synchronously from API call and then polled by UI.
- Storage cleanup is best-effort for uploaded assets/exports on carousel deletion.

## Design Notes
The provided Figma file was used as a reference for layout structure, screen hierarchy and component grouping (My Carousels → Create → Preview → Editor).

Since the task goal was to deliver a working end-to-end MVP, the implementation focuses on:

- functional UX flow
- clear visual hierarchy
- responsive layout
- simple and consistent design system

Instead of reproducing the Figma layout pixel-perfectly, the UI was implemented using a lightweight component structure with Tailwind utilities.

This allowed faster iteration and easier extension of the editor features (template settings, background controls, layout adjustments).

The overall interaction model and screen structure follow the Figma reference, while the visual styling was simplified to keep the MVP implementation focused on functionality and maintainability.

If required, the UI can be aligned closer to the original Figma layout with pixel-perfect adjustments.
