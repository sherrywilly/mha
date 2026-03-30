# SafeCare eMAR & Lead Engine

A clinical-grade UK care home medication administration and lead management platform.

## Architecture

- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL (multi-tenant via row-level `care_home_id` filtering)
- **Auth**: JWT (HS256), role-based (Admin, Nurse, GP, Family)
- **Audit**: Immutable WORM audit trail — records can only be corrected, never deleted
- **Integrations**: NHS dm+d medication dictionary sync

## Key Features

| Feature | Description |
|---|---|
| **Vitals Bridge** | BP/Blood-sugar captured during med round; automatically blocks medication & alerts GP if reading is out of range |
| **WORM Audit Trail** | Every medication administration is immutably signed; corrections require a reason |
| **Family Portal** | Read-only login for relatives to see medication and care status |
| **Lead CRM** | Smart Lead Scoring ranks enquiries by urgency (hospital discharge > browsing) |
| **dm+d Sync** | Medications validated against NHS Dictionary of Medicines and Devices |
| **Offline Engine** | Service worker / local queue ensures data is never lost if connection drops mid-round |

## 6-Month Roadmap

| Month | Focus | Milestone |
|---|---|---|
| 1 | Data Core | Resident profiles + dm+d sync |
| 2 | Med Round | Mobile UI + barcode scanning |
| 3 | Offline Engine | Mid-round crash recovery |
| 4 | Lead CRM | Enquiry forms + visual pipeline |
| 5 | Security Audit | Cyber Essentials + DTAC |
| 6 | Pilot | 30-day paperless trial in Essex/Suffolk |

## Pricing

| Tier | Price | Includes |
|---|---|---|
| 1 | £3 / bed / month | eMAR only |
| 2 | £5 / bed / month | eMAR + Leads CRM |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn main:app --reload
```

## CQC Compliance Notes

- All medication events are stored in an append-only audit table
- Corrections are stored as new rows referencing the original, with a mandatory reason
- Family Portal access is read-only and scoped to the resident's care home tenant
- Multi-tenant isolation ensures Care Home A cannot access Care Home B data
