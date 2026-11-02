<!-- Owner: Person A -->
# Relational Schema & Normalization Analysis (3NF / BCNF)

## 1. Visual Relational Schema Diagram (Elmasri & Navathe Style)

Below is the formal **Relational Database Schema Diagram with Referential Integrity Constraints** following the standard Elmasri & Navathe textbook convention. 
- Relations are depicted as rectangular blocks with attribute cells.
- **Primary key** attributes have a solid underline (composite primary keys have all component attributes underlined).
- Directed arrows originate from the **foreign key** attributes and point directly to the referenced **primary key** attributes.

![Relational Database Schema Diagram](relational_schema_diagram.svg)

---

## 2. Relational Schema Representation

Notation:
- **`TABLE_NAME`** (`Primary_Key`, Non_Key_Attributes, `Foreign_Key*`)
- Primary keys are underlined or designated by `(PK)`
- Foreign keys are designated by `(FK -> Referenced_Table.Column)`
- Unique alternate keys are designated by `(UK)`

```
1.  app_user (user_id [PK], first_name, last_name, email [UK], phone [UK], password_hash, role, is_active, created_at)
2.  station (station_id [PK], station_code [UK], station_name, city, state)
3.  train (train_id [PK], train_number [UK], train_name, train_type, is_active)
4.  train_running_day (train_id [PK, FK -> train.train_id], day_of_week [PK])
5.  seat_class (class_code [PK], class_name, is_ac, fare_per_km, tatkal_open_time, tatkal_quota_pct, tatkal_surcharge_pct, tatkal_min_charge, tatkal_max_charge)
6.  coach (coach_id [PK], train_id [FK -> train.train_id], class_code [FK -> seat_class.class_code], coach_number, UK(train_id, coach_number))
7.  seat (seat_id [PK], coach_id [FK -> coach.coach_id], seat_number, berth_type, UK(coach_id, seat_number))
8.  train_run (run_id [PK], train_id [FK -> train.train_id], journey_date, run_status, UK(train_id, journey_date))
9.  train_stop (train_id [PK, FK -> train.train_id], stop_seq [PK], station_id [FK -> station.station_id], arrival_time, departure_time, day_offset, distance_km, UK(train_id, station_id))
10. booking (pnr [PK], user_id [FK -> app_user.user_id], run_id [FK -> train_run.run_id], source_station_id [FK -> station.station_id], dest_station_id [FK -> station.station_id], class_code [FK -> seat_class.class_code], booking_type, status, booking_time, expires_at, total_fare)
11. run_seat (run_id [PK, FK -> train_run.run_id], seat_id [PK, FK -> seat.seat_id], quota_type, seat_status, hold_expires_at, held_by_pnr [FK -> booking.pnr], version_no)
12. passenger (pnr [PK, FK -> booking.pnr], passenger_seq [PK], name, dob, gender, id_proof_type, id_proof_no, fare_amount, status, run_id [FK -> run_seat.run_id], seat_id [FK -> run_seat.seat_id], UK(run_id, seat_id))
13. payment (payment_id [PK], pnr [FK -> booking.pnr], amount, method, status, txn_ref [UK], idempotency_key [UK], created_at)
14. cancellation (cancellation_id [PK], pnr [PK, UK, FK -> booking.pnr], cancelled_at, refund_amount, reason)
15. audit_log (log_id [PK], table_name, record_id, action, old_value, new_value, changed_at)
```

---

## 2. Mapping Rules from Conceptual ER to Relational Schema

1. **Strong Entities to Relations**:
   - Each strong entity (`app_user`, `station`, `train`, `seat_class`) maps directly to a relation. Simple attributes become columns; candidate keys become `PRIMARY KEY` or `UNIQUE` constraints.
2. **Weak Entities to Relations**:
   - Weak entities (`train_stop`, `run_seat`, `passenger`) include the primary key of their identifying owner entity as a foreign key that forms part of their composite primary key:
     - `train_stop`: PK is (`train_id`, `stop_seq`)
     - `run_seat`: PK is (`run_id`, `seat_id`)
     - `passenger`: PK is (`pnr`, `passenger_seq`)
   - Referential integrity is preserved via `ON DELETE CASCADE`.
3. **Multivalued Attribute De-nesting**:
   - The multivalued attribute `running_days` of entity `train` is mapped into a separate relation `train_running_day` with composite PK (`train_id`, `day_of_week`). This satisfies First Normal Form (1NF).
4. **1:N Binary Relationships**:
   - Mapped by placing the primary key of the "1" side as a foreign key on the "N" side (e.g., `coach` contains `train_id` FK; `booking` contains `user_id` and `run_id` FKs).
