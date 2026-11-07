# API contract

Base URL: `http://127.0.0.1:8000/api`. Send JSON request bodies; protected endpoints use `Authorization: Bearer <access>`. The accompanying YAML file defines the OpenAPI contract.

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/auth/register` | Create a customer account |
| POST | `/auth/login` | Log in and receive access/refresh tokens |
| POST | `/auth/refresh` | Refresh a session for an active account |
| GET | `/auth/me` | Read the authenticated user |
| GET | `/stations/` | Search station code/name/city with q |
| GET | `/trains/` | List active train catalog |
| GET | `/trains/search/` | Search source/dest station code or ID and run date |
| GET | `/trains/{id}/` | Read timetable, running days and coach count |
| GET | `/runs/{run_id}/seats/` | Read coach seat map by class and quota |
| GET | `/tatkal/status/` | Read opening status by run_id and class |
| POST | `/bookings/` | Atomically reserve seats for eight minutes |
| GET | `/bookings/my/` | List the authenticated user bookings |
| GET | `/bookings/{pnr}/` | Read owned booking or admin-accessible booking |
| POST | `/bookings/{pnr}/cancel/` | Cancel confirmed owned ticket or admin-accessible ticket |
| POST | `/payments/confirm/` | Confirm a simulated payment with idempotency protection |
| GET | `/search/trains/` | Semantic train search using q |
| GET | `/search/faq/` | Semantic project-policy search using q and optional category |
| GET | `/admin/revenue/` | ADMIN: revenue summary and per-run rows |
| GET | `/admin/audit-logs/` | ADMIN: latest trigger logs; filter entity/action |
| GET | `/admin/reports/{metric}/` | ADMIN: occupancy or tatkal-demand |
| POST | `/admin/runs/` | ADMIN: create a dated run and inventory |
| POST | `/admin/release-holds/` | ADMIN: run the expiry sweep |

## Response shapes

- Auth registration/login: `{user, tokens: {access, refresh}}`; refresh: `{access, refresh}`; profile: `{user}`.
- Stations and catalog: arrays. Route search: `{source, destination, journey_date, quota, count, trains}` with one flat row per run/class. The frontend adapter groups class availability per train.
- Seat map: `{run_id, train_number, train_name, journey_date, tatkal_info, coaches: [{coach_id, coach_code, class_code, seats: [...]}]}`.
- Booking creation: `{message, booking: {pnr, status: "HOLD", total_fare, expires_at, passengers, ...}}`. Database/list/detail status for this state is `PENDING`.
- Booking list: array. Detail: `{pnr, status, source, destination, passengers, payments, cancellation, ...}`. PNRs in backend responses are stringified where appropriate; clients must not assume every endpoint uses identical projections.
- Payment: `{message, booking: {pnr, status}, payment: {payment_id, transaction_id, amount, payment_method, ...}}`. The server derives the amount from the booking. The idempotency key must be supplied in the header or body; conflicting request reuse is rejected.
- Cancellation: `{message, cancellation: {pnr, status, refund_amount, reason}}`.
- Semantic search: `{query, count, results}` (FAQ also includes category).
- Revenue: `{summary, revenue_data}`; audit/occupancy/demand: arrays; run creation and sweep return messages plus generated identifiers/counts.
- Expected failures use `{error: {code, message, details}}`. Booking refusals return 409; invalid payment/state requests return 400; unauthorized ownership returns 403.

## Implemented constraints

One to six passengers for General, one to four for Tatkal. Ages 1–120; supported IDs: Aadhaar, PAN, passport, voter ID. Public signup creates customers. Admin routes require ADMIN. Runs and booking departure validation use Indian local time. Payments/refunds are simulated; see README for the project refund tiers.
