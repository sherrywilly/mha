"""
SafeCare eMAR & Lead Engine — FastAPI application entry point.

Run with:
    uvicorn main:app --reload
"""
from fastapi import FastAPI

from app.routers import auth, drugs, family_portal, leads, med_events, residents

app = FastAPI(
    title="SafeCare eMAR & Lead Engine",
    description=(
        "Clinical-grade UK care home medication administration record (eMAR) "
        "and lead management platform. Multi-tenant, CQC-compliant, NHS dm+d integrated."
    ),
    version="0.1.0",
    contact={"name": "SafeCare Support", "email": "support@safecare.example.com"},
    license_info={"name": "Proprietary"},
)

app.include_router(auth.router)
app.include_router(residents.router)
app.include_router(med_events.router)
app.include_router(leads.router)
app.include_router(family_portal.router)
app.include_router(drugs.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "SafeCare eMAR & Lead Engine"}
