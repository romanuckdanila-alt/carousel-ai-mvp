# carousel-ai MVP

## Project description
`carousel-ai` is an MVP that generates editable Instagram carousels from text (and video/link sources), lets users tune design settings, and exports slides as a ZIP of PNG images.

## Architecture
- `frontend/`: Nuxt 3 + Tailwind app with pages for My Carousels, Create, Preview, and Editor.
- `backend/`: FastAPI + SQLAlchemy API for carousels, slides, generation jobs, design updates, exports, and asset upload.
- `postgres`: primary relational database for carousel data.
- `minio`: S3-compatible storage for uploaded assets and generated ZIP exports.
- `OpenRouter` (via OpenAI SDK): LLM generation provider.
- `Playwright`: server-side rendering of 1080x1350 slide PNG images before zipping.

## Stack
- FastAPI
- Nuxt 3
- PostgreSQL
- MinIO
- Docker Compose

## Setup
```bash
docker compose up --build
```

Open:
- `http://localhost:3000` (frontend)
- `http://localhost:8000` (backend)

Environment variables:
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

## Demo flow
1. Create carousel
2. Generate slides
3. Preview
4. Edit
5. Export ZIP

## API endpoints
- `GET /health`
- `GET /carousels`
- `POST /carousels`
- `GET /carousels/{id}`
- `GET /carousels/{id}/slides`
- `PATCH /carousels/{id}/slides/{slide_id}`
- `PATCH /carousels/{id}/design`
- `POST /generations`
- `GET /generations/{id}`
- `POST /exports`
- `GET /exports/{id}`
- `POST /assets/upload`

## API examples
Health:
```bash
curl http://localhost:8000/health
```

Create carousel:
```bash
curl -X POST http://localhost:8000/carousels \
  -H "Content-Type: application/json" \
  -d '{
    "title":"AI onboarding checklist",
    "source_type":"text",
    "source_payload":{"text":"Step-by-step onboarding framework"},
    "slides_count":7,
    "language":"EN",
    "style_hint":"bold educational"
  }'
```

Start generation:
```bash
curl -X POST http://localhost:8000/generations \
  -H "Content-Type: application/json" \
  -d '{"carousel_id":"<CAROUSEL_ID>"}'
```

Poll generation:
```bash
curl http://localhost:8000/generations/<GENERATION_ID>
```

Patch design:
```bash
curl -X PATCH http://localhost:8000/carousels/<CAROUSEL_ID>/design \
  -H "Content-Type: application/json" \
  -d '{"template":"Classic","background_color":"#ffffff","show_header":true}'
```

Patch slide:
```bash
curl -X PATCH http://localhost:8000/carousels/<CAROUSEL_ID>/slides/<SLIDE_ID> \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated title","body":"Updated body","footer":"Updated footer"}'
```

Export:
```bash
curl -X POST http://localhost:8000/exports \
  -H "Content-Type: application/json" \
  -d '{"carousel_id":"<CAROUSEL_ID>"}'
```

Upload image:
```bash
curl -X POST http://localhost:8000/assets/upload \
  -F "file=@/path/to/file.png"
```

## Tools used
- Cursor
- ChatGPT
- Codex

## LLM provider
- OpenRouter endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Primary model: `openai/gpt-4o-mini`

## Estimated token usage
- Input prompt: ~900-1,700 tokens per generation
- Output for 6-10 slides: ~350-1,200 tokens
- Total per generation: ~1,250-2,900 tokens

## Estimated development time
- MVP baseline: ~9 hours
- UI/flow polish and design alignment: ~5 hours
