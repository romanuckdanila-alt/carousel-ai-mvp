# carousel-ai MVP

## Architecture
- `frontend/`: Nuxt 3 (Vue 3) + Tailwind UI for carousel list, creation, and slide editor.
- `backend/`: FastAPI app with SQLAlchemy models and REST endpoints.
- `postgres`: stores carousels, slides, generations, and exports.
- `minio`: S3-compatible storage for uploaded assets and exported ZIP files.
- `OpenRouter` via OpenAI Python SDK: primary LLM provider for generation.
- `Playwright`: renders 1080x1350 slide PNG files, zips them, uploads to MinIO.

## Run
```bash
docker compose up --build
```

Environment variables (`.env`):
```bash
OPENROUTER_API_KEY=YOUR_KEY
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Service URLs:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`

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

Generate slides:
```bash
curl -X POST http://localhost:8000/generations \
  -H "Content-Type: application/json" \
  -d '{"carousel_id":"<CAROUSEL_ID>"}'
```
`/generations` runs asynchronously (background task). Poll generation status:
```bash
curl http://localhost:8000/generations/<GENERATION_ID>
```

Update design settings:
```bash
curl -X PATCH http://localhost:8000/carousels/<CAROUSEL_ID>/design \
  -H "Content-Type: application/json" \
  -d '{"template":"Classic","background_color":"#ffffff","show_header":true}'
```

Update slide:
```bash
curl -X PATCH http://localhost:8000/carousels/<CAROUSEL_ID>/slides/<SLIDE_ID> \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated title","body":"Updated body","footer":"Updated footer"}'
```

Export ZIP:
```bash
curl -X POST http://localhost:8000/exports \
  -H "Content-Type: application/json" \
  -d '{"carousel_id":"<CAROUSEL_ID>"}'
```

Upload asset:
```bash
curl -X POST http://localhost:8000/assets/upload \
  -F "file=@/path/to/file.png"
```

## Tools used
- Codex
- ChatGPT
- FastAPI
- Nuxt 3
- PostgreSQL
- MinIO
- Playwright
- OpenRouter

## LLM provider
- OpenRouter (`https://openrouter.ai/api/v1/chat/completions`)
- Default model: `openai/gpt-4o-mini`

## Estimated token usage
- Typical generation request: ~1,000-1,800 input tokens.
- Typical generation response for 6-10 slides: ~350-1,200 output tokens.
- Per carousel generation estimate: ~1,400-3,000 total tokens.

## Time spent
- Initial MVP: ~9 hours.
- UI/flow alignment iteration: ~5 hours.
