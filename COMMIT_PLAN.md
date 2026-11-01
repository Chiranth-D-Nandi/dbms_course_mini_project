<!-- Owner: Person A -->
# Repository Commit Plan & Execution Log

This document tracks both the actual commits pushed by **Person A (Chiranth D Nandi)** and the planned progressive commits to be executed by **Person B (Jashruth K A)** via the handoff workflow.

---

## 1. PERSON A: Actual Commits Pushed to `origin/main`

Each entry corresponds to a small, atomic commit executed under Chiranth's git identity (`Chiranth D Nandi <nandi.chiranth@gmail.com>`).

| Commit # | Phase | Conventional Commit Message | Staged Files (Explicit Paths) |
| :--- | :--- | :--- | :--- |
| **A-01** | Phase 0 | `chore: add .gitignore and .env.example configuration` | `.gitignore`, `.env.example` |
| **A-02** | Phase 0 | `docs: add contributors matrix and file ownership manifest` | `CONTRIBUTORS.md`, `OWNERSHIP.csv` |
| **A-03** | Phase 0 | `chore: add handoff packaging scripts for Windows and POSIX` | `scripts/handoff.ps1`, `scripts/handoff.sh` |
| **A-04** | Phase 0 | `docs: add OpenAPI 3 specification and REST contract` | `docs/api_contract.yaml`, `docs/api_contract.md` |
| **A-05** | Phase 0 | `docs: establish commit execution plan for Person A and Person B` | `COMMIT_PLAN.md` |
| **A-06** | Phase 1 | `feat(db): add database reset and local setup guide` | `db/00_reset.sql`, `db/setup_local.md` |
| **A-07** | Phase 1 | `feat(db): add strong entities app_user, station, train` | `db/01_schema.sql` (Part 1) |
| **A-08** | Phase 1 | `feat(db): add train_running_day multivalued table and train_stop weak entity` | `db/01_schema.sql` (Part 2) |
| **A-09** | Phase 1 | `feat(db): add seat_class, coach, and seat relational tables` | `db/01_schema.sql` (Part 3) |
| **A-10** | Phase 1 | `feat(db): add train_run and run_seat concurrency control table` | `db/01_schema.sql` (Part 4) |
| **A-11** | Phase 1 | `feat(db): add booking, passenger, payment, cancellation, audit_log` | `db/01_schema.sql` (Part 5) |
| **A-12** | Phase 1 | `feat(db): add composite and fulltext indexes with check constraints` | `db/01_schema.sql` (Part 6) |
| **A-13** | Phase 1 | `feat(db): add ALTER and DROP demonstration script` | `db/02_alter_demo.sql` |
| **A-14** | Phase 1 | `docs: add entity-relationship diagram and entity descriptions` | `docs/er_diagram.md` |
| **A-15** | Phase 2 | `feat(db): implement sp_generate_run_inventory procedure` | `db/03_procedures.sql` (Part 1) |
| **A-16** | Phase 2 | `feat(db): implement fn_calc_fare dynamic pricing function` | `db/03_procedures.sql` (Part 2) |
| **A-17** | Phase 2 | `feat(db): implement sp_search_trains route matching procedure` | `db/03_procedures.sql` (Part 3) |
| **A-18** | Phase 2 | `feat(db): implement sp_book_tickets high-concurrency booking engine` | `db/03_procedures.sql` (Part 4) |
| **A-19** | Phase 2 | `feat(db): implement sp_confirm_payment and sp_cancel_booking` | `db/03_procedures.sql` (Part 5) |
| **A-20** | Phase 2 | `feat(db): implement sp_release_expired_holds procedure` | `db/03_procedures.sql` (Part 6) |
| **A-21** | Phase 2 | `feat(db): add audit and integrity triggers` | `db/04_triggers.sql` |
| **A-22** | Phase 2 | `feat(db): add views for availability, revenue, and routes` | `db/05_views.sql` |
| **A-23** | Phase 2 | `feat(db): add recurring MySQL event for hold release` | `db/06_events.sql` |
| **A-24** | Phase 2 | `docs: add relational schema and 3NF/BCNF normalization proof` | `docs/relational_schema.md` |
| **A-25** | Phase 3 | `feat(backend): scaffold Django project settings with PyMySQL` | `backend/tatkal_core/*`, `backend/manage.py`, `backend/requirements.txt` |
| **A-26** | Phase 3 | `feat(backend): add unmanaged Django models mapping to MySQL tables` | `backend/booking_engine/models.py` |
| **A-27** | Phase 3 | `feat(backend): add init_db management command for automated DDL execution` | `backend/booking_engine/management/commands/init_db.py` |
| **A-28** | Phase 3 | `feat(backend): add JWT authentication and role-based permissions` | `backend/booking_engine/auth_views.py`, `backend/booking_engine/permissions.py` |
| **A-29** | Phase 3 | `feat(backend): add stations and train search endpoints` | `backend/booking_engine/train_views.py` |
| **A-30** | Phase 3 | `feat(backend): add seat map and Tatkal status calculation endpoints` | `backend/booking_engine/seat_views.py` |
| **A-31** | Phase 3 | `feat(backend): implement booking endpoint with procedure call and throttling` | `backend/booking_engine/booking_views.py` |
| **A-32** | Phase 3 | `feat(backend): implement payment and cancellation endpoints with deadlock retry`| `backend/booking_engine/payment_views.py` |
| **A-33** | Phase 3 | `feat(backend): implement admin management and revenue reporting endpoints` | `backend/booking_engine/admin_views.py` |
| **A-34** | Phase 3 | `feat(chroma): add persistent ChromaDB query client and search wrapper` | `chroma_svc/__init__.py`, `chroma_svc/client.py`, `chroma_svc/search.py` |
| **A-35** | Phase 3 | `feat(backend): wire vector search endpoints for trains and policy FAQs` | `backend/booking_engine/search_views.py` |
| **A-36** | Phase 4 | `test(backend): add unit test fixtures and model tests` | `backend/tests/conftest.py`, `backend/tests/test_models.py` |
| **A-37** | Phase 4 | `test(backend): add auth, search, and booking API tests` | `backend/tests/test_api.py` |
| **A-38** | Phase 4 | `test(backend): implement multi-threaded booking concurrency stress test` | `backend/tests/test_concurrency.py` |
| **A-39** | Phase 4 | `docs: add EXPLAIN index performance analysis demonstration` | `db/08_explain_demo.sql` |
| **A-40** | Phase 4 | `docs: add comprehensive SQL query suite with window functions` | `db/07_queries.sql`, `docs/important_queries.md` |
| **A-41** | Phase 4 | `docs: document transaction isolation levels and SKIP LOCKED mechanics` | `db/09_isolation_demo.md` |
| **A-42** | Phase 5 | `docs: add database architecture, data dictionary, and dual-DB justification`| `docs/data_dictionary.md`, `docs/db_choice_justification.md`, `docs/sql_vector_implementation.md`, `docs/system_architecture.md` |

