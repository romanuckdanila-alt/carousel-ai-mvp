from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.db import SessionLocal, get_db, init_db
from app.models import Carousel, Export, Generation, Language, Slide, SourceType
from app.schemas import (
    AssetUploadResponse,
    CarouselCreate,
    CarouselDesignUpdate,
    CarouselDetail,
    CarouselRead,
    ExportCreate,
    ExportRead,
    GenerationCreate,
    GenerationRead,
    SlideRead,
    SlideUpdate,
)
from app.services.export import ExportService
from app.services.llm import LLMService
from app.services.storage import StorageService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="carousel-ai", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage_service = StorageService()
llm_service = LLMService()
export_service = ExportService(storage_service)


def _seed_demo_carousel() -> None:
    db = SessionLocal()
    try:
        if db.query(Carousel.id).first():
            return

        demo_slides = [
            {
                "order": 1,
                "title": "Welcome to your first 14 days",
                "body": "Start with product context: vision, user pain, and success metrics.",
                "footer": "Build context first",
            },
            {
                "order": 2,
                "title": "Map your tool stack",
                "body": "Set up analytics, docs, task board, and communication channels.",
                "footer": "Own your workspace",
            },
            {
                "order": 3,
                "title": "Interview key stakeholders",
                "body": "Talk to founders, design, engineering, support, and sales leads.",
                "footer": "Collect real constraints",
            },
            {
                "order": 4,
                "title": "Define onboarding KPIs",
                "body": "Track activation, retention, and first-value completion by segment.",
                "footer": "Measure what matters",
            },
            {
                "order": 5,
                "title": "Ship one small improvement",
                "body": "Pick a low-risk win to learn release process and team cadence.",
                "footer": "Learn by shipping",
            },
            {
                "order": 6,
                "title": "Align on 30-60-90 plan",
                "body": "Present priorities, tradeoffs, and expected outcomes to leadership.",
                "footer": "Create clear momentum",
            },
        ]

        carousel = Carousel(
            title="AI Startup Onboarding Guide",
            source_type=SourceType.text,
            source_payload={
                "text": "Demo seed carousel for reviewers.",
                "design": {
                    "template": "Classic",
                    "background_color": "#f4f6fb",
                    "dark_overlay": False,
                    "show_header": True,
                    "show_footer": True,
                    "header_text": "AI Startup Onboarding Guide",
                    "footer_text": "Demo carousel",
                    "content_padding": 52,
                    "horizontal_alignment": "left",
                    "vertical_alignment": "top",
                },
            },
            slides_count=6,
            language=Language.EN,
            style_hint="clean and practical",
            status="ready",
        )
        db.add(carousel)
        db.flush()

        for slide in demo_slides:
            db.add(
                Slide(
                    carousel_id=carousel.id,
                    order=slide["order"],
                    title=slide["title"],
                    body=slide["body"],
                    footer=slide["footer"],
                )
            )

        db.add(
            Generation(
                carousel_id=carousel.id,
                status="completed",
                result_json={"provider": "seed", "slides": demo_slides},
            )
        )

        db.commit()
        logger.info("Seeded demo carousel id=%s", carousel.id)
    except Exception:
        logger.exception("Failed to seed demo carousel")
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    _seed_demo_carousel()

    for attempt in range(1, 21):
        try:
            storage_service.ensure_default_buckets()
            return
        except Exception:
            if attempt == 20:
                raise
            time.sleep(1)


def _get_carousel_or_404(db: Session, carousel_id: str) -> Carousel:
    carousel = db.query(Carousel).filter(Carousel.id == carousel_id).first()
    if not carousel:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return carousel


def _run_generation_job(generation_id: str, carousel_id: str) -> None:
    db = SessionLocal()
    try:
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        carousel = db.query(Carousel).filter(Carousel.id == carousel_id).first()
        if not generation or not carousel:
            logger.error(
                "Generation job missing records generation_id=%s carousel_id=%s",
                generation_id,
                carousel_id,
            )
            return

        generation.status = "running"
        db.commit()

        result = llm_service.generate_slides(carousel)

        db.query(Slide).filter(Slide.carousel_id == carousel.id).delete(synchronize_session=False)
        for item in result["slides"]:
            db.add(
                Slide(
                    carousel_id=carousel.id,
                    order=item["order"],
                    title=item["title"],
                    body=item["body"],
                    footer=item["footer"],
                )
            )

        generation.status = "completed"
        generation.result_json = result
        carousel.status = "generated" if result.get("provider") == "openrouter" else "generated_fallback"
        db.commit()

        logger.info(
            "Generation job completed generation_id=%s carousel_id=%s provider=%s",
            generation_id,
            carousel_id,
            result.get("provider"),
        )
    except Exception as exc:
        logger.exception(
            "Generation job failed generation_id=%s carousel_id=%s error=%s",
            generation_id,
            carousel_id,
            exc,
        )
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        carousel = db.query(Carousel).filter(Carousel.id == carousel_id).first()
        if generation:
            generation.status = "failed"
            generation.result_json = {"error": str(exc)}
        if carousel:
            carousel.status = "generation_failed"
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/carousels", response_model=list[CarouselRead])
def list_carousels(db: Session = Depends(get_db)) -> list[Carousel]:
    return db.query(Carousel).order_by(Carousel.created_at.desc()).all()


