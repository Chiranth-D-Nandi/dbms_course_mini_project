<!-- Owner: Person A -->
# Relational Data Dictionary — Tatkal Railway Reservation System

This data dictionary formally defines all relational tables, views, columns, domains, integrity constraints, and foreign key dependencies in the `tatkal_db` MySQL 8.0 database.

---

## 1. Table: `app_user`
Stores registered users, administrative staff, and credential hashes.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `user_id` | `INT` | NO | PK | Auto Inc | Unique user surrogate identifier. |
| `first_name` | `VARCHAR(50)` | NO | - | None | Legal first name. |
| `last_name` | `VARCHAR(50)` | NO | - | None | Legal surname. |
| `email` | `VARCHAR(100)` | NO | UQ | None | Unique login email. Indexed via `idx_app_user_email`. |
| `phone` | `VARCHAR(15)` | NO | UQ | None | 10-15 digit contact number. Indexed. |
| `password_hash` | `VARCHAR(255)` | NO | - | None | PBKDF2-HMAC-SHA256 salted password hash. |
| `role` | `ENUM('ADMIN', 'CUSTOMER')` | NO | - | `'CUSTOMER'` | Role-based authorization boundary. |
| `is_active` | `BOOLEAN` | NO | - | `TRUE` | Soft account deactivation status. |
| `created_at` | `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP` | Account creation timestamp. |
| `updated_at` | `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP ON UPDATE` | Last profile update timestamp. |

---

## 2. Table: `station`
Stores railway junctions, terminals, and intermediate halts across India.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `station_id` | `INT` | NO | PK | Auto Inc | Unique station surrogate key. |
| `station_code` | `VARCHAR(10)` | NO | UQ | None | Standard IR station code (e.g., `'SBC'`, `'NDLS'`). |
| `station_name` | `VARCHAR(100)` | NO | - | None | Official station designation. |
| `city` | `VARCHAR(50)` | NO | - | None | Municipality / metropolitan area. |
| `state` | `VARCHAR(50)` | NO | - | None | State / Union territory. |
| `zone` | `VARCHAR(10)` | NO | - | None | Railway administrative zone (e.g., `'SWR'`, `'NR'`). |
| `number_of_platforms` | `INT` | NO | - | `1` | Operational platforms. CHECK: `> 0`. |
| `created_at` | `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP` | Ingestion timestamp. |

*Fulltext Index*: `ft_station_search(station_code, station_name, city)` enables natural language autocomplete.

---

## 3. Table: `train`
Stores train schedules, categories, endpoints, and route distances.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `train_id` | `INT` | NO | PK | Auto Inc | Unique train entity identifier. |
| `train_number` | `VARCHAR(10)` | NO | UQ | None | 5-digit official train number (e.g., `'12658'`). |
| `train_name` | `VARCHAR(100)` | NO | - | None | Name of the express or mail train. |
| `train_type` | `ENUM(...)` | NO | - | `'EXPRESS'` | `RAJDHANI`, `SHATABDI`, `TEJAS`, `SUPERFAST`, `EXPRESS`, `MAIL`. |
| `source_station_id` | `INT` | NO | FK | None | References `station(station_id)`. Originating station. |
| `dest_station_id` | `INT` | NO | FK | None | References `station(station_id)`. Terminating station. |
| `total_distance_km` | `INT` | NO | - | None | Route length in km. CHECK: `> 0`. |
| `is_active` | `BOOLEAN` | NO | - | `TRUE` | Train operational status flag. |
| `created_at` | `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP` | Registration timestamp. |

---

## 4. Table: `train_running_day`
Multivalued table indicating the days of the week on which a train departs from its source.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | `INT` | NO | PK | Auto Inc | Primary surrogate key. |
| `train_id` | `INT` | NO | FK | None | References `train(train_id)` ON DELETE CASCADE. |
| `day_of_week` | `ENUM(...)` | NO | - | None | `'MON'`, `'TUE'`, `'WED'`, `'THU'`, `'FRI'`, `'SAT'`, `'SUN'`. |