---

## 2. PERSON B: Planned Progressive Commit Sequence (for Handoff)

Person B receives their files in `handoff/person_b/` and commits them to `origin/main` under their own git identity (`Jashruth K A`).

| Commit # | Phase | Planned Commit Message | Staged Files |
| :--- | :--- | :--- | :--- |
| **B-01** | Phase 0 | `chore(frontend): initialize MSW mock API handlers and browser worker` | `frontend/mocks/handlers.ts`, `frontend/mocks/browser.ts`, `frontend/mocks/server.ts` |
| **B-02** | Phase 1 | `feat(frontend): scaffold Next.js App Router application with Tailwind CSS` | `frontend/package.json`, `frontend/package-lock.json`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`, `frontend/postcss.config.js`, `frontend/src/app/globals.css` |
| **B-03** | Phase 1 | `feat(frontend): add root layout, navigation header, and notification toasts` | `frontend/src/app/layout.tsx`, `frontend/src/components/Navbar.tsx`, `frontend/src/components/Footer.tsx`, `frontend/src/components/Toast.tsx` |
| **B-04** | Phase 1 | `feat(frontend): add typed API client with JWT token refresh management` | `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts` |
| **B-05** | Phase 1 | `feat(frontend): build user login and registration pages with form validation` | `frontend/src/app/login/page.tsx`, `frontend/src/app/register/page.tsx` |
| **B-06** | Phase 2 | `feat(frontend): build home page with autocomplete and semantic search box` | `frontend/src/app/page.tsx`, `frontend/src/components/StationAutocomplete.tsx` |
| **B-07** | Phase 2 | `feat(frontend): build train search results page with class filters and sorting`| `frontend/src/app/search/page.tsx`, `frontend/src/components/TrainCard.tsx` |
| **B-08** | Phase 2 | `feat(frontend): build train detail page with route timeline and stop halts` | `frontend/src/app/trains/[id]/page.tsx`, `frontend/src/components/RouteTimeline.tsx` |
| **B-09** | Phase 2 | `feat(seed): build realistic database generator for stations, trains, and runs` | `scripts/seed.py` |
| **B-10** | Phase 2 | `feat(chroma): implement vector corpus generator and sentence-transformers ingestion`| `scripts/ingest_chroma.py` |
| **B-11** | Phase 3 | `feat(frontend): build Tatkal booking page with countdown and dynamic passenger form`| `frontend/src/app/book/[runId]/page.tsx`, `frontend/src/components/TatkalCountdown.tsx` |
| **B-12** | Phase 3 | `feat(frontend): build interactive coach seat map preview` | `frontend/src/components/SeatMap.tsx` |
| **B-13** | Phase 3 | `feat(frontend): build payment simulation page with hold countdown and idempotent retry`| `frontend/src/app/pay/[pnr]/page.tsx` |
| **B-14** | Phase 3 | `feat(frontend): build customer bookings list and ticket view with cancellation`| `frontend/src/app/bookings/page.tsx`, `frontend/src/app/bookings/[pnr]/page.tsx` |
| **B-15** | Phase 3 | `feat(frontend): build semantic FAQ and railway policies knowledge base page` | `frontend/src/app/help/page.tsx` |
| **B-16** | Phase 3 | `feat(frontend): build admin analytics dashboard with revenue and demand charts`| `frontend/src/app/admin/page.tsx`, `frontend/src/app/admin/trains/page.tsx`, `frontend/src/app/admin/runs/page.tsx`, `frontend/src/app/admin/audit-log/page.tsx` |
| **B-17** | Phase 4 | `test(load): implement Locust Tatkal booking load test for 300-500 concurrent users`| `scripts/locustfile.py` |
| **B-18** | Phase 4 | `test(e2e): add Playwright end-to-end integration test suite` | `frontend/tests/e2e.spec.ts`, `frontend/playwright.config.ts` |
| **B-19** | Phase 4 | `feat(ops): create cross-platform setup and development run scripts` | `scripts/setup.ps1`, `scripts/setup.sh`, `scripts/dev.ps1`, `scripts/dev.sh` |
| **B-20** | Phase 4 | `feat(demo): create live demo automation scripts for concurrency, window, and expiry`| `scripts/demo_reset.ps1`, `scripts/demo_reset.sh`, `scripts/demo_concurrency.ps1`, `scripts/demo_concurrency.sh`, `scripts/demo_tatkal_window.ps1`, `scripts/demo_tatkal_window.sh`, `scripts/demo_expiry.ps1`, `scripts/demo_expiry.sh` |
| **B-21** | Phase 4 | `feat(demo): create preflight verification script for live presentation readiness`| `scripts/preflight.ps1`, `scripts/preflight.sh` |
| **B-22** | Phase 5 | `docs: add problem statement, objectives, scope, and functional requirements`| `docs/problem_statement.md`, `docs/objectives.md`, `docs/scope.md`, `docs/functional_requirements.md` |
| **B-23** | Phase 5 | `docs: document testing results, load test report, and future enhancements` | `docs/testing_results.md`, `docs/conclusion_future_work.md`, `docs/screenshots.md` |
| **B-24** | Phase 5 | `docs: add presentation demo script and comprehensive project README` | `docs/DEMO_SCRIPT.md`, `README.md` |