5. **1:1 Optional Binary Relationships**:
   - `cancellation` has a 1:1 relationship with `booking`. Mapped with `pnr` as a foreign key with a `UNIQUE` constraint, preventing multiple cancellations per ticket.

---

## 3. Formal Normalization Proof (1NF -> 2NF -> 3NF -> BCNF)

A relation is in **Boyce-Codd Normal Form (BCNF)** if for every non-trivial functional dependency $X \rightarrow Y$, the determinant $X$ is a superkey.

### 3.1 Relation `app_user`
- **Candidate Keys**: `{user_id}`, `{email}`, `{phone}`
- **Functional Dependencies**:
  - $FD_1$: `user_id` $\rightarrow$ `first_name`, `last_name`, `email`, `phone`, `password_hash`, `role`, `is_active`, `created_at`
  - $FD_2$: `email` $\rightarrow$ `user_id`, `first_name`, `last_name`, `phone`, `password_hash`, `role`, `is_active`, `created_at`
  - $FD_3$: `phone` $\rightarrow$ `user_id`, `first_name`, `last_name`, `email`, `password_hash`, `role`, `is_active`, `created_at`
- **Proof**:
  - **1NF**: All attributes are atomic scalars.
  - **2NF**: No partial dependencies; all determinants are single-attribute candidate keys.
  - **3NF**: No transitive dependencies between non-prime attributes.
  - **BCNF**: In all $FD_1, FD_2, FD_3$, the left-hand side is a superkey. **Satisfies BCNF.**

### 3.2 Relation `station`
- **Candidate Keys**: `{station_id}`, `{station_code}`
- **Functional Dependencies**:
  - $FD_1$: `station_id` $\rightarrow$ `station_code`, `station_name`, `city`, `state`
  - $FD_2$: `station_code` $\rightarrow$ `station_id`, `station_name`, `city`, `state`
- **Proof**: Determinants are superkeys. **Satisfies BCNF.**

### 3.3 Relation `train`
- **Candidate Keys**: `{train_id}`, `{train_number}`
- **Functional Dependencies**:
  - $FD_1$: `train_id` $\rightarrow$ `train_number`, `train_name`, `train_type`, `is_active`
  - $FD_2$: `train_number` $\rightarrow$ `train_id`, `train_name`, `train_type`, `is_active`
- **Proof**: `total_coaches` was intentionally excluded and computed in a view to prevent transitive dependency $train\_id \rightarrow coaches \rightarrow total\_coaches$. Determinants are superkeys. **Satisfies BCNF.**

### 3.4 Relation `train_running_day`
- **Candidate Key**: `{train_id, day_of_week}`
- **Functional Dependencies**: None (all attributes are part of the composite primary key).
- **Proof**: Trivially satisfies BCNF.

### 3.5 Relation `seat_class`
- **Candidate Key**: `{class_code}`
- **Functional Dependencies**:
  - $FD_1$: `class_code` $\rightarrow$ `class_name`, `is_ac`, `fare_per_km`, `tatkal_open_time`, `tatkal_quota_pct`, `tatkal_surcharge_pct`, `tatkal_min_charge`, `tatkal_max_charge`
- **Proof**: Determinant is candidate key. **Satisfies BCNF.**

### 3.6 Relation `coach`
- **Candidate Keys**: `{coach_id}`, `{train_id, coach_number}`
- **Functional Dependencies**:
  - $FD_1$: `coach_id` $\rightarrow$ `train_id`, `class_code`, `coach_number`
  - $FD_2$: `{train_id, coach_number}` $\rightarrow$ `coach_id`, `class_code`
- **Proof**: Determinants are candidate keys. **Satisfies BCNF.**

### 3.7 Relation `seat`
- **Candidate Keys**: `{seat_id}`, `{coach_id, seat_number}`
- **Functional Dependencies**:
  - $FD_1$: `seat_id` $\rightarrow$ `coach_id`, `seat_number`, `berth_type`
  - $FD_2$: `{coach_id, seat_number}` $\rightarrow$ `seat_id`, `berth_type`
- **Proof**: Determinants are candidate keys. **Satisfies BCNF.**

### 3.8 Relation `train_run`
- **Candidate Keys**: `{run_id}`, `{train_id, journey_date}`
- **Functional Dependencies**:
  - $FD_1$: `run_id` $\rightarrow$ `train_id`, `journey_date`, `run_status`
  - $FD_2$: `{train_id, journey_date}` $\rightarrow$ `run_id`, `run_status`
- **Proof**: Determinants are candidate keys. **Satisfies BCNF.**

