<!-- Owner: Person A -->
# SQL & Vector DB Implementation Deep Dive

This technical document details the implementation of database-layer business logic in MySQL 8.0 (stored procedures, triggers, views, events) and semantic retrieval in ChromaDB.

---

## 1. Stored Procedures & Functions (`db/03_procedures.sql`)

Rather than executing multi-step business logic in the Python API layer with frequent network hops, critical ticketing workflows are encapsulated in compiled MySQL stored procedures.

### 1.1 `sp_generate_run_inventory(p_run_id INT)`
- **Purpose**: Populates the `run_seat` concurrency inventory whenever a new train journey date is scheduled.
- **Implementation**:
  - Traverses coaches attached to the train.
  - Queries base seats from table `seat`.
  - Allocates quota distribution: 80% to `GENERAL` quota, 20% to `TATKAL` quota (alternating by modulo 5 on seat number).
  - Inserts all rows with initial `status = 'AVAILABLE'` and `version = 0`.
  - Idempotent via `INSERT IGNORE`.

### 1.2 `fn_calc_fare(p_run_id, p_source_id, p_dest_id, p_class_code, p_booking_type)`
- **Purpose**: Deterministic, pure SQL stored function computing dynamic ticket pricing.
- **Mathematical Formula**:
  $$\text{Distance} = \text{Stop}_{\text{dest}}.\text{distance\_from\_source} - \text{Stop}_{\text{src}}.\text{distance\_from\_source}$$
  $$\text{Base Fare} = \text{Distance} \times \text{seat\_class}.\text{base\_fare\_per\_km}$$
  If `p_booking_type = 'TATKAL'`:
  $$\text{Raw Surcharge} = \text{Base Fare} \times \frac{\text{tatkal\_charge\_pct}}{100}$$
  $$\text{Surcharge} = \min(\max(\text{Raw Surcharge}, \text{tatkal\_min\_charge}), \text{tatkal\_max\_charge})$$
  $$\text{Total Seat Fare} = \text{Base Fare} + \text{Surcharge}$$

### 1.3 `sp_search_trains(p_source_id, p_dest_id, p_journey_date, p_class_code, p_quota)`
- **Purpose**: High-speed timetable lookup and real-time seat availability aggregation.
- **Implementation**:
  - Performs self-join on `train_stop` (`ts1` for source, `ts2` for destination).
  - Enforces `ts1.stop_sequence < ts2.stop_sequence` ensuring trains travel in the correct forward direction.
  - Joins `train_running_day` matching `DAYNAME(p_journey_date)`.
  - Aggregates available seats from `run_seat` where `status = 'AVAILABLE'` or hold has expired.

### 1.4 `sp_book_tickets(...)` — Concurrency Engine
- **Purpose**: Reserves 1 to 6 seats atomically without race conditions or double-bookings.
- **Concurrency Mechanism**:
  ```sql
  SELECT rs.run_seat_id, rs.seat_id
  FROM run_seat rs
  JOIN seat s ON rs.seat_id = s.seat_id
  JOIN coach c ON s.coach_id = c.coach_id
  WHERE rs.run_id = p_run_id
    AND rs.quota = p_booking_type
    AND (rs.status = 'AVAILABLE' OR (rs.status = 'HELD' AND rs.held_until < NOW()))
    AND c.class_code = p_class_code
  LIMIT v_req_seats
  FOR UPDATE SKIP LOCKED;
  ```
  - `FOR UPDATE`: Obtains exclusive record locks on selected candidate rows.
  - `SKIP LOCKED`: Skips rows currently locked by concurrent threads, eliminating lock wait queues.
  - Generates 10-digit PNR using pseudo-random digits and timestamp seed.
  - Inserts booking with `status = 'HOLD'`, `expires_at = NOW() + INTERVAL 8 MINUTE`.
  - Updates `run_seat` to `'HELD'` and links `held_by_booking_id`.
  - Inserts individual passenger records.