*Unique Composite*: `(train_id, day_of_week)`.

---

## 5. Table: `train_stop`
Weak entity modeling the ordered sequence of scheduled halts along a train's journey.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `stop_id` | `INT` | NO | PK | Auto Inc | Unique stop record identifier. |
| `train_id` | `INT` | NO | FK | None | References `train(train_id)` ON DELETE CASCADE. |
| `station_id` | `INT` | NO | FK | None | References `station(station_id)`. |
| `stop_sequence` | `INT` | NO | - | None | 1-based order of halt. CHECK: `>= 1`. |
| `arrival_time` | `TIME` | YES | - | `NULL` | Scheduled arrival (`NULL` for originating station). |
| `departure_time` | `TIME` | YES | - | `NULL` | Scheduled departure (`NULL` for terminating station). |
| `halt_duration_minutes` | `INT` | NO | - | `0` | Platform stoppage time in minutes. CHECK: `>= 0`. |
| `distance_from_source_km` | `INT` | NO | - | `0` | Cumulative km from origin. CHECK: `>= 0`. |
| `day_offset` | `INT` | NO | - | `0` | Journey day offset (0 = day 1, 1 = day 2). CHECK: `>= 0`. |

*Unique Composite Constraints*: `(train_id, stop_sequence)` and `(train_id, station_id)`.

---

## 6. Table: `seat_class`
Defines travel classes, dynamic base rates per kilometer, and Tatkal charge rules.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `class_code` | `VARCHAR(10)` | NO | PK | None | Primary code: `'SL'`, `'3A'`, `'2A'`, `'1A'`, `'CC'`, `'EC'`. |
| `class_name` | `VARCHAR(50)` | NO | - | None | Full class title (e.g., `'AC 3 Tier'`). |
| `is_ac` | `BOOLEAN` | NO | - | `FALSE` | Determines whether Tatkal opens at 10:00 AM (AC) or 11:00 AM (Non-AC). |
| `base_fare_per_km` | `DECIMAL(5,2)` | NO | - | None | Mileage tariff coefficient. CHECK: `> 0`. |
| `tatkal_opening_time` | `TIME` | NO | - | None | Daily opening time (10:00:00 or 11:00:00). |
| `tatkal_charge_pct` | `DECIMAL(5,2)` | NO | - | `30.00` | Surcharge percentage (10.00% for SL, 30.00% for AC). |
| `tatkal_min_charge` | `DECIMAL(7,2)` | NO | - | None | Statutory minimum Tatkal surcharge. |
| `tatkal_max_charge` | `DECIMAL(7,2)` | NO | - | None | Statutory maximum Tatkal surcharge. |

---

## 7. Table: `coach`
Represents physical coaches attached to a train composition.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `coach_id` | `INT` | NO | PK | Auto Inc | Primary surrogate key. |
| `train_id` | `INT` | NO | FK | None | References `train(train_id)` ON DELETE CASCADE. |
| `coach_code` | `VARCHAR(10)` | NO | - | None | Coach label (e.g., `'B1'`, `'B2'`, `'S1'`, `'A1'`). |
| `class_code` | `VARCHAR(10)` | NO | FK | None | References `seat_class(class_code)`. |
| `coach_position` | `INT` | NO | - | None | Physical position behind locomotive. CHECK: `>= 1`. |
| `total_seats` | `INT` | NO | - | `72` | Total seat capacity. CHECK: `> 0`. |

*Unique Composite*: `(train_id, coach_code)`.

---

## 8. Table: `seat`
Represents individual seats/berths within a coach.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `seat_id` | `INT` | NO | PK | Auto Inc | Primary surrogate key. |
| `coach_id` | `INT` | NO | FK | None | References `coach(coach_id)` ON DELETE CASCADE. |
| `seat_number` | `INT` | NO | - | None | Number within coach (e.g., 1 to 72). CHECK: `> 0`. |
| `berth_type` | `ENUM(...)` | NO | - | None | `LOWER`, `MIDDLE`, `UPPER`, `SIDE_LOWER`, `SIDE_UPPER`, `WINDOW`, `AISLE`. |

