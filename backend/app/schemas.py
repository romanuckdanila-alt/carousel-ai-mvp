from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import Language, SourceType


class CarouselCreate(BaseModel):
    title: str
    source_type: SourceType
    source_payload: dict[str, Any]
    slides_count: int = Field(ge=6, le=10)
    language: Language
    style_hint: str | None = None


class CarouselRead(BaseModel):
    id: str
    title: str
    source_type: SourceType
    source_payload: dict[str, Any]
    slides_count: int
    language: Language
    style_hint: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SlideRead(BaseModel):
    id: str
    carousel_id: str
    order: int
    title: str
    body: str
    footer: str

    model_config = ConfigDict(from_attributes=True)


class SlideUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    footer: str | None = None


class CarouselDesignUpdate(BaseModel):
    template: str | None = None
    apply_to_all_slides: bool | None = None
    background_color: str | None = None
    background_image_url: str | None = None
    dark_overlay: bool | None = None
    show_header: bool | None = None
    show_footer: bool | None = None
    header_text: str | None = None
    footer_text: str | None = None
    content_padding: int | None = Field(default=None, ge=0, le=240)
    horizontal_alignment: str | None = None
    vertical_alignment: str | None = None
    additional: dict[str, Any] | None = None


class CarouselDetail(CarouselRead):
    slides: list[SlideRead] = []


class GenerationCreate(BaseModel):
    carousel_id: str


class GenerationRead(BaseModel):
    id: str
    carousel_id: str
    status: str
    result_json: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportCreate(BaseModel):
    carousel_id: str


class ExportRead(BaseModel):
    id: str
    carousel_id: str
    status: str
    zip_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AssetUploadResponse(BaseModel):
    key: str
    url: str