### 3.9 Relation `train_stop`
- **Candidate Keys**: `{train_id, stop_seq}`, `{train_id, station_id}`
- **Functional Dependencies**:
  - $FD_1$: `{train_id, stop_seq}` $\rightarrow$ `station_id`, `arrival_time`, `departure_time`, `day_offset`, `distance_km`
  - $FD_2$: `{train_id, station_id}` $\rightarrow$ `stop_seq`, `arrival_time`, `departure_time`, `day_offset`, `distance_km`
- **Proof**: Both `{train_id, stop_seq}` and `{train_id, station_id}` are superkeys. Derived attribute `halt_duration` was omitted from storage to avoid transitive functional dependency `{arrival_time, departure_time}` $\rightarrow$ `halt_duration`. **Satisfies BCNF.**

### 3.10 Relation `run_seat` (Concurrency Table)
- **Candidate Key**: `{run_id, seat_id}`
- **Functional Dependencies**:
  - $FD_1$: `{run_id, seat_id}` $\rightarrow$ `quota_type`, `seat_status`, `hold_expires_at`, `held_by_pnr`, `version_no`
- **Proof**: Determinant is primary key. **Satisfies BCNF.**

### 3.11 Relation `booking`
- **Candidate Key**: `{pnr}`
- **Functional Dependencies**:
  - $FD_1$: `pnr` $\rightarrow$ `user_id`, `run_id`, `source_station_id`, `dest_station_id`, `class_code`, `booking_type`, `status`, `booking_time`, `expires_at`, `total_fare`
- **Proof**: Determinant is primary key. **Satisfies BCNF.**

### 3.12 Relation `passenger`
- **Candidate Keys**: `{pnr, passenger_seq}`, `{run_id, seat_id}` (when allocated)
- **Functional Dependencies**:
  - $FD_1$: `{pnr, passenger_seq}` $\rightarrow$ `name`, `dob`, `gender`, `id_proof_type`, `id_proof_no`, `fare_amount`, `status`, `run_id`, `seat_id`
  - $FD_2$: `{run_id, seat_id}` $\rightarrow$ `pnr`, `passenger_seq`, `name`, `dob`, `gender`, `id_proof_type`, `id_proof_no`, `fare_amount`, `status`
- **Proof**: Derived attribute `age` is calculated on demand in `v_passenger_age` from `dob` rather than stored, eliminating transitive dependency $dob \rightarrow age$. Determinants are candidate keys. **Satisfies BCNF.**

### 3.13 Relation `payment`
- **Candidate Keys**: `{payment_id}`, `{txn_ref}`, `{idempotency_key}`
- **Functional Dependencies**:
  - $FD_1$: `payment_id` $\rightarrow$ `pnr`, `amount`, `method`, `status`, `txn_ref`, `idempotency_key`, `created_at`
  - $FD_2$: `txn_ref` $\rightarrow$ `payment_id`, `pnr`, `amount`, `method`, `status`, `idempotency_key`, `created_at`
  - $FD_3$: `idempotency_key` $\rightarrow$ `payment_id`, `pnr`, `amount`, `method`, `status`, `txn_ref`, `created_at`
- **Proof**: All determinants are superkeys. **Satisfies BCNF.**

### 3.14 Relation `cancellation`
- **Candidate Keys**: `{cancellation_id}`, `{pnr}`
- **Functional Dependencies**:
  - $FD_1$: `cancellation_id` $\rightarrow$ `pnr`, `cancelled_at`, `refund_amount`, `reason`
  - $FD_2$: `pnr` $\rightarrow$ `cancellation_id`, `cancelled_at`, `refund_amount`, `reason`
- **Proof**: Determinants are superkeys. **Satisfies BCNF.**

### 3.15 Relation `audit_log`
- **Candidate Key**: `{log_id}`
- **Functional Dependencies**:
  - $FD_1$: `log_id` $\rightarrow$ `table_name`, `record_id`, `action`, `old_value`, `new_value`, `changed_at`
- **Proof**: Determinant is primary key. **Satisfies BCNF.**

---

## 4. Summary of Normalization Achievement
Every relation in the Tatkal High-Concurrency Reservation Engine strictly satisfies **Boyce-Codd Normal Form (BCNF)**:
1. Zero repeating groups or non-atomic fields (1NF).
2. Zero partial key dependencies on composite candidate keys (2NF).
3. Zero transitive functional dependencies among non-prime attributes (3NF).
4. Every determinant in every non-trivial functional dependency is a superkey (BCNF).
5. All calculated quantities (`total_coaches`, `halt_duration`, `age`, `available_seats`, `net_revenue`) are derived exclusively via relational views and functions, preventing update, insertion, and deletion anomalies.
