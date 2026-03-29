from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.controlled_drug import CDTransaction, CDStatus
from app.schemas.controlled_drug import CDTransactionCreate, CDTransactionOut

router = APIRouter()

@router.post("/cd-transactions", response_model=CDTransactionOut, status_code=201)
def create_cd_transaction(payload: CDTransactionCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    tx = CDTransaction(id=str(uuid4()), **payload.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.post("/cd-transactions/{tx_id}/witness", response_model=CDTransactionOut)
def witness_cd_transaction(tx_id: str, witnessed_by_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    tx = db.query(CDTransaction).filter(CDTransaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Not found")
    from datetime import datetime, timezone
    tx.witnessed_by_id = witnessed_by_id
    tx.witnessed_at = datetime.now(timezone.utc)
    tx.status = CDStatus.complete
    db.commit()
    db.refresh(tx)
    return tx

@router.get("/cd-transactions/pending-witness", response_model=List[CDTransactionOut])
def pending_witness(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(CDTransaction).filter(CDTransaction.status == CDStatus.pending_witness).all()
