# Data dictionary

Generated from the configured MySQL schema. `db/01_schema.sql` and `db/02_alter_demo.sql` are the SQL source of truth.

The booking primary key is `pnr`; `train_running_day`, `train_stop`, `run_seat` and `passenger` use composite primary keys. Only active passenger allocations retain run/seat references.

## `app_user`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `user_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `first_name` | `varchar(50)` | `NO` | `` | `NULL` | `` |
| `last_name` | `varchar(50)` | `NO` | `` | `NULL` | `` |
| `email` | `varchar(100)` | `NO` | `UNI` | `NULL` | `` |
| `phone` | `varchar(15)` | `NO` | `UNI` | `NULL` | `` |
| `password_hash` | `varchar(255)` | `NO` | `` | `NULL` | `` |
| `role` | `enum('ADMIN','CUSTOMER')` | `NO` | `` | `CUSTOMER` | `` |
| `is_active` | `tinyint(1)` | `NO` | `` | `1` | `` |
| `created_at` | `timestamp` | `NO` | `` | `CURRENT_TIMESTAMP` | `DEFAULT_GENERATED` |

Indexes:
- `email(email)` (unique)
- `phone(phone)` (unique)
- `PRIMARY(user_id)` (unique)

## `audit_log`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `log_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `table_name` | `varchar(64)` | `NO` | `` | `NULL` | `` |
| `record_id` | `varchar(64)` | `NO` | `` | `NULL` | `` |
| `action` | `varchar(20)` | `NO` | `` | `NULL` | `` |
| `old_value` | `json` | `YES` | `` | `NULL` | `` |
| `new_value` | `json` | `YES` | `` | `NULL` | `` |
| `changed_at` | `timestamp` | `NO` | `` | `CURRENT_TIMESTAMP` | `DEFAULT_GENERATED` |

Indexes:
- `PRIMARY(log_id)` (unique)

## `booking`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `pnr` | `bigint` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `user_id` | `int` | `NO` | `MUL` | `NULL` | `` |
| `run_id` | `int` | `NO` | `MUL` | `NULL` | `` |
| `source_station_id` | `int` | `NO` | `MUL` | `NULL` | `` |
| `dest_station_id` | `int` | `NO` | `MUL` | `NULL` | `` |
| `class_code` | `char(3)` | `NO` | `MUL` | `NULL` | `` |
| `booking_type` | `enum('GENERAL','TATKAL')` | `NO` | `` | `NULL` | `` |
| `status` | `enum('PENDING','CONFIRMED','CANCELLED','EXPIRED','FAILED')` | `NO` | `MUL` | `PENDING` | `` |
| `booking_time` | `timestamp` | `NO` | `` | `CURRENT_TIMESTAMP` | `DEFAULT_GENERATED` |
| `expires_at` | `timestamp` | `YES` | `` | `NULL` | `` |
| `total_fare` | `decimal(10,2)` | `NO` | `` | `NULL` | `` |

Foreign keys:
- `(class_code)` → `seat_class(class_code)`
- `(dest_station_id)` → `station(station_id)`
- `(run_id)` → `train_run(run_id)`
- `(source_station_id)` → `station(station_id)`
- `(user_id)` → `app_user(user_id)`

Indexes:
- `fk_booking_class(class_code)`
- `fk_booking_dest(dest_station_id)`
- `fk_booking_source(source_station_id)`
- `idx_booking_expiry(status, expires_at)`
- `idx_booking_run(run_id, status)`
- `idx_booking_user(user_id, booking_time)`
- `PRIMARY(pnr)` (unique)

## `cancellation`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `cancellation_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `pnr` | `bigint` | `NO` | `UNI` | `NULL` | `` |
| `cancelled_at` | `timestamp` | `NO` | `` | `CURRENT_TIMESTAMP` | `DEFAULT_GENERATED` |
| `refund_amount` | `decimal(10,2)` | `NO` | `` | `NULL` | `` |
| `reason` | `text` | `NO` | `` | `NULL` | `` |

Foreign keys:
- `(pnr)` → `booking(pnr)`

Indexes:
- `pnr(pnr)` (unique)
- `PRIMARY(cancellation_id)` (unique)

