-- Owner: Person A
-- ==============================================================================
-- 01_schema.sql: Relational DDL for Tatkal High-Concurrency Train Booking System
-- Meets MySQL 8.0+ standards: InnoDB, utf8mb4, CHECK constraints, Composite & Full-Text Indexes
-- ==============================================================================

USE tatkal_db;

-- ------------------------------------------------------------------------------
-- 1. app_user (Strong Entity: System Users & Credentials)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'CUSTOMER') NOT NULL DEFAULT 'CUSTOMER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_user_phone CHECK (phone REGEXP '^[0-9]{10}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. station (Strong Entity: Railway Stations)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS station (
    station_id INT AUTO_INCREMENT PRIMARY KEY,
    station_code VARCHAR(10) NOT NULL UNIQUE,
    station_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    FULLTEXT idx_ft_station (station_name, city)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. train (Strong Entity: Train Profiles)
-- Note: total_coaches is derived dynamically via views/functions
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS train (
    train_id INT AUTO_INCREMENT PRIMARY KEY,
    train_number VARCHAR(10) NOT NULL UNIQUE,
    train_name VARCHAR(100) NOT NULL,
    train_type ENUM('SUPERFAST', 'EXPRESS', 'MAIL', 'RAJDHANI', 'SHATABDI') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FULLTEXT idx_ft_train_name (train_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. train_running_day (Multivalued Attribute Table for train.running_days)
-- 0 = Sunday, 1 = Monday, ..., 6 = Saturday
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS train_running_day (
    train_id INT NOT NULL,
    day_of_week TINYINT NOT NULL,
    PRIMARY KEY (train_id, day_of_week),
    CONSTRAINT chk_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT fk_running_day_train FOREIGN KEY (train_id) REFERENCES train(train_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 5. seat_class (Strong Entity: Travel Classes & Tatkal Pricing Rules)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS seat_class (
    class_code CHAR(3) NOT NULL PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL,
    is_ac BOOLEAN NOT NULL DEFAULT FALSE,
    fare_per_km DECIMAL(6,2) NOT NULL,
    tatkal_open_time TIME NOT NULL,
    tatkal_quota_pct TINYINT NOT NULL,
    tatkal_surcharge_pct DECIMAL(5,2) NOT NULL DEFAULT 30.00,
    tatkal_min_charge DECIMAL(8,2) NOT NULL DEFAULT 100.00,
    tatkal_max_charge DECIMAL(8,2) NOT NULL DEFAULT 500.00,
    CONSTRAINT chk_fare_per_km CHECK (fare_per_km > 0),
    CONSTRAINT chk_tatkal_quota_pct CHECK (tatkal_quota_pct BETWEEN 0 AND 100),
    CONSTRAINT chk_tatkal_surcharge CHECK (tatkal_surcharge_pct >= 0),
    CONSTRAINT chk_tatkal_charges CHECK (tatkal_max_charge >= tatkal_min_charge AND tatkal_min_charge >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 6. coach (Strong Entity: Train Coaches)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coach (
    coach_id INT AUTO_INCREMENT PRIMARY KEY,
    train_id INT NOT NULL,
    class_code CHAR(3) NOT NULL,
    coach_number VARCHAR(10) NOT NULL,
    CONSTRAINT uk_train_coach UNIQUE (train_id, coach_number),
    CONSTRAINT fk_coach_train FOREIGN KEY (train_id) REFERENCES train(train_id) ON DELETE CASCADE,
    CONSTRAINT fk_coach_class FOREIGN KEY (class_code) REFERENCES seat_class(class_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 7. seat (Strong Entity: Physical Seats per Coach)
-- Berth Types: LB(Lower), MB(Middle), UB(Upper), SL(Side Lower), SU(Side Upper),
--              WS(Window), MS(Middle Seat), AS(Aisle)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS seat (
    seat_id INT AUTO_INCREMENT PRIMARY KEY,
    coach_id INT NOT NULL,
    seat_number INT NOT NULL,
    berth_type ENUM('LB', 'MB', 'UB', 'SL', 'SU', 'WS', 'MS', 'AS') NOT NULL,
    CONSTRAINT uk_coach_seat UNIQUE (coach_id, seat_number),
    CONSTRAINT chk_seat_number CHECK (seat_number > 0),
    CONSTRAINT fk_seat_coach FOREIGN KEY (coach_id) REFERENCES coach(coach_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 8. train_run (Strong Entity: Scheduled Train Operations on a Calendar Date)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS train_run (
    run_id INT AUTO_INCREMENT PRIMARY KEY,
    train_id INT NOT NULL,
    journey_date DATE NOT NULL,
    run_status ENUM('SCHEDULED', 'CANCELLED', 'DEPARTED') NOT NULL DEFAULT 'SCHEDULED',
    CONSTRAINT uk_train_run UNIQUE (train_id, journey_date),
    CONSTRAINT fk_run_train FOREIGN KEY (train_id) REFERENCES train(train_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 9. train_stop (Weak Entity: Intermediate Stations along Train Route)
-- Identified by (train_id, stop_seq). Cascade deleted when train is deleted.
-- Note: halt_duration is derived dynamically in v_train_route
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS train_stop (
    train_id INT NOT NULL,
    stop_seq INT NOT NULL,
    station_id INT NOT NULL,
    arrival_time TIME NULL,
    departure_time TIME NULL,
    day_offset TINYINT NOT NULL DEFAULT 0,
    distance_km INT NOT NULL DEFAULT 0,
    PRIMARY KEY (train_id, stop_seq),
    CONSTRAINT uk_train_station UNIQUE (train_id, station_id),
    CONSTRAINT chk_stop_seq CHECK (stop_seq > 0),
    CONSTRAINT chk_day_offset CHECK (day_offset >= 0),
    CONSTRAINT chk_distance_km CHECK (distance_km >= 0),
    CONSTRAINT fk_stop_train FOREIGN KEY (train_id) REFERENCES train(train_id) ON DELETE CASCADE,
    CONSTRAINT fk_stop_station FOREIGN KEY (station_id) REFERENCES station(station_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 10. booking (Strong Entity: Customer Ticket Bookings)
-- PNR starts from 1,000,000,000 (10-digit Indian Railway standard)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS booking (
    pnr BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    run_id INT NOT NULL,
    source_station_id INT NOT NULL,
    dest_station_id INT NOT NULL,
    class_code CHAR(3) NOT NULL,
    booking_type ENUM('GENERAL', 'TATKAL') NOT NULL,
    status ENUM('PENDING', 'CONFIRMED', 'CANCELLED', 'EXPIRED', 'FAILED') NOT NULL DEFAULT 'PENDING',
    booking_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL DEFAULT NULL,
    total_fare DECIMAL(10,2) NOT NULL,
    CONSTRAINT chk_total_fare CHECK (total_fare >= 0),
    CONSTRAINT chk_different_stations CHECK (source_station_id <> dest_station_id),
    CONSTRAINT fk_booking_user FOREIGN KEY (user_id) REFERENCES app_user(user_id),
    CONSTRAINT fk_booking_run FOREIGN KEY (run_id) REFERENCES train_run(run_id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_source FOREIGN KEY (source_station_id) REFERENCES station(station_id),
    CONSTRAINT fk_booking_dest FOREIGN KEY (dest_station_id) REFERENCES station(station_id),
    CONSTRAINT fk_booking_class FOREIGN KEY (class_code) REFERENCES seat_class(class_code)
) ENGINE=InnoDB AUTO_INCREMENT=1000000000 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 11. run_seat (Weak Entity: THE CONCURRENCY INVENTORY TABLE)
-- Identified by (run_id, seat_id).
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS run_seat (
    run_id INT NOT NULL,
    seat_id INT NOT NULL,
    quota_type ENUM('GENERAL', 'TATKAL') NOT NULL,
    seat_status ENUM('AVAILABLE', 'HELD', 'BOOKED') NOT NULL DEFAULT 'AVAILABLE',
    hold_expires_at TIMESTAMP NULL DEFAULT NULL,
    held_by_pnr BIGINT NULL DEFAULT NULL,
    version_no INT NOT NULL DEFAULT 0,
    PRIMARY KEY (run_id, seat_id),
    CONSTRAINT fk_run_seat_run FOREIGN KEY (run_id) REFERENCES train_run(run_id) ON DELETE CASCADE,
    CONSTRAINT fk_run_seat_seat FOREIGN KEY (seat_id) REFERENCES seat(seat_id) ON DELETE CASCADE,
    CONSTRAINT fk_run_seat_pnr FOREIGN KEY (held_by_pnr) REFERENCES booking(pnr) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 12. passenger (Weak Entity: Passengers on a Booking)
-- Identified by (pnr, passenger_seq). Linked to allocated (run_id, seat_id).
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS passenger (
    pnr BIGINT NOT NULL,
    passenger_seq INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    gender ENUM('MALE', 'FEMALE', 'OTHER') NOT NULL,
    id_proof_type ENUM('AADHAAR', 'PAN', 'PASSPORT', 'VOTER_ID') NOT NULL,
    id_proof_no VARCHAR(50) NOT NULL,
    fare_amount DECIMAL(10,2) NOT NULL,
    status ENUM('CONFIRMED', 'CANCELLED') NOT NULL DEFAULT 'CONFIRMED',
    run_id INT NULL DEFAULT NULL,
    seat_id INT NULL DEFAULT NULL,
    PRIMARY KEY (pnr, passenger_seq),
    CONSTRAINT uk_passenger_run_seat UNIQUE (run_id, seat_id),
    CONSTRAINT chk_passenger_seq CHECK (passenger_seq BETWEEN 1 AND 6),
    CONSTRAINT chk_passenger_fare CHECK (fare_amount >= 0),
    CONSTRAINT fk_passenger_booking FOREIGN KEY (pnr) REFERENCES booking(pnr) ON DELETE CASCADE,
    CONSTRAINT fk_passenger_run_seat FOREIGN KEY (run_id, seat_id) REFERENCES run_seat(run_id, seat_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 13. payment (Strong Entity: Transaction & Idempotency)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    pnr BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    method ENUM('UPI', 'CARD', 'NETBANKING') NOT NULL,
    status ENUM('SUCCESS', 'FAILED', 'REFUNDED') NOT NULL,
    txn_ref VARCHAR(64) NOT NULL UNIQUE,
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_payment_amount CHECK (amount >= 0),
    CONSTRAINT fk_payment_booking FOREIGN KEY (pnr) REFERENCES booking(pnr) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 14. cancellation (Strong Entity: Booking Cancellation & Refunds)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cancellation (
    cancellation_id INT AUTO_INCREMENT PRIMARY KEY,
    pnr BIGINT NOT NULL UNIQUE,
    cancelled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    refund_amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    CONSTRAINT chk_refund_amount CHECK (refund_amount >= 0),
    CONSTRAINT fk_cancellation_booking FOREIGN KEY (pnr) REFERENCES booking(pnr) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 15. audit_log (Trigger-Only Audit Ledger)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(64) NOT NULL,
    record_id VARCHAR(64) NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_value JSON NULL,
    new_value JSON NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- PERFORMANCE INDEXES (Explained and justified in docs/data_dictionary.md)
-- ------------------------------------------------------------------------------
-- 1. Accelerates high-concurrency seat allocation search in sp_book_tickets
CREATE INDEX idx_run_seat_search ON run_seat(run_id, quota_type, seat_status);

-- 2. Sweeper index for event/procedure sp_release_expired_holds
CREATE INDEX idx_run_seat_expiry ON run_seat(seat_status, hold_expires_at);

-- 3. Optimizes customer booking history and status lookups
CREATE INDEX idx_booking_user ON booking(user_id, booking_time);
CREATE INDEX idx_booking_run ON booking(run_id, status);
CREATE INDEX idx_booking_expiry ON booking(status, expires_at);

-- 4. Optimizes train route matching and station lookup in sp_search_trains
CREATE INDEX idx_train_stop_station ON train_stop(station_id, train_id);
