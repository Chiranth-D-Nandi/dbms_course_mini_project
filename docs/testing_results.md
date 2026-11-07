# Verification results

Verified locally on 6–7 November 2026 with Python 3.11, Django 5.2, MySQL 8.0.33, Next.js 14.2.35 and Chromium through Playwright. The original checkout's illustrative latency/load tables have been replaced by observed results.

| Check | Observed result |
| --- | --- |
| Django system check | No issues |
| Frontend TypeScript | Passed |
| Normal production build | Passed; includes booking, payment, ticket-detail and timetable routes |
| Browser end-to-end suite | 5 passed |
| Concurrency oversubscription | 16 simultaneous requests for 8 seats: 8 successful holds, 8 sold out, 0 duplicate assignments |
| Read-only SQL examples | All 11 SELECT/EXPLAIN demonstrations executed successfully |
| Schema documentation | Generated from the 15 actual database tables |
| Backend suite | 31 passed in 65.71 seconds; saved JUnit report |

## Backend coverage

API/model tests cover authentication, station/route search, timetable conversion, seat maps, booking/payment/cancellation, role restrictions and semantic retrieval. Regression tests cover rejected public-admin signup, account creation and token refresh, booking ownership, payment-key binding, equivalent retries, invalid PNRs, expired payment and inventory reuse, all four General refund tiers, Tatkal opening/passenger limit/zero refund, concurrent same-key payment, exact revenue totals, date-of-birth boundaries, admin scheduling and read-only routine restrictions.

Backend tests provision a unique disposable database, seed it, run the suite and delete that database. They do not reset the demo database. The final machine-readable report is [backend-tests.xml](artifacts/backend-tests.xml).

## Browser coverage

1. Customer login, dated search, timetable, two-passenger reservation, hold timer, simulated payment, confirmed ticket, cancellation and booking history.
2. Homepage station autocomplete and real catalog timetable lookup.
3. Semantic FAQ and train discovery with loaded timetable content.
4. Administrator reports, trigger audit log, future run/inventory creation, hold sweep and catalog.
5. Mobile layout with no horizontal page scrolling and unauthenticated booking redirect.

Actual captures are in [screenshots.md](screenshots.md). The browser test build uses `.next-e2e` on dedicated ports 3100/8100 so another application on port 3000 is not mistaken for this project. The normal build remains separate.

## Measured HTTP smoke test

The standard-library runner `scripts/load_smoke.py` completed a two-user, ten-second run against the local Django development server:

- 40 requests; 0 unexpected errors.
- Average response: 261.55 ms; p95: 360.22 ms; p99: 777.95 ms.
- Four successful holds, four confirmations, four equivalent payment retries and four cancellations, plus login, search and seat-map reads.

Raw results: [load-smoke.json](artifacts/load-smoke.json). This small run is a workflow smoke test, not a production capacity or latency guarantee. No 250-user/12,480-request benchmark is claimed.

Locust remains available as an optional script, but its native gevent DLL was blocked by Windows application control on this machine. The standard-library test above ran successfully without changing that policy.

## Reproduce

Run `.\scripts\verify.ps1`, or follow the individual commands in README. An existing MySQL administrator account is required for temporary test-schema provisioning. Seed and ingest first when setting up another machine. The first vector request in a fresh process can take longer while the model runtime loads.