## `coach`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `coach_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `train_id` | `int` | `NO` | `MUL` | `NULL` | `` |
| `class_code` | `char(3)` | `NO` | `MUL` | `NULL` | `` |
| `coach_number` | `varchar(10)` | `NO` | `` | `NULL` | `` |

Foreign keys:
- `(class_code)` → `seat_class(class_code)`
- `(train_id)` → `train(train_id)`

Indexes:
- `fk_coach_class(class_code)`
- `PRIMARY(coach_id)` (unique)
- `uk_train_coach(train_id, coach_number)` (unique)

## `passenger`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `pnr` | `bigint` | `NO` | `PRI` | `NULL` | `` |
| `passenger_seq` | `int` | `NO` | `PRI` | `NULL` | `` |
| `name` | `varchar(100)` | `NO` | `` | `NULL` | `` |
| `dob` | `date` | `NO` | `` | `NULL` | `` |
| `gender` | `enum('MALE','FEMALE','OTHER')` | `NO` | `` | `NULL` | `` |
| `id_proof_type` | `enum('AADHAAR','PAN','PASSPORT','VOTER_ID')` | `NO` | `` | `NULL` | `` |
| `id_proof_no` | `varchar(50)` | `NO` | `` | `NULL` | `` |
| `fare_amount` | `decimal(10,2)` | `NO` | `` | `NULL` | `` |
| `status` | `enum('CONFIRMED','CANCELLED')` | `NO` | `` | `CONFIRMED` | `` |
| `run_id` | `int` | `YES` | `MUL` | `NULL` | `` |
| `seat_id` | `int` | `YES` | `` | `NULL` | `` |

Foreign keys:
- `(pnr)` → `booking(pnr)`
- `(run_id, seat_id)` → `run_seat(run_id, seat_id)`

Indexes:
- `PRIMARY(pnr, passenger_seq)` (unique)
- `uk_passenger_run_seat(run_id, seat_id)` (unique)

## `payment`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `payment_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `pnr` | `bigint` | `NO` | `MUL` | `NULL` | `` |
| `amount` | `decimal(10,2)` | `NO` | `` | `NULL` | `` |
| `method` | `enum('UPI','CARD','NETBANKING')` | `NO` | `` | `NULL` | `` |
| `status` | `enum('SUCCESS','FAILED','REFUNDED')` | `NO` | `` | `NULL` | `` |
| `txn_ref` | `varchar(64)` | `NO` | `UNI` | `NULL` | `` |
| `idempotency_key` | `varchar(128)` | `NO` | `UNI` | `NULL` | `` |
| `created_at` | `timestamp` | `NO` | `` | `CURRENT_TIMESTAMP` | `DEFAULT_GENERATED` |

Foreign keys:
- `(pnr)` → `booking(pnr)`

Indexes:
- `fk_payment_booking(pnr)`
- `idempotency_key(idempotency_key)` (unique)
- `PRIMARY(payment_id)` (unique)
- `txn_ref(txn_ref)` (unique)

## `run_seat`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `run_id` | `int` | `NO` | `PRI` | `NULL` | `` |
| `seat_id` | `int` | `NO` | `PRI` | `NULL` | `` |
| `quota_type` | `enum('GENERAL','TATKAL')` | `NO` | `` | `NULL` | `` |
| `seat_status` | `enum('AVAILABLE','HELD','BOOKED')` | `NO` | `MUL` | `AVAILABLE` | `` |
| `hold_expires_at` | `timestamp` | `YES` | `` | `NULL` | `` |
| `held_by_pnr` | `bigint` | `YES` | `MUL` | `NULL` | `` |
| `version_no` | `int` | `NO` | `` | `0` | `` |

Foreign keys:
- `(held_by_pnr)` → `booking(pnr)`
- `(run_id)` → `train_run(run_id)`
- `(seat_id)` → `seat(seat_id)`

Indexes:
- `fk_run_seat_pnr(held_by_pnr)`
- `fk_run_seat_seat(seat_id)`
- `idx_run_seat_expiry(seat_status, hold_expires_at)`
- `idx_run_seat_search(run_id, quota_type, seat_status)`
- `PRIMARY(run_id, seat_id)` (unique)

## `seat`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `seat_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `coach_id` | `int` | `NO` | `MUL` | `NULL` | `` |
| `seat_number` | `int` | `NO` | `` | `NULL` | `` |
| `berth_type` | `enum('LB','MB','UB','SL','SU','WS','MS','AS')` | `NO` | `` | `NULL` | `` |