@app.post("/carousels", response_model=CarouselRead, status_code=201)
def create_carousel(payload: CarouselCreate, db: Session = Depends(get_db)) -> Carousel:
    carousel = Carousel(
        title=payload.title,
        source_type=payload.source_type,
        source_payload=payload.source_payload,
        slides_count=payload.slides_count,
        language=payload.language,
        style_hint=payload.style_hint,
        status="draft",
    )
    db.add(carousel)
    db.commit()
    db.refresh(carousel)
    return carousel


@app.get("/carousels/{carousel_id}", response_model=CarouselDetail)
def get_carousel(carousel_id: str, db: Session = Depends(get_db)) -> Carousel:
    carousel = (
        db.query(Carousel)
        .options(joinedload(Carousel.slides))
        .filter(Carousel.id == carousel_id)
        .first()
    )
    if not carousel:
        raise HTTPException(status_code=404, detail="Carousel not found")

    carousel.slides.sort(key=lambda slide: slide.order)
    return carousel


@app.get("/carousels/{carousel_id}/slides", response_model=list[SlideRead])
def list_slides(carousel_id: str, db: Session = Depends(get_db)) -> list[Slide]:
    _get_carousel_or_404(db, carousel_id)
    return db.query(Slide).filter(Slide.carousel_id == carousel_id).order_by(Slide.order).all()


@app.patch("/carousels/{carousel_id}/design", response_model=CarouselRead)
def update_carousel_design(
    carousel_id: str,
    payload: CarouselDesignUpdate,
    db: Session = Depends(get_db),
) -> Carousel:
    carousel = _get_carousel_or_404(db, carousel_id)
    source_payload = dict(carousel.source_payload or {})
    design = dict(source_payload.get("design", {}))
    design.update(payload.model_dump(exclude_none=True))
    source_payload["design"] = design

    carousel.source_payload = source_payload
    db.commit()
    db.refresh(carousel)
    return carousel


@app.patch("/carousels/{carousel_id}/slides/{slide_id}", response_model=SlideRead)
def update_slide(
    carousel_id: str,
    slide_id: str,
    payload: SlideUpdate,
    db: Session = Depends(get_db),
) -> Slide:
    _get_carousel_or_404(db, carousel_id)
    slide = db.query(Slide).filter(Slide.id == slide_id, Slide.carousel_id == carousel_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(slide, field, value)

    db.commit()
    db.refresh(slide)
    return slide


@app.post("/generations", response_model=GenerationRead, status_code=201)
def create_generation(
    payload: GenerationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Generation:
    carousel = _get_carousel_or_404(db, payload.carousel_id)

    generation = Generation(carousel_id=carousel.id, status="pending")
    db.add(generation)
    carousel.status = "generating"
    db.commit()
    db.refresh(generation)

    background_tasks.add_task(_run_generation_job, generation.id, carousel.id)
    return generation


@app.get("/generations/{generation_id}", response_model=GenerationRead)
def get_generation(generation_id: str, db: Session = Depends(get_db)) -> Generation:
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation


@app.post("/exports", response_model=ExportRead, status_code=201)
def create_export(payload: ExportCreate, db: Session = Depends(get_db)) -> Export:
    carousel = _get_carousel_or_404(db, payload.carousel_id)
    slides = db.query(Slide).filter(Slide.carousel_id == carousel.id).order_by(Slide.order).all()
    if not slides:
        raise HTTPException(status_code=400, detail="No slides found for carousel")

    export = Export(carousel_id=carousel.id, status="running")
    db.add(export)
    db.commit()
    db.refresh(export)

    try:
        zip_url = export_service.render_and_upload_zip(carousel, slides)
        export.status = "completed"
        export.zip_url = zip_url
        carousel.status = "exported"
        db.commit()
        db.refresh(export)
        return export
    except Exception as exc:
        export.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")


@app.get("/exports/{export_id}", response_model=ExportRead)
def get_export(export_id: str, db: Session = Depends(get_db)) -> Export:
    export = db.query(Export).filter(Export.id == export_id).first()
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    return export


@app.post("/assets/upload", response_model=AssetUploadResponse, status_code=201)
async def upload_asset(file: UploadFile = File(...)) -> AssetUploadResponse:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    key = f"assets/{uuid4()}-{file.filename}"
    storage_service.upload_bytes(
        bucket=settings.assets_bucket,
        key=key,
        content=payload,
        content_type=file.content_type or "application/octet-stream",
    )
    url = storage_service.public_presigned_get_url(settings.assets_bucket, key)
    return AssetUploadResponse(key=key, url=url)
