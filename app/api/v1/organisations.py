from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_role
from app.models.organisation import Organisation, Site, Unit
from app.schemas.organisation import (
    OrganisationCreate, OrganisationOut,
    SiteCreate, SiteOut,
    UnitCreate, UnitOut,
)
from app.core.rbac import ROLE_ADMIN

router = APIRouter()

@router.get("/organisations", response_model=List[OrganisationOut])
def list_organisations(db: Session = Depends(get_db)):
    return db.query(Organisation).all()

@router.post("/organisations", response_model=OrganisationOut, status_code=201)
def create_organisation(payload: OrganisationCreate, db: Session = Depends(get_db), _=Depends(require_role(ROLE_ADMIN))):
    org = Organisation(id=str(uuid4()), **payload.model_dump())
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

@router.get("/organisations/{org_id}", response_model=OrganisationOut)
def get_organisation(org_id: str, db: Session = Depends(get_db)):
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Not found")
    return org

@router.put("/organisations/{org_id}", response_model=OrganisationOut)
def update_organisation(org_id: str, payload: OrganisationCreate, db: Session = Depends(get_db), _=Depends(require_role(ROLE_ADMIN))):
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(org, k, v)
    db.commit()
    db.refresh(org)
    return org

@router.delete("/organisations/{org_id}", status_code=204)
def delete_organisation(org_id: str, db: Session = Depends(get_db), _=Depends(require_role(ROLE_ADMIN))):
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(org)
    db.commit()

@router.get("/organisations/{org_id}/sites", response_model=List[SiteOut])
def list_sites(org_id: str, db: Session = Depends(get_db)):
    return db.query(Site).filter(Site.organisation_id == org_id).all()

@router.post("/organisations/{org_id}/sites", response_model=SiteOut, status_code=201)
def create_site(org_id: str, payload: SiteCreate, db: Session = Depends(get_db), _=Depends(require_role(ROLE_ADMIN))):
    data = payload.model_dump()
    data["organisation_id"] = org_id
    site = Site(id=str(uuid4()), **data)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site

@router.get("/sites/{site_id}/units", response_model=List[UnitOut])
def list_units(site_id: str, db: Session = Depends(get_db)):
    return db.query(Unit).filter(Unit.site_id == site_id).all()

@router.post("/sites/{site_id}/units", response_model=UnitOut, status_code=201)
def create_unit(site_id: str, payload: UnitCreate, db: Session = Depends(get_db), _=Depends(require_role(ROLE_ADMIN))):
    data = payload.model_dump()
    data["site_id"] = site_id
    unit = Unit(id=str(uuid4()), **data)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit
