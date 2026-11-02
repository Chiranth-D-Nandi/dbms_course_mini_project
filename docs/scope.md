<!-- Owner: Person B -->
# System Scope & Boundaries

## 1. In-Scope Functional Areas

1. **Station & Train Network Management**:
   - 30 major Indian railway stations covering all major zones (Northern, Southern, Western, Eastern, South Western, etc.).
   - 25 realistic passenger trains spanning Rajdhani, Shatabdi, Superfast, and Mail categories with scheduled stops, cumulative distances, day offsets, and coach compositions.

2. **Multi-Class Dynamic Seating & Inventory Generation**:
   - 5 standard travel classes: Sleeper (SL), AC 3 Tier (3A), AC 2 Tier (2A), AC First Class (1A), and AC Chair Car (CC).
   - Dynamic inventory generation for 10 consecutive journey days per train via `sp_generate_run_inventory`.
   - Quota bifurcation: General (80%) and Tatkal (20%).

3. **High-Concurrency Tatkal Booking Engine**:
   - Real-time seat locking (`SELECT ... FOR UPDATE SKIP LOCKED`).
   - Strict Tatkal opening rules (10:00 AM for AC classes, 11:00 AM for Non-AC classes, 1 day in advance).
   - 8-minute seat hold timer with automated timeout release via MySQL event.
   - Idempotent payment processing via `Idempotency-Key` preventing duplicate charges.

4. **Ticket Cancellation & Graded Refunds**:
   - Railway refund rules enforcing tiered clerkage deductions based on departure proximity (>48 hrs, 48-12 hrs, 12-4 hrs, <4 hrs).
   - Zero refund policy on confirmed Tatkal cancellations.
   - Seat release back to available inventory.

5. **Semantic Information Retrieval**:
   - Natural language train query resolution via ChromaDB cosine similarity.
   - Policy and FAQ question answering across 35+ granular chunks.

6. **Administrative Analytics & Governance**:
   - Comprehensive revenue and occupancy reports via SQL view `v_admin_revenue`.
   - Immutable audit trail logging via database triggers and table `audit_log`.
   - Manual hold sweep and train run creation utilities.

---

## 2. Out-of-Scope (Deliberate Design Boundaries)

1. **Physical Banking Gateway Integration**:
   - Real credit card/UPI bank connections (Razorpay/Stripe live mode) are replaced with a realistic mock payment simulation engine enforcing idempotency and status transitions.
2. **Real-Time GPS Train Telemetry**:
   - Live GPS tracking of physical rolling stock is simulated via static scheduled arrival and departure timetables in `train_stop`.
3. **Multi-Leg Dynamic Transfers**:
   - Ticket reservations operate over single-train routes directly connecting boarding station to destination station along the train's scheduled itinerary.
