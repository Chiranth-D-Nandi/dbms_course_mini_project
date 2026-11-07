# Tatkal train booking — DBMS mini project

A local course-project application with a Next.js frontend, Django REST API, MySQL 8 database, and Chroma semantic search. Payment and refund processing are simulations; no bank is connected.

## Start on this computer

The project is configured in `.env` to use the isolated `tatkal_review` database. Existing unrelated databases were preserved. From the repository root:

```powershell
.\scripts\dev.ps1
```

Open the frontend URL printed by the launcher. It prefers http://localhost:3000 and API port 8000; if another app uses them, it selects free ports and connects the services automatically.

| Account | Email | Password |
| --- | --- | --- |
| Customer | chiranth@example.com | Customer@123 |
| Customer | jashruth@example.com | Customer@123 |
| Administrator | admin@tatkal.com | Admin@123 |

Registration creates customers only. Demo administrators are created by the seed script. Keep `.env` out of Git.

## What works

- Register, log in, refresh sessions, and log out.
- Search stations and dated train routes; filter classes/types and sort results.
- Inspect train timetables and coach seat maps.
- Reserve up to six General passengers or four Tatkal passengers per booking.
- Hold automatically assigned seats for eight minutes, then confirm a simulated UPI/card/netbanking payment with retry protection.
- View and print tickets, see reservation history, cancel confirmed tickets, and display the computed refund.
- Expire unpaid reservations atomically through a MySQL event every 30 seconds, or the admin sweep action.
- Browse admin revenue/occupancy reports, inspect trigger audit logs, and schedule train runs with inventory.
- Search the local train catalog and project-policy FAQs using sentence-transformer embeddings and ChromaDB.

SQL provides the schema, foreign keys, composite keys, constraints, indexes, stored procedures, fare function, triggers, views, and expiry event. Seat allocation uses `FOR UPDATE SKIP LOCKED` and a unique active passenger-seat constraint. The Django models use real composite primary keys (Django 5.2+).

## Fresh setup

Requires Python 3.11+, Node.js 20+, and a running MySQL 8 server with an administrator account allowed to create the project schema, accounts, routines and events.

1. Copy `.env.example` to `.env`, set `MYSQL_ROOT_PASSWORD`, and choose a new `MYSQL_DATABASE`. Quote passwords containing spaces or `#`.
2. On Windows run `.\scripts\setup.ps1`; on Linux/macOS run `bash scripts/setup.sh`.
3. Run the dev launcher and open the frontend.

Setup creates a virtual environment, installs dependencies, initializes an empty database, seeds dated runs and demo accounts, downloads/caches the embedding model, indexes search content, and builds the frontend. The first model download needs internet; subsequent searches use the local cache. Re-running setup preserves existing project tables.

Manual Windows commands:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend/manage.py init_db --if-empty
.\.venv\Scripts\python.exe scripts/seed.py
.\.venv\Scripts\python.exe scripts/ingest_chroma.py
cd frontend
npm ci
npm run build
```

`init_db --update-objects` refreshes routines, views, triggers and events while preserving table data. `init_db --reset` explicitly erases the selected project's data. It is not needed to start the application. `seed.py` extends the run calendar for the next ten days and skips existing sample payments, so rerun it when demonstrating on a later date. The SQL files target `tatkal_db` when run directly; the management command safely substitutes the database and account names from `.env`.

## Rules used in this demonstration

- Journey date means the train's originating run date; stops can have overnight day offsets.
- AC Tatkal opens at 10:00 IST and Sleeper Tatkal at 11:00 IST one day before the run. Booking after boarding departure is rejected.
- Holds last 480 seconds. The UI countdown does not override the database deadline.
- General cancellation refunds: 90% above 48 hours, 50% at 12–48 hours, 25% at 4–12 hours, zero below four hours. Confirmed Tatkal refunds are zero. These are simplified project rules, not an official railway tariff.
- The map is informational; allocation is automatic. A physical seat is reserved for the whole run. Waitlists, partial-route seat reuse and live railway integration are outside scope.

## Verify

On Windows, `.\scripts\verify.ps1` runs the complete workflow below.

```powershell
.\.venv\Scripts\python.exe backend/manage.py check
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

Backend tests create and delete their own temporary MySQL database rather than modifying your demo database. Root credentials in `.env` are required for that provisioning. Browser tests start local API/frontend servers, use the demo database and create sample tickets/runs. They create a separate `.next-e2e` build on ports 3100/8100 and require the seeded search index. They leave the normal build and other running apps untouched.

See [testing results](docs/testing_results.md), [demo walkthrough](docs/DEMO_SCRIPT.md), [API contract](docs/api_contract.md), and [database schema](docs/relational_schema.md). Performance results should be taken from actual local test runs, not treated as production latency guarantees.

## Team

Chiranth D Nandi and Jashruth K A. Original contribution assignments are recorded in [CONTRIBUTORS.md](CONTRIBUTORS.md) and [OWNERSHIP.csv](OWNERSHIP.csv).
