from fastapi import APIRouter
from app.api.v1 import auth, organisations, residents, medications, emar, controlled_drugs, stock, prescriptions, errors, events

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organisations.router, tags=["organisations"])
api_router.include_router(residents.router, tags=["residents"])
api_router.include_router(medications.router, tags=["medications"])
api_router.include_router(emar.router, tags=["emar"])
api_router.include_router(controlled_drugs.router, tags=["controlled_drugs"])
api_router.include_router(stock.router, tags=["stock"])
api_router.include_router(prescriptions.router, tags=["prescriptions"])
api_router.include_router(errors.router, tags=["errors"])
api_router.include_router(events.router, tags=["events"])
