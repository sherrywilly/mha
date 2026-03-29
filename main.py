from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.auth.router import router as auth_router
from app.routers.orgs import router as orgs_router
from app.routers.residents import router as residents_router
from app.routers.medications import router as medications_router
from app.routers.administration import router as administration_router
from app.routers.topical import router as topical_router
from app.routers.controlled import router as controlled_router
from app.routers.stock import router as stock_router
from app.routers.prescriptions import router as prescriptions_router
from app.routers.errors import router as errors_router
from app.routers.exports import router as exports_router

# Import all models so SQLAlchemy registers them before create_all
import app.models.org  # noqa: F401
import app.models.resident  # noqa: F401
import app.models.medication  # noqa: F401
import app.models.topical  # noqa: F401
import app.models.controlled  # noqa: F401
import app.models.stock  # noqa: F401
import app.models.prescription  # noqa: F401
import app.models.error  # noqa: F401


TOPICAL_SITES = [
    ("SCALP", "Scalp", "HEAD"),
    ("FOREHEAD", "Forehead", "HEAD"),
    ("LEFT_EAR", "Left Ear", "HEAD"),
    ("RIGHT_EAR", "Right Ear", "HEAD"),
    ("NOSE", "Nose", "HEAD"),
    ("NECK_FRONT", "Front of Neck", "NECK"),
    ("NECK_BACK", "Back of Neck", "NECK"),
    ("CHEST_UPPER", "Upper Chest", "CHEST"),
    ("CHEST_LOWER", "Lower Chest", "CHEST"),
    ("ABDOMEN_UPPER", "Upper Abdomen", "ABDOMEN"),
    ("ABDOMEN_LOWER", "Lower Abdomen", "ABDOMEN"),
    ("BACK_UPPER", "Upper Back", "BACK"),
    ("BACK_LOWER", "Lower Back", "BACK"),
    ("LEFT_ARM_UPPER", "Left Upper Arm", "LEFT_ARM"),
    ("LEFT_ARM_LOWER", "Left Forearm", "LEFT_ARM"),
    ("LEFT_HAND", "Left Hand", "LEFT_ARM"),
    ("RIGHT_ARM_UPPER", "Right Upper Arm", "RIGHT_ARM"),
    ("RIGHT_ARM_LOWER", "Right Forearm", "RIGHT_ARM"),
    ("RIGHT_HAND", "Right Hand", "RIGHT_ARM"),
    ("LEFT_THIGH", "Left Thigh", "LEFT_LEG"),
    ("LEFT_KNEE", "Left Knee", "LEFT_LEG"),
    ("LEFT_LOWER_LEG", "Left Lower Leg", "LEFT_LEG"),
    ("LEFT_FOOT", "Left Foot", "LEFT_LEG"),
    ("RIGHT_THIGH", "Right Thigh", "RIGHT_LEG"),
    ("RIGHT_KNEE", "Right Knee", "RIGHT_LEG"),
    ("RIGHT_LOWER_LEG", "Right Lower Leg", "RIGHT_LEG"),
    ("RIGHT_FOOT", "Right Foot", "RIGHT_LEG"),
    ("PERINEAL", "Perineal Area", "PERINEAL"),
    ("OTHER", "Other", "OTHER"),
]


async def _seed_topical_sites(db):
    from sqlalchemy import select
    from app.models.topical import TopicalSite
    for code, label, region in TOPICAL_SITES:
        result = await db.execute(select(TopicalSite).where(TopicalSite.code == code))
        if not result.scalar_one_or_none():
            db.add(TopicalSite(code=code, label=label, body_region=region))
    await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await _seed_topical_sites(db)
    yield


app = FastAPI(
    title="MHA eMAR API",
    description="Electronic Medication Administration Record system for nursing homes",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Authentication"},
        {"name": "organisations", "description": "Organisation hierarchy management"},
        {"name": "residents", "description": "Resident management"},
        {"name": "medications", "description": "Medication orders and dose scheduling"},
        {"name": "administration", "description": "Dose administration records"},
        {"name": "topical", "description": "Topical medication with body map"},
        {"name": "controlled_drugs", "description": "Controlled drug register"},
        {"name": "stock", "description": "Stock management"},
        {"name": "prescriptions", "description": "Prescription requests to GPs"},
        {"name": "errors", "description": "Medication error reporting"},
        {"name": "exports", "description": "MAR and audit exports"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(orgs_router)
app.include_router(residents_router)
app.include_router(medications_router)
app.include_router(administration_router)
app.include_router(topical_router)
app.include_router(controlled_router)
app.include_router(stock_router)
app.include_router(prescriptions_router)
app.include_router(errors_router)
app.include_router(exports_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
