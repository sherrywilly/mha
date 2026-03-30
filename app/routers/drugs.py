"""Drug / dm+d router — search and manual sync."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Drug, UserRole
from app.routers.deps import require_roles
from app.schemas.schemas import DrugOut
from app.services.dmd_sync import fetch_dmd_drug

router = APIRouter(prefix="/drugs", tags=["drugs"])


@router.get("/", response_model=List[DrugOut])
def search_drugs(
    q: str = "",
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.admin, UserRole.nurse, UserRole.gp)),
):
    """Search local drug cache by name."""
    query = db.query(Drug)
    if q:
        query = query.filter(Drug.name.ilike(f"%{q}%"))
    return query.order_by(Drug.name).limit(50).all()


@router.post("/sync/{dmd_id}", response_model=DrugOut)
def sync_drug(
    dmd_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.admin)),
):
    """Fetch a drug from the NHS dm+d API and upsert it into the local cache."""
    data = fetch_dmd_drug(dmd_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Drug {dmd_id} not found in dm+d")

    drug = db.query(Drug).filter(Drug.dmd_id == dmd_id).first()
    if drug:
        for key, value in data.items():
            setattr(drug, key, value)
    else:
        drug = Drug(**data)
        db.add(drug)

    db.commit()
    db.refresh(drug)
    return drug
