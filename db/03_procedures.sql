-- Owner: Person A
-- ==============================================================================
-- 03_procedures.sql: Stored Procedures & Functions for Tatkal Engine
-- Encapsulates core ACID transactions, FOR UPDATE SKIP LOCKED concurrency,
-- dynamic fare calculation, idempotency checks, and automated hold sweeps.
-- ==============================================================================

USE tatkal_db;

DELIMITER $$

-- ------------------------------------------------------------------------------
-- 1. fn_calc_fare: Distance and Class-based Dynamic Pricing Function
-- Computes base fare per km + Tatkal surcharge clamped to [min, max]
-- ------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_calc_fare$$
CREATE FUNCTION fn_calc_fare(
    p_train_id INT,
    p_src_station_id INT,
    p_dst_station_id INT,
    p_class_code CHAR(3),
    p_booking_type ENUM('GENERAL', 'TATKAL')
) RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_src_km INT DEFAULT 0;
    DECLARE v_dst_km INT DEFAULT 0;
    DECLARE v_distance INT DEFAULT 0;
    DECLARE v_rate_per_km DECIMAL(6,2) DEFAULT 0.00;
    DECLARE v_tatkal_surcharge_pct DECIMAL(5,2) DEFAULT 0.00;
    DECLARE v_tatkal_min DECIMAL(8,2) DEFAULT 0.00;
    DECLARE v_tatkal_max DECIMAL(8,2) DEFAULT 0.00;
    DECLARE v_base_fare DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_surcharge DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_total_fare DECIMAL(10,2) DEFAULT 0.00;

    -- Retrieve distance coordinates from train_stop
    SELECT distance_km INTO v_src_km
    FROM train_stop
    WHERE train_id = p_train_id AND station_id = p_src_station_id
    LIMIT 1;

    SELECT distance_km INTO v_dst_km
    FROM train_stop
    WHERE train_id = p_train_id AND station_id = p_dst_station_id
    LIMIT 1;

    SET v_distance = ABS(v_dst_km - v_src_km);
    IF v_distance = 0 THEN
        SET v_distance = 50; -- Minimum floor distance
    END IF;

    -- Fetch class rate and tatkal parameters
    SELECT fare_per_km, tatkal_surcharge_pct, tatkal_min_charge, tatkal_max_charge
    INTO v_rate_per_km, v_tatkal_surcharge_pct, v_tatkal_min, v_tatkal_max
    FROM seat_class
    WHERE class_code = p_class_code
    LIMIT 1;

    SET v_base_fare = ROUND(v_distance * v_rate_per_km, 2);

    IF p_booking_type = 'TATKAL' THEN
        SET v_surcharge = ROUND((v_base_fare * v_tatkal_surcharge_pct) / 100.0, 2);
        -- Clamp surcharge between minimum and maximum bounds
        IF v_surcharge < v_tatkal_min THEN
            SET v_surcharge = v_tatkal_min;
        ELSEIF v_surcharge > v_tatkal_max THEN
            SET v_surcharge = v_tatkal_max;
        END IF;
        SET v_total_fare = v_base_fare + v_surcharge;
    ELSE
        SET v_total_fare = v_base_fare;
    END IF;

    RETURN v_total_fare;
END$$

