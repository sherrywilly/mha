from uuid import uuid4
from typing import List, Optional
from datetime import date, timedelta, datetime, timezone
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.medication import Drug, MedicationOrder
from app.models.emar import DoseDue, DoseStatus
from app.schemas.medication import DrugCreate, DrugOut, MedicationOrderCreate, MedicationOrderOut

router = APIRouter()

@router.get("/drugs", response_model=List[DrugOut])
def list_drugs(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Drug).all()

@router.post("/drugs", response_model=DrugOut, status_code=201)
def create_drug(payload: DrugCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    drug = Drug(id=str(uuid4()), **payload.model_dump())
    db.add(drug)
    db.commit()
    db.refresh(drug)
    return drug

@router.get("/drugs/{drug_id}", response_model=DrugOut)
def get_drug(drug_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    d = db.query(Drug).filter(Drug.id == drug_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    return d

@router.put("/drugs/{drug_id}", response_model=DrugOut)
def update_drug(drug_id: str, payload: DrugCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    d = db.query(Drug).filter(Drug.id == drug_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d

@router.delete("/drugs/{drug_id}", status_code=204)
def delete_drug(drug_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    d = db.query(Drug).filter(Drug.id == drug_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(d)
    db.commit()

@router.get("/medication-orders", response_model=List[MedicationOrderOut])
def list_orders(resident_id: Optional[str] = Query(None), db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(MedicationOrder)
    if resident_id:
        q = q.filter(MedicationOrder.resident_id == resident_id)
    return q.all()

@router.post("/medication-orders", response_model=MedicationOrderOut, status_code=201)
def create_order(payload: MedicationOrderCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    order = MedicationOrder(id=str(uuid4()), **payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/medication-orders/{order_id}", response_model=MedicationOrderOut)
def get_order(order_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    o = db.query(MedicationOrder).filter(MedicationOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    return o

@router.put("/medication-orders/{order_id}", response_model=MedicationOrderOut)
def update_order(order_id: str, payload: MedicationOrderCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    o = db.query(MedicationOrder).filter(MedicationOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(o, k, v)
    db.commit()
    db.refresh(o)
    return o

@router.delete("/medication-orders/{order_id}", status_code=204)
def delete_order(order_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    o = db.query(MedicationOrder).filter(MedicationOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(o)
    db.commit()

@router.post("/medication-orders/{order_id}/generate-doses")
def generate_doses(order_id: str, days: int = Query(7), db: Session = Depends(get_db), _=Depends(get_current_user)):
    order = db.query(MedicationOrder).filter(MedicationOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Not found")
    created = 0
    today = date.today()
    for day_offset in range(days):
        day = today + timedelta(days=day_offset)
        times = order.daily_times or ["08:00"]
        for t in times:
            h, m = map(int, t.split(":"))
            scheduled = datetime(day.year, day.month, day.day, h, m, tzinfo=timezone.utc)
            dose_key = hashlib.sha256(f"{order_id}{scheduled.isoformat()}".encode()).hexdigest()
            exists = db.query(DoseDue).filter(DoseDue.dose_key == dose_key).first()
            if not exists:
                dd = DoseDue(
                    id=str(uuid4()),
                    order_id=order_id,
                    resident_id=order.resident_id,
                    scheduled_datetime=scheduled,
                    window_start=scheduled - timedelta(hours=1),
                    window_end=scheduled + timedelta(hours=1),
                    status=DoseStatus.due,
                    dose_key=dose_key,
                )
                db.add(dd)
                created += 1
    db.commit()
    return {"created": created}
