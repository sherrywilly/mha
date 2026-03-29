from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.api.deps import get_db, get_current_user
from app.models.stock import StockLocation, StockItem, StockTransaction, StockAlert
from app.schemas.stock import (
    StockLocationCreate, StockLocationOut,
    StockTransactionCreate, StockTransactionOut,
    StockItemOut, StockAlertOut, StockCountItem,
)

router = APIRouter()

@router.get("/stock/locations", response_model=List[StockLocationOut])
def list_locations(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(StockLocation).all()

@router.post("/stock/locations", response_model=StockLocationOut, status_code=201)
def create_location(payload: StockLocationCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    loc = StockLocation(id=str(uuid4()), **payload.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc

@router.get("/stock/items", response_model=List[StockItemOut])
def list_items(location_id: Optional[str] = Query(None), db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(StockItem)
    if location_id:
        q = q.filter(StockItem.location_id == location_id)
    return q.all()

@router.post("/stock/transactions", response_model=StockTransactionOut)
def create_stock_transaction(payload: StockTransactionCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    tx = StockTransaction(id=str(uuid4()), **payload.model_dump())
    try:
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
    except IntegrityError:
        db.rollback()
        existing = db.query(StockTransaction).filter(
            StockTransaction.client_event_id == payload.client_event_id
        ).first()
        if existing:
            return existing
        raise HTTPException(status_code=409, detail="Conflict")

@router.post("/stock/counts", response_model=List[dict])
def batch_count(items: List[StockCountItem], db: Session = Depends(get_db), _=Depends(get_current_user)):
    results = []
    for item in items:
        stock_item = db.query(StockItem).filter(StockItem.id == item.item_id).first()
        if not stock_item:
            results.append({"item_id": item.item_id, "error": "not found"})
            continue
        existing = db.query(StockTransaction).filter(StockTransaction.client_event_id == item.client_event_id).first()
        if existing:
            results.append({"item_id": item.item_id, "status": "duplicate"})
            continue
        tx = StockTransaction(
            id=str(uuid4()),
            item_id=item.item_id,
            transaction_type="count",
            quantity_change=item.counted_qty - stock_item.on_hand_qty,
            quantity_after=item.counted_qty,
            performed_by_id=item.performed_by_id,
            client_event_id=item.client_event_id,
        )
        stock_item.on_hand_qty = item.counted_qty
        db.add(tx)
        results.append({"item_id": item.item_id, "status": "counted"})
    db.commit()
    return results

@router.get("/stock/alerts", response_model=List[StockAlertOut])
def list_alerts(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(StockAlert).all()