-- ------------------------------------------------------------------------------
-- 2. sp_generate_run_inventory: Populates run_seat inventory per train run
-- Applies seat_class.tatkal_quota_pct to divide seats into TATKAL vs GENERAL
-- ------------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_generate_run_inventory$$
CREATE PROCEDURE sp_generate_run_inventory(IN p_run_id INT)
BEGIN
    DECLARE v_train_id INT;
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_coach_id INT;
    DECLARE v_class_code CHAR(3);
    DECLARE v_quota_pct TINYINT;
    DECLARE v_total_coach_seats INT;
    DECLARE v_tatkal_seat_limit INT;

    -- Cursor to iterate through all coaches of the train
    DECLARE cur_coaches CURSOR FOR
        SELECT c.coach_id, c.class_code, sc.tatkal_quota_pct, COUNT(s.seat_id)
        FROM train_run tr
        JOIN coach c ON tr.train_id = c.train_id
        JOIN seat_class sc ON c.class_code = sc.class_code
        LEFT JOIN seat s ON c.coach_id = s.coach_id
        WHERE tr.run_id = p_run_id
        GROUP BY c.coach_id, c.class_code, sc.tatkal_quota_pct;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    SELECT train_id INTO v_train_id FROM train_run WHERE run_id = p_run_id;
    IF v_train_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Specified train run_id does not exist.';
    END IF;

    OPEN cur_coaches;
    coach_loop: LOOP
        FETCH cur_coaches INTO v_coach_id, v_class_code, v_quota_pct, v_total_coach_seats;
        IF done THEN
            LEAVE coach_loop;
        END IF;

        IF v_total_coach_seats > 0 THEN
            -- Calculate number of seats to allocate to Tatkal
            SET v_tatkal_seat_limit = CEIL((v_total_coach_seats * v_quota_pct) / 100.0);

            -- Insert seats for this coach into run_seat
            -- Lowest seat numbers up to v_tatkal_seat_limit receive TATKAL quota
            INSERT INTO run_seat (run_id, seat_id, quota_type, seat_status, hold_expires_at, held_by_pnr, version_no)
            SELECT
                p_run_id,
                s.seat_id,
                IF(s.seat_number <= v_tatkal_seat_limit, 'TATKAL', 'GENERAL'),
                'AVAILABLE',
                NULL,
                NULL,
                0
            FROM seat s
            WHERE s.coach_id = v_coach_id
            ON DUPLICATE KEY UPDATE run_id = run_id; -- Idempotent
        END IF;
    END LOOP;
    CLOSE cur_coaches;
END$$

-- ------------------------------------------------------------------------------
-- 3. sp_search_trains: Monotonic Route Matching with Live Availability
-- Finds trains running that weekday where source stop_seq < destination stop_seq
-- ------------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_search_trains$$
CREATE PROCEDURE sp_search_trains(
    IN p_src_station_id INT,
    IN p_dst_station_id INT,
    IN p_journey_date DATE
)
BEGIN
    DECLARE v_day_of_week TINYINT;
    -- MySQL DAYOFWEEK: 1=Sun, 2=Mon... convert to 0=Sun..6=Sat
    SET v_day_of_week = DAYOFWEEK(p_journey_date) - 1;

    SELECT
        tr.run_id,
        t.train_id,
        t.train_number,
        t.train_name,
        t.train_type,
        ts_src.departure_time AS source_departure,
        ts_dst.arrival_time AS dest_arrival,
        ABS(ts_dst.distance_km - ts_src.distance_km) AS distance_km,
        tr.journey_date,
        sc.class_code,
        sc.class_name,
        sc.is_ac,
        fn_calc_fare(t.train_id, p_src_station_id, p_dst_station_id, sc.class_code, 'GENERAL') AS base_fare,
        fn_calc_fare(t.train_id, p_src_station_id, p_dst_station_id, sc.class_code, 'TATKAL') AS tatkal_fare,
        COALESCE(SUM(CASE WHEN rs.quota_type = 'GENERAL' AND rs.seat_status = 'AVAILABLE' THEN 1 ELSE 0 END), 0) AS general_available,
        COALESCE(SUM(CASE WHEN rs.quota_type = 'TATKAL' AND rs.seat_status = 'AVAILABLE' THEN 1 ELSE 0 END), 0) AS tatkal_available
    FROM train t
    JOIN train_running_day trd ON t.train_id = trd.train_id AND trd.day_of_week = v_day_of_week
    JOIN train_stop ts_src ON t.train_id = ts_src.train_id AND ts_src.station_id = p_src_station_id
    JOIN train_stop ts_dst ON t.train_id = ts_dst.train_id AND ts_dst.station_id = p_dst_station_id
    JOIN train_run tr ON t.train_id = tr.train_id AND tr.journey_date = p_journey_date AND tr.run_status = 'SCHEDULED'
    JOIN coach c ON t.train_id = c.train_id
    JOIN seat_class sc ON c.class_code = sc.class_code
    JOIN seat s ON c.coach_id = s.coach_id
    LEFT JOIN run_seat rs ON tr.run_id = rs.run_id AND s.seat_id = rs.seat_id
    WHERE ts_src.stop_seq < ts_dst.stop_seq -- Route sequence monotonicity
      AND t.is_active = TRUE
    GROUP BY
        tr.run_id, t.train_id, t.train_number, t.train_name, t.train_type,
        ts_src.departure_time, ts_dst.arrival_time, ts_src.distance_km, ts_dst.distance_km,
        tr.journey_date, sc.class_code, sc.class_name, sc.is_ac
    ORDER BY ts_src.departure_time ASC, sc.class_code ASC;