### 1.5 `sp_confirm_payment(p_booking_id, p_idempotency_key, p_payment_method, ...)`
- **Purpose**: Finalizes confirmed ticket upon successful payment gateway callback.
- **Idempotency Protection**:
  - Checks if `p_idempotency_key` already exists in `payment` table. If found, returns existing `SUCCESS` without double-booking.
  - Validates that booking is currently in `'HOLD'` state and `expires_at >= NOW()`.
  - Transitions `booking.status` to `'CONFIRMED'`.
  - Transitions all held `run_seat.status` from `'HELD'` to `'BOOKED'`.

### 1.6 `sp_cancel_booking(p_booking_id, p_reason, ...)`
- **Purpose**: Processes customer ticket cancellations according to Indian Railway refund rules.
- **Refund Slabs**:
  - $\Delta t > 48\text{ hrs}$: Flat clerkage fee per passenger (e.g. Rs 180 for 3A).
  - $12\text{ hrs} < \Delta t \le 48\text{ hrs}$: 25% cancellation charge.
  - $4\text{ hrs} < \Delta t \le 12\text{ hrs}$: 50% cancellation charge.
  - $\Delta t \le 4\text{ hrs}$: 100% cancellation charge (0% refund).
  - Tatkal tickets: 0% refund per IRCTC rules.
  - Releases `run_seat.status` back to `'AVAILABLE'` and clears `held_by_booking_id`.

---

## 2. Integrity & Audit Triggers (`db/04_triggers.sql`)

Database triggers enforce data integrity and populate immutable audit trails automatically.

1. **`trg_booking_status_audit`**: Fires `AFTER UPDATE ON booking`. When `status` changes, writes JSON snapshots of old and new status to `audit_log`.
2. **`trg_run_seat_audit`**: Fires `AFTER UPDATE ON run_seat`. Records seat transitions (`AVAILABLE` $\to$ `HELD` $\to$ `BOOKED`).
3. **`trg_booking_route_check`**: Fires `BEFORE INSERT ON booking`. Verifies that source and destination belong to the train's route and source sequence precedes destination sequence.
4. **`trg_passenger_validate`**: Fires `BEFORE INSERT ON passenger`. Enforces age boundaries ($1 \le \text{age} \le 120$) and ID card length.
5. **`trg_prevent_booked_seat_delete`**: Fires `BEFORE DELETE ON run_seat`. Rejects deletion of any seat whose status is `'BOOKED'`.

---

## 3. Recurring Event Scheduler (`db/06_events.sql`)

- **Event**: `ev_release_expired_holds`
- **Schedule**: `EVERY 30 SECOND`
- **Body**: Executes `CALL sp_release_expired_holds(@v_count);`
- **Action**: Sweeps all bookings where `status = 'HOLD'` and `expires_at < NOW()`, marks them `'EXPIRED'`, and transitions associated `run_seat` rows back to `'AVAILABLE'`.

---

## 4. ChromaDB Vector Architecture (`chroma_svc/`)

```
 [ Query: "overnight sleeper train to Chennai" ]
                       |
                       v
         [ sentence-transformers model ]
              (all-MiniLM-L6-v2)
                       |
                       v
            [ 384-dimensional Vector ]
                       |
                       v
       [ ChromaDB HNSW Index: Cosine Space ]
           /                               \
          v                                 v
   Collection: `train_info`        Collection: `policy_faq`
   - Train metadata & routes       - Cancellation slabs & rules
   - Match score: 0.912            - Match score: 0.884
```

- **Persistence**: ChromaDB persistent client stores indexed vector data in `./chroma_data`.
- **Model Cache**: `all-MiniLM-L6-v2` weights stored locally in `./models/all-MiniLM-L6-v2`.
- **Distance Metric**: Cosine distance ($d = 1 - \cos(\theta)$), converted to similarity score:
  $$\text{Similarity} = \max(0, 1 - \text{distance})$$
- **Filtering**: Supports metadata filtering via `where={"category": category}` on FAQ queries.
