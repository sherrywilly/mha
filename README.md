# MHA eMAR Platform — Backend

A production-minded **FastAPI** backend for the nursing-home eMAR + compliance platform.

## Features

- **Multi-tenant hierarchy**: Organisation → Site → Unit
- **RBAC + unit-scoped access**: Admin, Manager, Nurse, Senior Carer, Carer roles
- **eMAR scheduling**: DoseDue generation from MedicationOrder schedules, AdministrationRecord capture
- **Controlled drug double-sign**: CDTransaction with witness workflow
- **Stock management**: Shelf vs trolley locations, on-hand quantities, low-stock alerts, idempotent transactions
- **Prescription workflow**: Draft → AI-drafted → Approved → Sent (AI stub, no real email)
- **Medication error log**: Near-miss / error types with manager close workflow
- **Topical application**: Body-region capture linked to AdministrationRecord
- **Idempotent event ingestion**: `client_event_id` deduplication for offline sync
- **JWT authentication** with RBAC enforcement
- **Audit fields** on all clinical models (`created_at`, `updated_at`, `created_by_id`)
- **IP allowlisting hooks** (placeholder for per-site enforcement)

## Prerequisites

- Python 3.11+
- PostgreSQL (for production) or SQLite (tests use in-memory SQLite)

## Installation

```bash
# Clone the repo
git clone https://github.com/sherrywilly/mha.git
cd mha

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and edit as needed:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost/mha` | PostgreSQL connection string |
| `SECRET_KEY` | `changeme-dev-secret` | JWT signing key — **change in production** |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |
| `ALLOWED_IPS` | `[]` | JSON list of allowlisted CIDR ranges (empty = no restriction) |

## Database Setup

```bash
# Create the database (PostgreSQL)
createdb mha

# Run Alembic migrations
alembic upgrade head
```

## Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Documentation

- **Interactive docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Running Tests

Tests use an in-memory SQLite database — no PostgreSQL required.

```bash
pytest tests/ -v
```

## API Overview

All routes are prefixed with `/api/v1`.

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Obtain JWT token |
| POST | `/auth/users` | Create user (admin only) |
| GET | `/auth/me` | Current user profile |
| CRUD | `/organisations` | Manage organisations (admin) |
| CRUD | `/organisations/{id}/sites` | Manage sites |
| CRUD | `/sites/{id}/units` | Manage units |
| CRUD | `/residents` | Manage residents (unit-scoped) |
| CRUD | `/drugs` | Drug catalogue |
| CRUD | `/medication-orders` | Medication orders per resident |
| POST | `/medication-orders/{id}/generate-doses` | Generate DoseDue schedule |
| GET | `/doses-due` | Query due doses by unit/date |
| POST | `/administration-records` | Record administration (idempotent) |
| GET | `/administration-records` | Query administration records |
| POST | `/cd-transactions` | Create CD transaction |
| POST | `/cd-transactions/{id}/witness` | Second-sign CD transaction |
| GET | `/cd-transactions/pending-witness` | List pending witness records |
| GET/POST | `/stock/locations` | Stock locations |
| GET | `/stock/items` | Stock items by location |
| POST | `/stock/transactions` | Stock transaction (idempotent) |
| POST | `/stock/counts` | Batch count submission |
| GET | `/stock/alerts` | Low-stock / not-available alerts |
| POST | `/prescription-requests` | Create draft |
| POST | `/prescription-requests/{id}/ai-draft` | Request AI draft (stub) |
| POST | `/prescription-requests/{id}/approve` | Approve prescription |
| POST | `/prescription-requests/{id}/send` | Send prescription (stub) |
| POST | `/medication-errors` | Report error / near-miss |
| GET | `/medication-errors` | List errors |
| POST | `/medication-errors/{id}/close` | Manager close |
| POST | `/events/ingest` | Idempotent batch event ingestion |
| GET | `/health` | Health check |

## Project Structure

```
.
├── main.py                  # FastAPI entrypoint
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial.py  # All tables in one migration
├── app/
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # SQLAlchemy engine + session
│   ├── core/
│   │   ├── security.py      # JWT + password hashing
│   │   └── rbac.py          # Role constants + permissions
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   └── api/
│       ├── deps.py          # Auth + RBAC dependencies
│       └── v1/              # All API routers
└── tests/
    ├── conftest.py          # SQLite test fixtures
    ├── test_auth.py         # Auth flow tests
    └── test_idempotency.py  # Deduplication tests
```