*Unique Composite*: `(coach_id, seat_number)`.

---

## 9. Table: `train_run`
Represents a specific physical journey instance of a train on a given calendar date.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `run_id` | `INT` | NO | PK | Auto Inc | Primary surrogate key. |
| `train_id` | `INT` | NO | FK | None | References `train(train_id)` ON DELETE CASCADE. |
| `journey_date` | `DATE` | NO | - | None | Calendar date of departure from origin. |
| `run_status` | `ENUM(...)` | NO | - | `'SCHEDULED'` | `'SCHEDULED'`, `'CANCELLED'`, `'COMPLETED'`. |
| `created_at` | `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP` | Generation timestamp. |

*Unique Composite*: `(train_id, journey_date)`.

---

## 10. Table: `run_seat` (Core Concurrency Control)
Manages the real-time reservation state of every seat on every train run.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `run_seat_id` | `BIGINT` | NO | PK | Auto Inc | Primary surrogate key. |
| `run_id` | `INT` | NO | FK | None | References `train_run(run_id)` ON DELETE CASCADE. |
| `seat_id` | `INT` | NO | FK | None | References `seat(seat_id)`. |
| `quota` | `ENUM(...)` | NO | - | `'GENERAL'` | `'GENERAL'`, `'TATKAL'`, `'PREMIUM_TATKAL'`. |
| `status` | `ENUM(...)` | NO | - | `'AVAILABLE'` | `'AVAILABLE'`, `'HELD'`, `'BOOKED'`. |
| `held_until` | `DATETIME` | YES | - | `NULL` | Hold expiration time (8 minutes from selection). |
| `held_by_booking_id`| `INT` | YES | - | `NULL` | ID of pending booking hold holder. |
| `version` | `INT` | NO | - | `0` | Optimistic locking concurrency version counter. |

*Critical Composite Index*: `idx_run_seat_status_quota(run_id, quota, status)` optimizes `FOR UPDATE SKIP LOCKED`.

---

## 11. Table: `booking`
Tracks passenger ticket orders, status lifecycles, and financial totals.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `booking_id` | `INT` | NO | PK | Auto Inc | Primary surrogate key. |
| `pnr` | `VARCHAR(10)` | NO | UQ | None | 10-digit unique Passenger Name Record. |
| `user_id` | `INT` | NO | FK | None | References `app_user(user_id)`. |
| `run_id` | `INT` | NO | FK | None | References `train_run(run_id)`. |
| `source_station_id` | `INT` | NO | FK | None | References `station(station_id)`. Boarding station. |
| `dest_station_id` | `INT` | NO | FK | None | References `station(station_id)`. Destination station. |
| `class_code` | `VARCHAR(10)` | NO | FK | None | References `seat_class(class_code)`. |
| `booking_type` | `ENUM(...)` | NO | - | `'GENERAL'` | `'GENERAL'`, `'TATKAL'`, `'PREMIUM_TATKAL'`. |
| `status` | `ENUM(...)` | NO | - | `'HOLD'` | `'HOLD'`, `'CONFIRMED'`, `'CANCELLED'`, `'EXPIRED'`. |
| `booking_time` | `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP` | Order timestamp. |
| `expires_at` | `DATETIME` | YES | - | `NULL` | Hold cutoff timestamp. |
| `total_fare` | `DECIMAL(10,2)`| NO | - | None | Total fare calculated via `fn_calc_fare`. CHECK: `> 0`. |

---

