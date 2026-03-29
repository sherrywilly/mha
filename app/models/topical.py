from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BodyRegion:
    HEAD = "HEAD"
    NECK = "NECK"
    CHEST = "CHEST"
    ABDOMEN = "ABDOMEN"
    BACK = "BACK"
    LEFT_ARM = "LEFT_ARM"
    RIGHT_ARM = "RIGHT_ARM"
    LEFT_LEG = "LEFT_LEG"
    RIGHT_LEG = "RIGHT_LEG"
    PERINEAL = "PERINEAL"
    OTHER = "OTHER"


class ModeOfAdministration:
    APPLY = "APPLY"
    MASSAGE = "MASSAGE"
    DRESSING = "DRESSING"
    SPRAY = "SPRAY"
    DROPS = "DROPS"
    CREAM = "CREAM"
    OINTMENT = "OINTMENT"
    GEL = "GEL"
    PATCH_APPLY = "PATCH_APPLY"
    PATCH_REMOVE = "PATCH_REMOVE"
    OTHER = "OTHER"


class TopicalSite(Base):
    __tablename__ = "topical_sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    body_region: Mapped[str] = mapped_column(String(20), nullable=False)

    topical_records: Mapped[list[TopicalAdministrationRecord]] = relationship(
        "TopicalAdministrationRecord", back_populates="body_site", lazy="noload"
    )


class TopicalAdministrationRecord(Base):
    __tablename__ = "topical_administration_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    administration_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("administration_records.id"), nullable=False
    )
    body_site_id: Mapped[str] = mapped_column(String(36), ForeignKey("topical_sites.id"), nullable=False)
    body_site_code: Mapped[str] = mapped_column(String(50), nullable=False)
    area_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode_of_administration: Mapped[str] = mapped_column(String(20), nullable=False, default=ModeOfAdministration.APPLY)
    condition_before: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_after: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    administered_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    administered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    body_site: Mapped[TopicalSite] = relationship("TopicalSite", back_populates="topical_records", lazy="noload")