Foreign keys:
- `(coach_id)` → `coach(coach_id)`

Indexes:
- `PRIMARY(seat_id)` (unique)
- `uk_coach_seat(coach_id, seat_number)` (unique)

## `seat_class`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `class_code` | `char(3)` | `NO` | `PRI` | `NULL` | `` |
| `class_name` | `varchar(50)` | `NO` | `` | `NULL` | `` |
| `is_ac` | `tinyint(1)` | `NO` | `` | `0` | `` |
| `fare_per_km` | `decimal(6,2)` | `NO` | `` | `NULL` | `` |
| `tatkal_open_time` | `time` | `NO` | `` | `NULL` | `` |
| `tatkal_quota_pct` | `tinyint` | `NO` | `` | `NULL` | `` |
| `tatkal_surcharge_pct` | `decimal(5,2)` | `NO` | `` | `30.00` | `` |
| `tatkal_min_charge` | `decimal(8,2)` | `NO` | `` | `100.00` | `` |
| `tatkal_max_charge` | `decimal(8,2)` | `NO` | `` | `500.00` | `` |

Indexes:
- `PRIMARY(class_code)` (unique)

## `station`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `station_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `station_code` | `varchar(10)` | `NO` | `UNI` | `NULL` | `` |
| `station_name` | `varchar(100)` | `NO` | `MUL` | `NULL` | `` |
| `city` | `varchar(100)` | `NO` | `` | `NULL` | `` |
| `state` | `varchar(100)` | `NO` | `` | `NULL` | `` |

Indexes:
- `idx_ft_station(station_name, city)`
- `PRIMARY(station_id)` (unique)
- `station_code(station_code)` (unique)

## `train`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `train_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `train_number` | `varchar(10)` | `NO` | `UNI` | `NULL` | `` |
| `train_name` | `varchar(100)` | `NO` | `MUL` | `NULL` | `` |
| `train_type` | `enum('SUPERFAST','EXPRESS','MAIL','RAJDHANI','SHATABDI')` | `NO` | `` | `NULL` | `` |
| `is_active` | `tinyint(1)` | `NO` | `` | `1` | `` |

Indexes:
- `idx_ft_train_name(train_name)`
- `PRIMARY(train_id)` (unique)
- `train_number(train_number)` (unique)

## `train_run`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `run_id` | `int` | `NO` | `PRI` | `NULL` | `auto_increment` |
| `train_id` | `int` | `NO` | `MUL` | `NULL` | `` |
| `journey_date` | `date` | `NO` | `` | `NULL` | `` |
| `run_status` | `enum('SCHEDULED','CANCELLED','DEPARTED')` | `NO` | `` | `SCHEDULED` | `` |

Foreign keys:
- `(train_id)` → `train(train_id)`

Indexes:
- `PRIMARY(run_id)` (unique)
- `uk_train_run(train_id, journey_date)` (unique)

## `train_running_day`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `train_id` | `int` | `NO` | `PRI` | `NULL` | `` |
| `day_of_week` | `tinyint` | `NO` | `PRI` | `NULL` | `` |

Foreign keys:
- `(train_id)` → `train(train_id)`

Indexes:
- `PRIMARY(train_id, day_of_week)` (unique)

## `train_stop`

| Column | Type | Nullable | Key | Default | Extra |
| --- | --- | --- | --- | --- | --- |
| `train_id` | `int` | `NO` | `PRI` | `NULL` | `` |
| `stop_seq` | `int` | `NO` | `PRI` | `NULL` | `` |
| `station_id` | `int` | `NO` | `MUL` | `NULL` | `` |
| `arrival_time` | `time` | `YES` | `` | `NULL` | `` |
| `departure_time` | `time` | `YES` | `` | `NULL` | `` |
| `day_offset` | `tinyint` | `NO` | `` | `0` | `` |
| `distance_km` | `int` | `NO` | `` | `0` | `` |

Foreign keys:
- `(station_id)` → `station(station_id)`
- `(train_id)` → `train(train_id)`

Indexes:
- `idx_train_stop_station(station_id, train_id)`
- `PRIMARY(train_id, stop_seq)` (unique)
- `uk_train_station(train_id, station_id)` (unique)