## 12. Table: `passenger`
Stores passenger identification details and assigned seat references.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `passenger_id` | `INT` | NO | PK | Auto Inc | Primary surrogate key. |
| `booking_id` | `INT` | NO | FK | None | References `booking(booking_id)` ON DELETE CASCADE. |
| `run_seat_id` | `BIGINT` | NO | FK | None | References `run_seat(run_seat_id)`. Assigned seat. |
| `passenger_name` | `VARCHAR(100)`| NO | - | None | Full legal name. |
| `age` | `INT` | NO | - | None | Passenger age. CHECK: `age BETWEEN 1 AND 120`. |
| `gender` | `ENUM(...)` | NO | - | None | `'MALE'`, `'FEMALE'`, `'OTHER'`. |
| `id_card_type` | `ENUM(...)` | NO | - | None | `'AADHAAR'`, `'PAN'`, `'PASSPORT'`, `'VOTER_ID'`, `'DRIVING_LICENSE'`. |
| `id_card_number` | `VARCHAR(50)` | NO | - | None | Identification proof number. |
| `seat_fare` | `DECIMAL(8,2)` | NO | - | None | Individual fare component. CHECK: `> 0`. |

---

## 13. Table: `payment`
Records financial transactions and enforces idempotency.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `payment_id` | `INT` | NO | PK | Auto Inc | Primary surrogate key. |
| `booking_id` | `INT` | NO | FK | None | References `booking(booking_id)`. |
| `idempotency_key` | `VARCHAR(100)`| NO | UQ | None | Client-supplied UUID preventing double charges. |
| `transaction_id` | `VARCHAR(100)`| NO | UQ | None | Gateway transaction reference. |
| `amount` | `DECIMAL(10,2)`| NO | - | None | Payment amount matching booking total. |
| `payment_method` | `ENUM(...)` | NO | - | None | `'UPI'`, `'CREDIT_CARD'`, `'DEBIT_CARD'`, `'NET_BANKING'`. |
| `payment_status` | `ENUM(...)` | NO | - | `'SUCCESS'` | `'SUCCESS'`, `'FAILED'`, `'REFUNDED'`. |
| `payment_time` | `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP` | Transaction execution timestamp. |

---

## 14. Table: `cancellation`
Records ticket cancellations, refund amounts, and clerkage penalties.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `cancellation_id` | `INT` | NO | PK | Auto Inc | Primary surrogate key. |
| `booking_id` | `INT` | NO | FK | None | References `booking(booking_id)`. |
| `cancellation_time`| `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP` | Cancellation timestamp. |
| `refund_amount` | `DECIMAL(10,2)`| NO | - | None | Net amount refunded to customer. |
| `cancellation_fee`| `DECIMAL(10,2)`| NO | - | None | Penalty retained by railways. |
| `reason` | `TEXT` | YES | - | `NULL` | Customer stated reason. |

---

## 15. Table: `audit_log`
Immutable system audit trail populated automatically by database triggers.

| Column | Data Type | Nullable | Key | Default | Description / Business Rules |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `log_id` | `BIGINT` | NO | PK | Auto Inc | Primary surrogate key. |
| `entity_name` | `VARCHAR(50)` | NO | - | None | Target table (e.g., `'booking'`, `'run_seat'`). |
| `entity_id` | `BIGINT` | NO | - | None | Primary key of target entity. |
| `action` | `VARCHAR(20)` | NO | - | None | `'INSERT'`, `'UPDATE'`, `'DELETE'`. |
| `old_state` | `JSON` | YES | - | `NULL` | Pre-mutation JSON representation. |
| `new_state` | `JSON` | YES | - | `NULL` | Post-mutation JSON representation. |
| `changed_by` | `VARCHAR(100)`| NO | - | `'SYSTEM'` | Database user or API principal. |
| `changed_at` | `TIMESTAMP` | NO | - | `CURRENT_TIMESTAMP` | Audit log event timestamp. |

---

## 16. Database Views

1. **`v_passenger_age`**: Derives dynamic current age from birthdate without storing stale age integers.
2. **`v_train_route`**: Denormalizes complete route timetable joining train, stops, and stations.
3. **`v_run_availability`**: Aggregates real-time seat counts (`available_seats`, `held_seats`, `booked_seats`) per run, class, and quota.
4. **`v_booking_summary`**: Summarizes customer bookings with train name, stations, passenger count, and fare.
5. **`v_admin_revenue`**: Aggregates daily financial performance, gross revenue, cancellations, refund payouts, and net profit per train and class.
