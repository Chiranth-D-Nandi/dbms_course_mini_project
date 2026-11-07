# SQL and vector implementation

`db/01_schema.sql` defines 15 InnoDB relations with foreign keys, unique constraints, composite keys and checks. `db/02_alter_demo.sql` demonstrates an alteration and additional index. The Django unmanaged models map to this SQL-owned schema.

## Reservation transaction

`sp_book_tickets` validates the run, future boarding departure, passenger count and Tatkal opening. It calculates fares with `fn_calc_fare`, discovers physical candidate seat IDs with a consistent-read cursor and locks each candidate inventory row by `(run_id,seat_id)` using `FOR UPDATE SKIP LOCKED`. The point lookup avoids a sorted join locking rows that it does not ultimately allocate.

For sufficient seats it creates a `PENDING` booking, marks selected inventory `HELD`, inserts passengers, sets matching eight-minute deadlines and commits. Otherwise it rolls back the whole group. The unique `(run_id,seat_id)` on active passenger references adds a database constraint against duplicate assignment. The API retries signaled deadlocks with bounded backoff.

## Payment, cancellation and expiration

Payment locks the booking first. An idempotency key is bound to PNR, amount and method. Equivalent retries return the original payment; conflicting key reuse is rejected. The server uses the stored fare, verifies ownership and confirms only an unexpired pending booking. Payment is simulated.

Cancellation uses the project refund tiers documented in README. It clears passenger seat references and frees inventory in one transaction. Expiration similarly locks/updates bookings first, clears expired allocations and commits inventory release together. The native event calls this sweep every 30 seconds; the admin endpoint can invoke it manually.

Booking and inventory triggers write JSON audit changes. Other triggers validate routes, ages, passenger limits, payment amounts and booked-seat deletion. Reports aggregate receipts, refunds and seat counts separately before joining, avoiding fan-out errors.

## Search and roles

Station search uses a FULLTEXT index on `(station_name,city)` plus code/name/city prefixes. Route search joins source and destination stops with increasing `stop_seq`, run dates and running days. Views derive availability, ages, stop halts, booking summaries and revenue.

`app_rw` has application table write permissions and routine access. `app_ro` has table/view read permissions and can execute only the train-search procedure; it cannot invoke mutating DEFINER routines.

The Chroma ingestion script reads all 25 seeded train profiles/routes from MySQL and indexes 14 project-policy FAQs with local `all-MiniLM-L6-v2` embeddings. Model and index paths come from `.env`. The first setup downloads the model; later retrieval uses the cache. Cosine similarity ranks discovery results. Vector search is independent of booking correctness and is never used to allocate inventory.

See `testing_results.md` for observed tests and `db/09_isolation_demo.md` for a manual locking exercise.
