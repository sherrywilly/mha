import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def test_unit(db, setup_db):
    from app.models.organisation import Organisation, Site, Unit
    org = Organisation(id=str(uuid4()), name="Idempotency Test Org", is_active=True)
    db.add(org)
    db.commit()
    site = Site(id=str(uuid4()), organisation_id=org.id, name="Test Site", address="123 Test St", is_active=True)
    db.add(site)
    db.commit()
    unit = Unit(id=str(uuid4()), site_id=site.id, name="Test Unit", is_active=True)
    db.add(unit)
    db.commit()
    return unit

@pytest.fixture(scope="module")
def test_resident(db, test_unit):
    from app.models.resident import Resident
    import datetime
    resident = Resident(
        id=str(uuid4()),
        unit_id=test_unit.id,
        first_name="John",
        last_name="Doe",
        dob=datetime.date(1940, 1, 1),
        nhs_number="1234567890",
        is_active=True,
    )
    db.add(resident)
    db.commit()
    return resident

@pytest.fixture(scope="module")
def test_drug(db):
    from app.models.medication import Drug
    drug = Drug(
        id=str(uuid4()),
        name="Paracetamol",
        generic_name="Paracetamol",
        category="Analgesic",
        unit_of_measure="mg",
        is_active=True,
    )
    db.add(drug)
    db.commit()
    return drug

@pytest.fixture(scope="module")
def test_order(db, test_resident, test_drug):
    from app.models.medication import MedicationOrder
    import datetime
    order = MedicationOrder(
        id=str(uuid4()),
        resident_id=test_resident.id,
        drug_id=test_drug.id,
        prescribed_by="Dr. Smith",
        dose_amount=500.0,
        dose_unit="mg",
        route="oral",
        frequency_type="daily_times",
        daily_times=["08:00", "20:00"],
        start_date=datetime.date.today(),
        is_active=True,
    )
    db.add(order)
    db.commit()
    return order

@pytest.fixture(scope="module")
def test_stock_location(db, test_unit):
    from app.models.stock import StockLocation
    loc = StockLocation(
        id=str(uuid4()),
        unit_id=test_unit.id,
        name="Main Shelf",
        location_type="shelf",
        is_active=True,
    )
    db.add(loc)
    db.commit()
    return loc

@pytest.fixture(scope="module")
def test_stock_item(db, test_stock_location, test_drug):
    from app.models.stock import StockItem
    item = StockItem(
        id=str(uuid4()),
        location_id=test_stock_location.id,
        drug_id=test_drug.id,
        on_hand_qty=100.0,
        reorder_threshold=10.0,
        unit_of_measure="mg",
    )
    db.add(item)
    db.commit()
    return item

def test_admin_record_idempotency(client, admin_token, admin_user, test_order, test_resident, db):
    from app.models.emar import AdministrationRecord
    client_event_id = str(uuid4())
    payload = {
        "order_id": test_order.id,
        "resident_id": test_resident.id,
        "administered_by_id": admin_user.id,
        "administered_at": "2024-01-01T08:00:00",
        "status": "given",
        "client_event_id": client_event_id,
    }
    resp1 = client.post("/api/v1/administration-records", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp1.status_code in (200, 201)
    resp2 = client.post("/api/v1/administration-records", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp2.status_code in (200, 201)
    # Both responses should return the same record
    assert resp1.json()["id"] == resp2.json()["id"]
    assert resp1.json()["client_event_id"] == resp2.json()["client_event_id"]
    count = db.query(AdministrationRecord).filter_by(client_event_id=client_event_id).count()
    assert count == 1

def test_stock_transaction_idempotency(client, admin_token, admin_user, test_stock_item, db):
    from app.models.stock import StockTransaction
    client_event_id = str(uuid4())
    payload = {
        "item_id": test_stock_item.id,
        "transaction_type": "receive",
        "quantity_change": 50.0,
        "quantity_after": 150.0,
        "performed_by_id": admin_user.id,
        "client_event_id": client_event_id,
    }
    resp1 = client.post("/api/v1/stock/transactions", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp1.status_code in (200, 201)
    resp2 = client.post("/api/v1/stock/transactions", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp2.status_code in (200, 201)
    # Both responses should return the same record
    assert resp1.json()["id"] == resp2.json()["id"]
    assert resp1.json()["client_event_id"] == resp2.json()["client_event_id"]
    count = db.query(StockTransaction).filter_by(client_event_id=client_event_id).count()
    assert count == 1
