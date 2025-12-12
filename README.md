# Wellspring AI EHR Prototype

This is a **backend/API prototype** for Wellspring Family & Community Institute's AI-enabled EHR.
It focuses on:
- Appointment scheduling (calendar-ready)
- Progress notes (including a Wiley-style structured note generator)
- Billing & superbills
- Insurance and Bill-To info
- Client portal stubs
- Telehealth session stubs
- E-prescribing stubs (medications + prescriptions)
- ICD-10 storage/search and AI suggestions
- Intake, consent, payment consent, and telehealth consent PDF templates
- Admin staff preferences and service-line–aware UI spec (`ui_spec.json`)

## 1. Environment & Database

The project uses **environment variables** loaded from `.env` via `python-dotenv`.

- Example file: `.env.example`
- You can copy it to `.env` and adjust as needed.

Default local database (for development):

```env
DATABASE_URL=sqlite+aiosqlite:///./wellspring_ehr.db
```

Example Postgres credentials (for future hosting):

```env
DB_ENGINE=postgresql+asyncpg
DB_HOST=localhost
DB_PORT=5432
DB_NAME=wellspring_ehr
DB_USER=wellspring_ehr_user
DB_PASSWORD=super-secure-password
DATABASE_URL=postgresql+asyncpg://wellspring_ehr_user:super-secure-password@localhost:5432/wellspring_ehr
```

The **actual** running connection string is `settings.database_url` in `app/config.py`.

## 2. Installing & Running Locally

```bash
cd wellspring_ehr
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Make sure .env exists (copy from .env.example if needed)
cp .env.example .env  # or create/edit manually

# Run the API
uvicorn app.main:app --reload
```

Then open:

- API docs: http://localhost:8000/docs
- Root landing page: http://localhost:8000/
- Client portal stub: http://localhost:8000/portal/login

On startup, FastAPI will create all database tables using the configured `DATABASE_URL`.

## 3. Key Endpoints

- **Clients**: `POST /clients/`, `GET /clients/`, `GET /clients/{id}`
- **Users**: `POST /users`, `POST /login`, `POST /verify-reset-token`, `POST /forgot-password`, `POST /reset-password`
- **Appointments**:
  - `POST /appointments/`
  - `GET /appointments/`
  - `GET /appointments/calendar?start=YYYY-MM-DD&end=YYYY-MM-DD&provider_id=...`
- **Notes**:
  - `POST /notes/`
  - `GET /notes/client/{client_id}`
  - `POST /ai/note-suggestions`
  - `POST /ai/wiley-style-note`
  - `POST /ai/icd10-suggest`
- **Billing**: `POST /billing/invoices`, `GET /billing/invoices`
- **Insurance**: `POST /insurance/`, `GET /insurance/client/{client_id}`
- **Family Contacts**: `POST /family-contacts/`, `GET /family-contacts/client/{client_id}`
- **Staff Assignments**: `POST /staff-assignments/`, `GET /staff-assignments/client/{client_id}`
- **Documents**: `POST /documents/`, `GET /documents/client/{client_id}`
- **Reminders**: `POST /reminders/`, `GET /reminders/client/{client_id}`
- **Assessments**: `POST /assessments/`, `GET /assessments/client/{client_id}`
- **Telehealth Sessions**: `POST /telehealth/sessions`, `GET /telehealth/sessions`
- **Prescribing**:
  - `POST /prescribing/medications`, `GET /prescribing/medications`
  - `POST /prescribing/prescriptions`, `GET /prescribing/prescriptions`
- **ICD-10 Codes**: `POST /icd10/`, `GET /icd10/`, `GET /icd10/search?q=anxiety`
- **Reports/PDFs**:
  - `GET /reports/superbill/{invoice_id}`
  - `GET /reports/consent/{client_id}`
  - `GET /reports/intake/{client_id}`
  - `GET /reports/payment-consent/{client_id}`
  - `GET /reports/telehealth-consent/{client_id}`
- **Admin Staff Preferences**:
  - `POST /admin/preferences`
  - `GET /admin/preferences/{user_id}`

## 4. UI Spec (Service-Line–Aware Tabs)

The file `app/ui_spec.json` defines tabs and modules for different Wellspring service lines
(`outpatient`, `peer`, `waads`, `dahs`).

The backend exposes this via:

- `GET /config/ui-spec`

Your front-end or low-code tool can:

1. Fetch `/config/ui-spec`
2. Filter tabs by `serviceLine` (e.g., only those that include `"waads"`)
3. Build navigation and screens accordingly.

## 5. HostGator / Cloud Deployment Notes

This prototype is a **Python/FastAPI** app. To deploy on HostGator (or any cloud):

- Ensure the hosting plan supports **Python + ASGI** (e.g., VPS or dedicated).
- Point Gunicorn/Uvicorn (or a managed ASGI runner) to `app.main:app`.
- Set environment variables (`DATABASE_URL`, `SECRET_KEY`, etc.) via the hosting control panel.
- Use a managed Postgres/MySQL instance for production instead of SQLite.

Security, authentication, and HIPAA hardening are **not** fully implemented here.
This is a functional prototype and must be extended before production use.
