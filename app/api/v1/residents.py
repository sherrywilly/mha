from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.resident import Resident
from app.schemas.resident import ResidentCreate, ResidentUpdate, ResidentOut

router = APIRouter()

@router.get("/residents", response_model=List[ResidentOut])
def list_residents(unit_id: Optional[str] = Query(None), db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Resident)
    if unit_id:
        q = q.filter(Resident.unit_id == unit_id)
    return q.all()

@router.post("/residents", response_model=ResidentOut, status_code=201)
def create_resident(payload: ResidentCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    resident = Resident(id=str(uuid4()), **payload.model_dump())
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident

@router.get("/residents/{resident_id}", response_model=ResidentOut)
def get_resident(resident_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(Resident).filter(Resident.id == resident_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return r

@router.put("/residents/{resident_id}", response_model=ResidentOut)
def update_resident(resident_id: str, payload: ResidentUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(Resident).filter(Resident.id == resident_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r

@router.delete("/residents/{resident_id}", status_code=204)
def delete_resident(resident_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(Resident).filter(Resident.id == resident_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(r)
    db.commit()
