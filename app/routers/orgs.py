from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, log_audit_event
from app.database import get_db
from app.models.org import (
    AccessPolicy, ApprovedDevice, Organisation, Site, Unit, User
)
from app.schemas.org import (
    AccessPolicyCreate, AccessPolicyRead,
    ApprovedDeviceCreate, ApprovedDeviceRead,
    OrganisationCreate, OrganisationRead, OrganisationUpdate,
    SiteCreate, SiteRead, SiteUpdate,
    UnitCreate, UnitRead, UnitUpdate,
)

router = APIRouter(tags=["organisations"])


# ── Organisations ──────────────────────────────────────────────
@router.get("/orgs", response_model=list[OrganisationRead])
async def list_orgs(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organisation))
    return result.scalars().all()


@router.post("/orgs", response_model=OrganisationRead, status_code=201)
async def create_org(payload: OrganisationCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org = Organisation(**payload.model_dump())
    db.add(org)
    await db.flush()
    await log_audit_event(db, "CREATE_ORG", "organisation", user_id=current_user.id, resource_id=org.id)
    return org


@router.get("/orgs/{org_id}", response_model=OrganisationRead)
async def get_org(org_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organisation, org_id)
    if not org:
        raise HTTPException(404, "Organisation not found")
    return org


@router.put("/orgs/{org_id}", response_model=OrganisationRead)
async def update_org(org_id: str, payload: OrganisationUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organisation, org_id)
    if not org:
        raise HTTPException(404, "Organisation not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(org, k, v)
    await log_audit_event(db, "UPDATE_ORG", "organisation", user_id=current_user.id, resource_id=org_id)
    return org


@router.delete("/orgs/{org_id}", status_code=204)
async def delete_org(org_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organisation, org_id)
    if not org:
        raise HTTPException(404, "Organisation not found")
    org.is_active = False
    await log_audit_event(db, "DELETE_ORG", "organisation", user_id=current_user.id, resource_id=org_id)


# ── Sites ──────────────────────────────────────────────────────
@router.get("/orgs/{org_id}/sites", response_model=list[SiteRead])
async def list_sites(org_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Site).where(Site.org_id == org_id))
    return result.scalars().all()


@router.post("/orgs/{org_id}/sites", response_model=SiteRead, status_code=201)
async def create_site(org_id: str, payload: SiteCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    site = Site(org_id=org_id, **payload.model_dump())
    db.add(site)
    await db.flush()
    await log_audit_event(db, "CREATE_SITE", "site", user_id=current_user.id, resource_id=site.id)
    return site


@router.get("/sites/{site_id}", response_model=SiteRead)
async def get_site(site_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    site = await db.get(Site, site_id)
    if not site:
        raise HTTPException(404, "Site not found")
    return site


@router.put("/sites/{site_id}", response_model=SiteRead)
async def update_site(site_id: str, payload: SiteUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    site = await db.get(Site, site_id)
    if not site:
        raise HTTPException(404, "Site not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(site, k, v)
    await log_audit_event(db, "UPDATE_SITE", "site", user_id=current_user.id, resource_id=site_id)
    return site


# ── Units ──────────────────────────────────────────────────────
@router.get("/sites/{site_id}/units", response_model=list[UnitRead])
async def list_units(site_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Unit).where(Unit.site_id == site_id))
    return result.scalars().all()


@router.post("/sites/{site_id}/units", response_model=UnitRead, status_code=201)
async def create_unit(site_id: str, payload: UnitCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    unit = Unit(site_id=site_id, **payload.model_dump())
    db.add(unit)
    await db.flush()
    await log_audit_event(db, "CREATE_UNIT", "unit", user_id=current_user.id, resource_id=unit.id)
    return unit


@router.get("/units/{unit_id}", response_model=UnitRead)
async def get_unit(unit_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    unit = await db.get(Unit, unit_id)
    if not unit:
        raise HTTPException(404, "Unit not found")
    return unit


@router.put("/units/{unit_id}", response_model=UnitRead)
async def update_unit(unit_id: str, payload: UnitUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    unit = await db.get(Unit, unit_id)
    if not unit:
        raise HTTPException(404, "Unit not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(unit, k, v)
    await log_audit_event(db, "UPDATE_UNIT", "unit", user_id=current_user.id, resource_id=unit_id)
    return unit


# ── Approved Devices ───────────────────────────────────────────
@router.post("/sites/{site_id}/devices", response_model=ApprovedDeviceRead, status_code=201)
async def register_device(site_id: str, payload: ApprovedDeviceCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    device = ApprovedDevice(site_id=site_id, registered_by=current_user.id, **payload.model_dump())
    db.add(device)
    await db.flush()
    return device


# ── Access Policy ──────────────────────────────────────────────
@router.get("/sites/{site_id}/access-policy", response_model=AccessPolicyRead)
async def get_access_policy(site_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccessPolicy).where(AccessPolicy.site_id == site_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(404, "Access policy not found")
    return policy


@router.post("/sites/{site_id}/access-policy", response_model=AccessPolicyRead, status_code=201)
async def upsert_access_policy(site_id: str, payload: AccessPolicyCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccessPolicy).where(AccessPolicy.site_id == site_id))
    policy = result.scalar_one_or_none()
    if policy:
        for k, v in payload.model_dump().items():
            setattr(policy, k, v)
    else:
        policy = AccessPolicy(site_id=site_id, **payload.model_dump())
        db.add(policy)
    await db.flush()
    return policy
