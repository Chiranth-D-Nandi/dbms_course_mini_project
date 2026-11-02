<!-- Owner: Person B -->
# Functional Requirements Specification (FRS)

## 1. User Authentication & Authorization (FR-01 to FR-04)
- **FR-01: User Registration**: System shall allow new users to register with name, email, phone, password, and designated role (`CUSTOMER` or `ADMIN`).
- **FR-02: Secure Password Storage**: All passwords shall be salted and hashed using PBKDF2-HMAC-SHA256 prior to storage.
- **FR-03: JWT Session Management**: System shall issue short-lived JWT access tokens (2 hours) and long-lived refresh tokens (7 days) for session continuity.
- **FR-04: Role-Based Access Control**: System shall restrict administrative endpoints (`/api/admin/*`) exclusively to authenticated users possessing the `ADMIN` role.

## 2. Train Search & Timetable Exploration (FR-05 to FR-08)
- **FR-05: Station Autocomplete**: System shall provide real-time search of stations by code, city, or name using MySQL `FULLTEXT` natural language matching.
- **FR-06: Direct Route Matching**: System shall locate all active trains traveling from source station to destination station on a given date where `source.stop_sequence < destination.stop_sequence`.
- **FR-07: Seat Availability Aggregation**: System shall compute real-time available seat counts for each train across travel classes and quotas.
- **FR-08: Timetable Inspection**: System shall display intermediate halts, arrival/departure times, stoppage durations, and distances.

## 3. High-Concurrency Booking & Hold Management (FR-09 to FR-13)
- **FR-09: Tatkal Window Enforcement**: System shall compute Tatkal opening status and enforce opening times (10:00 AM for AC, 11:00 AM for Non-AC, 1 day prior to departure).
- **FR-10: Atomic Seat Hold**: When a booking request is submitted, system shall atomically select and lock candidate seats using `SELECT ... FOR UPDATE SKIP LOCKED` and place them on `HOLD`.
- **FR-11: Hold Countdown**: System shall assign an 8-minute expiration deadline (`expires_at`) to held seats, rendering a live countdown timer in the user interface.
- **FR-12: Zero Double-Booking**: Under concurrent requests, system shall never assign the same physical seat to more than one active booking.
- **FR-13: Automated Hold Release**: Background event `ev_release_expired_holds` running every 30 seconds shall transition unconfirmed holds past `expires_at` to `EXPIRED` and restore seat availability.

## 4. Payment & Idempotency (FR-14 to FR-16)
- **FR-14: Payment Idempotency**: System shall require an `Idempotency-Key` on payment confirmation. Duplicate submissions with identical keys shall return existing confirmation without duplicate debit.
- **FR-15: Ticket Confirmation**: Upon payment success within 8 minutes, system shall transition booking status to `CONFIRMED` and seat status to `BOOKED`.
- **FR-16: Rejection of Expired Holds**: Payment confirmation submitted after hold expiration shall be rejected with an appropriate error.

## 5. Cancellation & Refunds (FR-17 to FR-18)
- **FR-17: Graded Refund Calculation**: System shall calculate cancellation penalties according to departure proximity tiers (>48 hrs, 48-12 hrs, 12-4 hrs, <4 hrs).
- **FR-18: Tatkal No-Refund Rule**: System shall withhold 100% of ticket fare for cancellations of confirmed Tatkal tickets.

## 6. Cognitive Semantic Search (FR-19 to FR-20)
- **FR-19: Semantic Train Discovery**: System shall accept natural language queries (e.g. *"fast night express to Chennai"*) and return relevant trains ranked by ChromaDB cosine similarity.
- **FR-20: Policy & FAQ Retrieval**: System shall match passenger questions against embedded railway regulations and display answers with similarity scores.

## 7. Administrative Reporting & Auditing (FR-21 to FR-23)
- **FR-21: Revenue Analytics**: Administrators shall have access to financial summaries and net revenue breakdowns via view `v_admin_revenue`.
- **FR-22: Audit Trail Inspection**: System shall maintain automated trigger-driven logs of all mutations on bookings and seats, viewable by administrators.
- **FR-23: Inventory Scheduling**: Administrators shall have the capability to schedule new train runs and generate inventories via stored procedure.
