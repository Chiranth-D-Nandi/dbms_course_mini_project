<!-- Owner: Person A -->
# Project Contributors & Ownership Matrix

## DBMS Level 3 Experiential Learning Project
**Institution**: PES University  
**Project Title**: Tatkal-Style High-Concurrency Train Booking System  
**Academic Year**: 2026  

---

## Team Members

| Name | SRN / PRN | GitHub Handle | Designated Role | Split |
| :--- | :--- | :--- | :--- | :--- |
| **Chiranth D Nandi** | `PES2UG24AM048` | `Chiranth-D-Nandi` | **Person A** (Data & Backend Half) | 50% |
| **Jashruth K A** | `PES2UG24AM069` | `Jashruth-KA` | **Person B** (Experience & Ops Half) | 50% |

---

## Detailed Responsibility Breakdown

### Person A: Chiranth D Nandi (`PES2UG24AM048`) — Data & Backend Half
- **MySQL Database Architecture & DDL**:
  - Authored complete relational schema (`db/01_schema.sql`) with 15 normalized tables (3NF/BCNF).
  - Designed check constraints, ENUMs, foreign keys with referential integrity rules, primary keys.
  - Implemented `ALTER` and `DROP` demonstrations (`db/02_alter_demo.sql`) and database reset script (`db/00_reset.sql`).
  - Authored local MySQL setup guide and role provisioning (`db/setup_local.md`).
- **Programmable Database Objects**:
  - Implemented business-critical stored procedures (`db/03_procedures.sql`): `sp_generate_run_inventory`, `fn_calc_fare`, `sp_search_trains`, `sp_book_tickets` (concurrency-safe with `FOR UPDATE SKIP LOCKED`), `sp_confirm_payment`, `sp_cancel_booking`, and `sp_release_expired_holds`.
  - Implemented audit and validation triggers (`db/04_triggers.sql`): `trg_booking_status_audit`, `trg_run_seat_audit`, `trg_booking_route_check`, `trg_passenger_validate`, `trg_payment_amount_check`, `trg_prevent_booked_seat_delete`.
  - Implemented relational views (`db/05_views.sql`): `v_run_availability`, `v_booking_summary`, `v_train_route`, `v_admin_revenue`, `v_passenger_age`.
  - Configured recurring MySQL event (`db/06_events.sql`): `ev_release_expired_holds` running every 30 seconds.
- **Django REST Framework Backend**:
  - Configured project settings, database connection routing to MySQL via PyMySQL (`db_app_rw`), JWT authentication (`djangorestframework-simplejwt`), and CORS headers.
  - Authored unmanaged Django models (`managed = False`) mapping directly to underlying relational tables.
  - Implemented REST API endpoints, serializers, role-based access control (ADMIN vs CUSTOMER), idempotency handling, rate limiting/throttling, and deadlock retry logic.
  - Authored `python manage.py init_db` management command for sequential DDL/DML bootstrap.
- **Vector Search Query Service**:
  - Built ChromaDB query client wrapper (`chroma_svc/client.py`, `chroma_svc/search.py`) supporting cosine similarity queries and hybrid SQL joins.
  - Implemented `/api/search/trains` and `/api/search/faq` API endpoints.
- **Backend Concurrency & Unit Testing**:
  - Authored comprehensive pytest suite (`backend/tests/`) featuring multi-threaded stress testing proving zero double-bookings under concurrent seat contention.
- **Technical Documentation & Contracts**:
  - Authored OpenAPI 3 specification (`docs/api_contract.yaml` and `docs/api_contract.md`).
  - Authored `docs/er_diagram.md` (with Mermaid ER diagram), `docs/relational_schema.md` (with normalization to 3NF/BCNF), `docs/data_dictionary.md`, `docs/db_choice_justification.md`, `docs/sql_vector_implementation.md`, `docs/important_queries.md` (`db/07_queries.sql`), `db/08_explain_demo.sql`, `db/09_isolation_demo.md`, and `docs/system_architecture.md`.
  - Maintained project repository hygiene (`.gitignore`, `.env.example`, `CONTRIBUTORS.md`, `COMMIT_PLAN.md`, `OWNERSHIP.csv`, `scripts/handoff.*`).

---

### Person B: Jashruth K A (`PES2UG24AM069`) — Experience & Ops Half
- **Next.js 14+ Frontend Application**:
  - Scaffolded Next.js App Router application in TypeScript strict mode with Tailwind CSS styling and Lucide icons.
  - Built typed API client communicating with Django REST backend (`NEXT_PUBLIC_API_URL`).
  - Implemented authentication flow with JWT storage, refresh cycle, and role-guarded route middleware (`ADMIN` vs `CUSTOMER`).
  - Built responsive UI pages: Home `/`, Train Search Results `/search`, Train Route Timeline `/trains/[id]`, Ticket Booking `/book/[runId]`, Payment Simulation `/pay/[pnr]`, My Bookings `/bookings`, Booking Details & Cancellation `/bookings/[pnr]`, Help & FAQ `/help`, Login `/login`, and Register `/register`.
  - Built Admin Portal: `/admin` (interactive analytics dashboard with revenue, occupancy, tatkal demand), `/admin/trains`, `/admin/runs`, `/admin/bookings`, and `/admin/audit-log`.
  - Developed mock service worker (`frontend/mocks/`) allowing standalone UI development against the API contract.
- **Tatkal High-Concurrency User Experience**:
  - Engineered live countdown timer to the Tatkal booking window opening.
  - Built real-time interactive coach seat map with berth positions and quota markings.
  - Built 5-minute seat-hold countdown timer on the payment screen with automatic expiry warning.
  - Designed idempotent payment button with retry-safe key caching and clear sold-out / try-again state handling.
- **Data Pipeline & Vector Ingestion**:
  - Authored comprehensive realistic database seeder (`scripts/seed.py`): ~30 stations across India, ~25 express/Rajdhani trains with detailed stops, coaches, seats, runs for 10 days, users, and historical bookings for analytics.
  - Built ChromaDB ingestion pipeline (`scripts/ingest_chroma.py`): downloads sentence-transformers `all-MiniLM-L6-v2` to local disk (`./models/`) for offline execution, generates descriptive documents for trains, and embeds 35+ Tatkal policy and ticketing FAQ chunks.
- **Testing, Load Testing & Ops Tooling**:
  - Authored Locust high-concurrency load test (`scripts/locustfile.py`) simulating 300-500 simultaneous users hitting Tatkal booking endpoints.
  - Authored Playwright end-to-end test suite verifying complete customer and admin flows.
  - Built cross-platform setup, dev, and demo scripts (`scripts/setup.*`, `scripts/dev.*`, `scripts/demo_*`, `scripts/preflight.*`).
- **Product Documentation & Evaluation Material**:
  - Authored `README.md`, `docs/problem_statement.md`, `docs/objectives.md`, `docs/scope.md`, `docs/functional_requirements.md`, `docs/screenshots.md`, `docs/testing_results.md`, `docs/conclusion_future_work.md`, and `docs/DEMO_SCRIPT.md`.