END$$

-- ------------------------------------------------------------------------------
-- 4. sp_book_tickets: HIGH-CONCURRENCY TATKAL BOOKING ENGINE
-- Uses SELECT ... FOR UPDATE SKIP LOCKED to prevent double-booking
-- ------------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_book_tickets$$
CREATE PROCEDURE sp_book_tickets(
    IN p_user_id INT,
    IN p_run_id INT,
    IN p_class_code CHAR(3),
    IN p_src_id INT,
    IN p_dst_id INT,
    IN p_booking_type ENUM('GENERAL', 'TATKAL'),
    IN p_passengers_json JSON,
    OUT p_pnr BIGINT,
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_passenger_count INT;
    DECLARE v_max_passengers INT;
    DECLARE v_journey_date DATE;
    DECLARE v_train_id INT;
    DECLARE v_run_status VARCHAR(20);
    DECLARE v_departure_dt DATETIME;
    DECLARE v_tatkal_open_time TIME;
    DECLARE v_tatkal_open_dt DATETIME;
    DECLARE v_fare_per_passenger DECIMAL(10,2);
    DECLARE v_total_fare DECIMAL(10,2);
    DECLARE v_available_seats_count INT DEFAULT 0;
    DECLARE v_pnr BIGINT;
    DECLARE i INT DEFAULT 0;
    DECLARE v_seat_id INT;
    DECLARE v_candidate_id INT;
    DECLARE v_locked_seat_id INT;
    DECLARE v_candidates_done BOOLEAN DEFAULT FALSE;
    DECLARE seat_candidates CURSOR FOR
        SELECT s.seat_id FROM seat s JOIN coach c ON c.coach_id = s.coach_id
        WHERE c.train_id = v_train_id AND c.class_code = p_class_code
        ORDER BY s.seat_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_candidates_done = TRUE;

    -- Deadlock Handler
    DECLARE EXIT HANDLER FOR 1213
    BEGIN
        ROLLBACK;
        SET p_pnr = NULL;
        SET p_status = 'DEADLOCK_RETRY';
        SET p_message = 'Database deadlock encountered. Please retry transaction.';
    END;

    -- Generic SQL Exception Handler
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_pnr = NULL;
        SET p_status = 'ERROR';
        SET p_message = 'Internal database exception occurred during seat allocation.';
    END;

    -- Step 1: Validate passenger count
    SET v_passenger_count = JSON_LENGTH(p_passengers_json);
    SET v_max_passengers = IF(p_booking_type = 'TATKAL', 4, 6);

    IF v_passenger_count IS NULL OR v_passenger_count < 1 OR v_passenger_count > v_max_passengers THEN
        SET p_pnr = NULL;
        SET p_status = 'INVALID_PASSENGERS';
        SET p_message = CONCAT('Passenger count must be between 1 and ', v_max_passengers, ' for ', p_booking_type);
        LEAVE proc_label;
    END IF;

    -- Step 2: Validate train run existence and status
    SELECT tr.journey_date, tr.train_id, tr.run_status
    INTO v_journey_date, v_train_id, v_run_status
    FROM train_run tr
    WHERE tr.run_id = p_run_id;

    IF v_run_status IS NULL OR v_run_status <> 'SCHEDULED' THEN
        SET p_pnr = NULL;
        SET p_status = 'RUN_NOT_AVAILABLE';
        SET p_message = 'Train run is either departed, cancelled, or non-existent.';
        LEAVE proc_label;
    END IF;

    SELECT TIMESTAMP(DATE_ADD(tr.journey_date, INTERVAL ts.day_offset DAY), ts.departure_time)
    INTO v_departure_dt
    FROM train_run tr JOIN train_stop ts ON ts.train_id = tr.train_id
    JOIN train t ON t.train_id = tr.train_id AND t.is_active = TRUE
    WHERE tr.run_id = p_run_id AND ts.station_id = p_src_id;
    IF v_departure_dt IS NULL OR NOW() >= v_departure_dt THEN
        SET p_pnr = NULL;
        SET p_status = 'DEPARTED';
        SET p_message = 'Boarding departure has passed or the train is inactive.';
        LEAVE proc_label;
    END IF;

    -- Step 3: Tatkal Window Opening Validation
    SELECT tatkal_open_time INTO v_tatkal_open_time
    FROM seat_class
    WHERE class_code = p_class_code;

    IF p_booking_type = 'TATKAL' THEN
        -- Window opens on (journey_date - 1 day) at class tatkal_open_time
        SET v_tatkal_open_dt = TIMESTAMP(DATE_SUB(v_journey_date, INTERVAL 1 DAY), v_tatkal_open_time);

        -- Check demo bypass flag (@DEMO_BYPASS_TATKAL_WINDOW)
        IF COALESCE(@DEMO_BYPASS_TATKAL_WINDOW, 0) <> 1 THEN
            IF NOW() < v_tatkal_open_dt THEN
                SET p_pnr = NULL;
                SET p_status = 'TATKAL_WINDOW_CLOSED';
                SET p_message = CONCAT('Tatkal window opens at ', DATE_FORMAT(v_tatkal_open_dt, '%Y-%m-%d %H:%i:%s'));
                LEAVE proc_label;
            END IF;
        END IF;
    END IF;

    -- Step 4: Calculate Fare
    SET v_fare_per_passenger = fn_calc_fare(v_train_id, p_src_id, p_dst_id, p_class_code, p_booking_type);
    SET v_total_fare = v_fare_per_passenger * v_passenger_count;

    -- Step 5: START TRANSACTION & LOCK SEATS
    START TRANSACTION;

    -- Temporary table to hold locked seat IDs
    DROP TEMPORARY TABLE IF EXISTS tmp_locked_seats;
    CREATE TEMPORARY TABLE tmp_locked_seats (
        alloc_order INT AUTO_INCREMENT PRIMARY KEY,
        seat_id INT NOT NULL
    );

    -- Candidate discovery is a consistent read. Lock exact inventory primary keys
    -- so a sorted join cannot accidentally lock every seat before applying LIMIT.
    SET v_candidates_done = FALSE;
    OPEN seat_candidates;
    candidate_loop: LOOP
        FETCH seat_candidates INTO v_candidate_id;
        IF v_candidates_done OR v_available_seats_count >= v_passenger_count THEN
            LEAVE candidate_loop;
        END IF;
        SET v_locked_seat_id = NULL;
        BEGIN
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_locked_seat_id = NULL;
            SELECT rs.seat_id INTO v_locked_seat_id
            FROM run_seat rs
            WHERE rs.run_id = p_run_id AND rs.seat_id = v_candidate_id
              AND rs.quota_type = p_booking_type AND rs.seat_status = 'AVAILABLE'
            FOR UPDATE SKIP LOCKED;
        END;
        IF v_locked_seat_id IS NOT NULL THEN
            INSERT INTO tmp_locked_seats (seat_id) VALUES (v_locked_seat_id);
            SET v_available_seats_count = v_available_seats_count + 1;
        END IF;
    END LOOP;
    CLOSE seat_candidates;

    -- Check if sufficient seats were locked
    IF v_available_seats_count < v_passenger_count THEN
        ROLLBACK;
        DROP TEMPORARY TABLE IF EXISTS tmp_locked_seats;
        SET p_pnr = NULL;
        SET p_status = 'SOLD_OUT';
        SET p_message = CONCAT('Requested ', v_passenger_count, ' seats not available in quota.');
        LEAVE proc_label;
    END IF;

    -- Create Booking record in PENDING status (8-minute hold)
    INSERT INTO booking (
        user_id, run_id, source_station_id, dest_station_id, class_code,
        booking_type, status, booking_time, expires_at, total_fare
    ) VALUES (
        p_user_id, p_run_id, p_src_id, p_dst_id, p_class_code,
        p_booking_type, 'PENDING', NOW(), DATE_ADD(NOW(), INTERVAL 8 MINUTE), v_total_fare
    );

    SET v_pnr = LAST_INSERT_ID();

    -- Mark locked seats as HELD for 8 minutes
    UPDATE run_seat rs
    JOIN tmp_locked_seats tls ON rs.seat_id = tls.seat_id
    SET rs.seat_status = 'HELD',
        rs.hold_expires_at = DATE_ADD(NOW(), INTERVAL 8 MINUTE),
        rs.held_by_pnr = v_pnr,
        rs.version_no = rs.version_no + 1
    WHERE rs.run_id = p_run_id;

    -- Insert passengers linked to allocated seats
    WHILE i < v_passenger_count DO
        SELECT seat_id INTO v_seat_id FROM tmp_locked_seats WHERE alloc_order = (i + 1);

        INSERT INTO passenger (
            pnr, passenger_seq, name, dob, gender, id_proof_type, id_proof_no,
            fare_amount, status, run_id, seat_id
        ) VALUES (
            v_pnr,
            i + 1,
            JSON_UNQUOTE(JSON_EXTRACT(p_passengers_json, CONCAT('$[', i, '].name'))),
            JSON_UNQUOTE(JSON_EXTRACT(p_passengers_json, CONCAT('$[', i, '].dob'))),
            JSON_UNQUOTE(JSON_EXTRACT(p_passengers_json, CONCAT('$[', i, '].gender'))),
            JSON_UNQUOTE(JSON_EXTRACT(p_passengers_json, CONCAT('$[', i, '].id_proof_type'))),
            JSON_UNQUOTE(JSON_EXTRACT(p_passengers_json, CONCAT('$[', i, '].id_proof_no'))),
            v_fare_per_passenger,
            'CONFIRMED',
            p_run_id,
            v_seat_id
        );

        SET i = i + 1;
    END WHILE;

    DROP TEMPORARY TABLE IF EXISTS tmp_locked_seats;

    COMMIT;

    SET p_pnr = v_pnr;
    SET p_status = 'PENDING';
    SET p_message = 'Seats successfully held. Please complete payment within 8 minutes.';
END$$

-- ------------------------------------------------------------------------------
-- 5. sp_confirm_payment: Idempotent Payment Confirmation & Ticket Issuance
-- ------------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_confirm_payment$$
CREATE PROCEDURE sp_confirm_payment(
    IN p_pnr BIGINT,
    IN p_amount DECIMAL(10,2),
    IN p_method VARCHAR(20),
    IN p_txn_ref VARCHAR(64),
    IN p_idempotency_key VARCHAR(128),
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
proc_pay: BEGIN
    DECLARE v_booking_status VARCHAR(20);
    DECLARE v_expires_at TIMESTAMP;
    DECLARE v_total_fare DECIMAL(10,2);
    DECLARE v_existing_payment_id INT;
    DECLARE v_existing_pnr BIGINT;
    DECLARE v_existing_method VARCHAR(20);
    DECLARE v_existing_amount DECIMAL(10,2);
    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        ROLLBACK;
        SET p_status = 'KEY_CONFLICT';
        SET p_message = 'Payment key or transaction reference is already used.';
    END;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Lock booking row FOR UPDATE
    SELECT status, expires_at, total_fare
    INTO v_booking_status, v_expires_at, v_total_fare
    FROM booking
    WHERE pnr = p_pnr
    FOR UPDATE;

    IF v_booking_status IS NULL THEN
        ROLLBACK;
        SET p_status = 'NOT_FOUND';
        SET p_message = 'PNR does not exist.';
        LEAVE proc_pay;
    END IF;

    -- Serialize retries on the booking lock, then bind a key to its request.
    SELECT payment_id, pnr, amount, method
    INTO v_existing_payment_id, v_existing_pnr, v_existing_amount, v_existing_method
    FROM payment WHERE idempotency_key = p_idempotency_key;
    IF v_existing_payment_id IS NOT NULL THEN
        ROLLBACK;
        IF v_existing_pnr = p_pnr AND v_existing_amount = p_amount AND v_existing_method = p_method THEN
            SET p_status = 'SUCCESS';
            SET p_message = 'Payment already confirmed (Idempotent response).';
        ELSE
            SET p_status = 'KEY_CONFLICT';
            SET p_message = 'This payment key belongs to a different request.';
        END IF;
        LEAVE proc_pay;
    END IF;

    IF v_booking_status = 'CONFIRMED' THEN
        ROLLBACK;
        SET p_status = 'ALREADY_CONFIRMED';
        SET p_message = 'This booking has already been paid and confirmed.';
        LEAVE proc_pay;
    END IF;

    IF v_booking_status <> 'PENDING' THEN
        ROLLBACK;
        SET p_status = 'INVALID_STATUS';
        SET p_message = 'Only pending bookings can be paid.';
        LEAVE proc_pay;
    END IF;

    IF v_expires_at IS NOT NULL AND NOW() >= v_expires_at THEN
        -- Mark expired and release seats
        UPDATE booking SET status = 'EXPIRED' WHERE pnr = p_pnr;
        UPDATE passenger SET run_id = NULL, seat_id = NULL WHERE pnr = p_pnr;
        UPDATE run_seat
        SET seat_status = 'AVAILABLE', hold_expires_at = NULL, held_by_pnr = NULL
        WHERE held_by_pnr = p_pnr;

        COMMIT;
        SET p_status = 'HOLD_EXPIRED';
        SET p_message = 'Seat hold has expired. Seats returned to inventory.';
        LEAVE proc_pay;
    END IF;

    IF p_amount <> v_total_fare THEN
        ROLLBACK;
        SET p_status = 'AMOUNT_MISMATCH';
        SET p_message = CONCAT('Payment amount (₹', p_amount, ') does not match total ticket fare (₹', v_total_fare, ')');
        LEAVE proc_pay;
    END IF;

    -- Record Payment
    INSERT INTO payment (pnr, amount, method, status, txn_ref, idempotency_key, created_at)
    VALUES (p_pnr, p_amount, p_method, 'SUCCESS', p_txn_ref, p_idempotency_key, NOW());

    -- Confirm Booking
    UPDATE booking
    SET status = 'CONFIRMED', expires_at = NULL
    WHERE pnr = p_pnr;

    -- Transition Seats from HELD to BOOKED
    UPDATE run_seat
    SET seat_status = 'BOOKED', hold_expires_at = NULL
    WHERE held_by_pnr = p_pnr;

    COMMIT;

    SET p_status = 'SUCCESS';
    SET p_message = 'Payment processed successfully. Ticket confirmed!';
END$$

-- ------------------------------------------------------------------------------
-- 6. sp_cancel_booking: Ticket Cancellation with Policy-Graded Refunds
-- ------------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_cancel_booking$$
CREATE PROCEDURE sp_cancel_booking(
    IN p_pnr BIGINT,
    IN p_user_id INT,
    IN p_reason TEXT,
    OUT p_status VARCHAR(20),
    OUT p_refund_amount DECIMAL(10,2),
    OUT p_message VARCHAR(255)
)
proc_cancel: BEGIN
    DECLARE v_owner_id INT;
    DECLARE v_user_role VARCHAR(20);
    DECLARE v_status VARCHAR(20);
    DECLARE v_total_fare DECIMAL(10,2);
    DECLARE v_booking_type VARCHAR(20);
    DECLARE v_journey_date DATE;
    DECLARE v_departure_time TIME;
    DECLARE v_departure_dt DATETIME;
    DECLARE v_hours_to_dep DECIMAL(12,4);
    DECLARE v_day_offset INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT b.user_id, b.status, b.total_fare, b.booking_type, tr.journey_date, ts.departure_time, ts.day_offset
    INTO v_owner_id, v_status, v_total_fare, v_booking_type, v_journey_date, v_departure_time, v_day_offset
    FROM booking b
    JOIN train_run tr ON b.run_id = tr.run_id
    JOIN train_stop ts ON tr.train_id = ts.train_id AND b.source_station_id = ts.station_id
    WHERE b.pnr = p_pnr
    FOR UPDATE;

    SELECT role INTO v_user_role FROM app_user WHERE user_id = p_user_id;

    IF v_owner_id IS NULL THEN
        ROLLBACK;
        SET p_status = 'NOT_FOUND';
        SET p_refund_amount = 0;
        SET p_message = 'Booking not found.';
        LEAVE proc_cancel;
    END IF;

    -- Security Authorization Check: Owner or Admin
    IF v_owner_id <> p_user_id AND v_user_role <> 'ADMIN' THEN
        ROLLBACK;
        SET p_status = 'UNAUTHORIZED';
        SET p_refund_amount = 0.00;
        SET p_message = 'You do not have permission to cancel this booking.';
        LEAVE proc_cancel;
    END IF;

    IF v_status <> 'CONFIRMED' THEN
        ROLLBACK;
        SET p_status = 'INVALID_STATUS';
        SET p_refund_amount = 0.00;
        SET p_message = CONCAT('Cannot cancel booking with current status: ', v_status);
        LEAVE proc_cancel;
    END IF;

    -- Compute Hours to Departure
    SET v_departure_dt = TIMESTAMP(DATE_ADD(v_journey_date, INTERVAL v_day_offset DAY), COALESCE(v_departure_time, '00:00:00'));
    SET v_hours_to_dep = TIMESTAMPDIFF(SECOND, NOW(), v_departure_dt) / 3600.0;

    -- Project demonstration refund policy (not an official railway tariff).
    IF v_booking_type = 'TATKAL' THEN
        SET p_refund_amount = 0.00; -- 0% refund on Tatkal
    ELSE
        IF v_hours_to_dep > 48 THEN
            SET p_refund_amount = ROUND(v_total_fare * 0.90, 2); -- 90%
        ELSEIF v_hours_to_dep >= 12 THEN
            SET p_refund_amount = ROUND(v_total_fare * 0.50, 2); -- 50%
        ELSEIF v_hours_to_dep >= 4 THEN
            SET p_refund_amount = ROUND(v_total_fare * 0.25, 2); -- 25%
        ELSE
            SET p_refund_amount = 0.00; -- 0%
        END IF;
    END IF;

    -- Record Cancellation
    INSERT INTO cancellation (pnr, cancelled_at, refund_amount, reason)
    VALUES (p_pnr, NOW(), p_refund_amount, p_reason);

    -- Update Booking & Passengers
    UPDATE booking SET status = 'CANCELLED' WHERE pnr = p_pnr;
    UPDATE passenger SET status = 'CANCELLED', run_id = NULL, seat_id = NULL WHERE pnr = p_pnr;

    -- Free Seats back into run_seat inventory
    UPDATE run_seat
    SET seat_status = 'AVAILABLE', hold_expires_at = NULL, held_by_pnr = NULL
    WHERE held_by_pnr = p_pnr;

    COMMIT;

    SET p_status = 'CANCELLED';
    SET p_message = CONCAT('Booking cancelled. Refund amount of ₹', p_refund_amount, ' calculated.');
END$$

-- ------------------------------------------------------------------------------
-- 7. sp_release_expired_holds: Periodic Sweeper Procedure
-- Invoked automatically by ev_release_expired_holds every 30 seconds
-- ------------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_release_expired_holds$$
CREATE PROCEDURE sp_release_expired_holds()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    START TRANSACTION;
    -- Lock bookings first, matching payment/cancellation lock order.
    UPDATE booking
    SET status = 'EXPIRED'
    WHERE status = 'PENDING' AND expires_at <= NOW();

    UPDATE run_seat rs
    JOIN booking b ON b.pnr = rs.held_by_pnr
    SET seat_status = 'AVAILABLE',
        hold_expires_at = NULL,
        held_by_pnr = NULL,
        version_no = version_no + 1
    WHERE rs.seat_status = 'HELD' AND b.status = 'EXPIRED';

    -- 3. Clear seat references for expired passengers so seats can be re-allocated
    UPDATE passenger p
    JOIN booking b ON p.pnr = b.pnr
    SET p.run_id = NULL, p.seat_id = NULL
    WHERE b.status = 'EXPIRED'
      AND p.run_id IS NOT NULL;
    COMMIT;
END$$

DELIMITER ;

GRANT EXECUTE ON PROCEDURE tatkal_db.sp_search_trains TO 'app_ro'@'localhost', 'app_ro'@'127.0.0.1';
