-- Owner: Person A
-- ==============================================================================
-- 04_triggers.sql: Database-Level Integrity, Route Sanity, and Audit Triggers
-- Enforces business rules at the storage engine tier independent of application code
-- ==============================================================================

USE tatkal_db;

DELIMITER $$

-- ------------------------------------------------------------------------------
-- 1. trg_booking_status_audit: AFTER UPDATE on booking
-- Records lifecycle transitions (PENDING -> CONFIRMED / CANCELLED / EXPIRED)
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_booking_status_audit$$
CREATE TRIGGER trg_booking_status_audit
AFTER UPDATE ON booking
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_at)
        VALUES (
            'booking',
            CAST(NEW.pnr AS CHAR),
            'UPDATE_STATUS',
            JSON_OBJECT('status', OLD.status, 'expires_at', OLD.expires_at, 'total_fare', OLD.total_fare),
            JSON_OBJECT('status', NEW.status, 'expires_at', NEW.expires_at, 'total_fare', NEW.total_fare),
            NOW()
        );
    END IF;
END$$

-- ------------------------------------------------------------------------------
-- 2. trg_run_seat_audit: AFTER UPDATE on run_seat
-- Records inventory allocation transitions (AVAILABLE -> HELD -> BOOKED)
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_run_seat_audit$$
CREATE TRIGGER trg_run_seat_audit
AFTER UPDATE ON run_seat
FOR EACH ROW
BEGIN
    IF OLD.seat_status <> NEW.seat_status THEN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_at)
        VALUES (
            'run_seat',
            CONCAT(NEW.run_id, ':', NEW.seat_id),
            'STATUS_CHANGE',
            JSON_OBJECT('status', OLD.seat_status, 'held_by_pnr', OLD.held_by_pnr, 'hold_expires_at', OLD.hold_expires_at, 'version_no', OLD.version_no),
            JSON_OBJECT('status', NEW.seat_status, 'held_by_pnr', NEW.held_by_pnr, 'hold_expires_at', NEW.hold_expires_at, 'version_no', NEW.version_no),
            NOW()
        );
    END IF;
END$$

-- ------------------------------------------------------------------------------
-- 3. trg_booking_route_check: BEFORE INSERT on booking
-- Verifies source and destination belong to the train route and src < dst
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_booking_route_check$$
CREATE TRIGGER trg_booking_route_check
BEFORE INSERT ON booking
FOR EACH ROW
BEGIN
    DECLARE v_train_id INT;
    DECLARE v_src_seq INT;
    DECLARE v_dst_seq INT;

    -- Lookup train_id for this run
    SELECT train_id INTO v_train_id FROM train_run WHERE run_id = NEW.run_id;

    IF v_train_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Integrity Error: Specified train run does not exist.';
    END IF;

    -- Lookup stop sequences
    SELECT stop_seq INTO v_src_seq
    FROM train_stop
    WHERE train_id = v_train_id AND station_id = NEW.source_station_id;

    SELECT stop_seq INTO v_dst_seq
    FROM train_stop
    WHERE train_id = v_train_id AND station_id = NEW.dest_station_id;

    IF v_src_seq IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Route Error: Source station does not belong to train route.';
    END IF;

    IF v_dst_seq IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Route Error: Destination station does not belong to train route.';
    END IF;

    IF v_src_seq >= v_dst_seq THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Route Error: Source station must precede destination station in route order.';
    END IF;
END$$

-- ------------------------------------------------------------------------------
-- 4. trg_passenger_validate: BEFORE INSERT on passenger
-- Validates Date of Birth not in future and limits passengers per PNR
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_passenger_validate$$
CREATE TRIGGER trg_passenger_validate
BEFORE INSERT ON passenger
FOR EACH ROW
BEGIN
    DECLARE v_booking_type VARCHAR(20);
    DECLARE v_current_count INT;
    DECLARE v_max_allowed INT;

    -- Verify Date of Birth is not in the future
    IF NEW.dob > CURRENT_DATE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Passenger Validation Error: Date of birth cannot be in the future.';
    END IF;

    -- Verify Age sanity (not older than 125 years)
    IF TIMESTAMPDIFF(YEAR, NEW.dob, CURRENT_DATE) > 125 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Passenger Validation Error: Implausible age detected (> 125 years).';
    END IF;

    -- Verify max passengers count per booking quota type
    SELECT booking_type INTO v_booking_type FROM booking WHERE pnr = NEW.pnr;
    SET v_max_allowed = IF(v_booking_type = 'TATKAL', 4, 6);

    SELECT COUNT(*) INTO v_current_count FROM passenger WHERE pnr = NEW.pnr;

    IF v_current_count >= v_max_allowed THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Passenger Validation Error: Maximum passengers exceeded for booking quota.';
    END IF;
END$$

-- ------------------------------------------------------------------------------
-- 5. trg_payment_amount_check: BEFORE INSERT on payment
-- Ensures charged payment amount matches booking total_fare exactly
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_payment_amount_check$$
CREATE TRIGGER trg_payment_amount_check
BEFORE INSERT ON payment
FOR EACH ROW
BEGIN
    DECLARE v_total_fare DECIMAL(10,2);

    SELECT total_fare INTO v_total_fare FROM booking WHERE pnr = NEW.pnr;

    IF v_total_fare IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment Validation Error: Booking PNR not found.';
    END IF;

    IF NEW.amount <> v_total_fare THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment Validation Error: Payment amount does not equal booking total fare.';
    END IF;
END$$

-- ------------------------------------------------------------------------------
-- 6. trg_prevent_booked_seat_delete: BEFORE DELETE on run_seat
-- Protects confirmed reservations from accidental physical deletion
-- ------------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_prevent_booked_seat_delete$$
CREATE TRIGGER trg_prevent_booked_seat_delete
BEFORE DELETE ON run_seat
FOR EACH ROW
BEGIN
    IF OLD.seat_status = 'BOOKED' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Referential Error: Cannot delete a run seat that is in BOOKED status.';
    END IF;
END$$

DELIMITER ;
