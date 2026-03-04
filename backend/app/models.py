from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SourceType(str, Enum):
    text = "text"
    video = "video"


class Language(str, Enum):
    RU = "RU"
    EN = "EN"
    FR = "FR"


class Carousel(Base):
    __tablename__ = "carousels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), nullable=False)
    source_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    slides_count: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[Language] = mapped_column(SAEnum(Language), nullable=False)
    style_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    slides: Mapped[list[Slide]] = relationship(
        "Slide",
        back_populates="carousel",
        cascade="all, delete-orphan",
        order_by="Slide.order",
    )
    generations: Mapped[list[Generation]] = relationship(
        "Generation",
        back_populates="carousel",
        cascade="all, delete-orphan",
    )
    exports: Mapped[list[Export]] = relationship(
        "Export",
        back_populates="carousel",
        cascade="all, delete-orphan",
    )


class Slide(Base):
    __tablename__ = "slides"
    __table_args__ = (UniqueConstraint("carousel_id", "order", name="uq_slides_carousel_order"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    carousel_id: Mapped[str] = mapped_column(String(36), ForeignKey("carousels.id", ondelete="CASCADE"), nullable=False)
    order: Mapped[int] = mapped_column("order", Integer, nullable=False, quote=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    footer: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    carousel: Mapped[Carousel] = relationship("Carousel", back_populates="slides")


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    carousel_id: Mapped[str] = mapped_column(String(36), ForeignKey("carousels.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    carousel: Mapped[Carousel] = relationship("Carousel", back_populates="generations")


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    carousel_id: Mapped[str] = mapped_column(String(36), ForeignKey("carousels.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    zip_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    carousel: Mapped[Carousel] = relationship("Carousel", back_populates="exports")
