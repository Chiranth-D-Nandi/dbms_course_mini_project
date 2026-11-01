-- Owner: Person A
-- ==============================================================================
-- 05_views.sql: Relational Views for Derived Attributes, Route Topologies,
-- Real-Time Availability Aggregations, and Analytical Revenue Summaries
-- ==============================================================================

USE tatkal_db;

-- ------------------------------------------------------------------------------
-- 1. v_passenger_age: Computes derived passenger age from dob
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_passenger_age AS
SELECT
    p.pnr,
    p.passenger_seq,
    p.name,
    p.dob,
    TIMESTAMPDIFF(YEAR, p.dob, CURRENT_DATE) AS age,
    p.gender,
    p.id_proof_type,
    p.id_proof_no,
    p.fare_amount,
    p.status,
    p.run_id,
    p.seat_id,
    c.coach_number,
    s.seat_number,
    s.berth_type
FROM passenger p
LEFT JOIN seat s ON p.seat_id = s.seat_id
LEFT JOIN coach c ON s.coach_id = c.coach_id;

-- ------------------------------------------------------------------------------
-- 2. v_train_route: Computes derived halt_duration_minutes in route order
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_train_route AS
SELECT
    t.train_id,
    t.train_number,
    t.train_name,
    t.train_type,
    ts.stop_seq,
    st.station_id,
    st.station_code,
    st.station_name,
    st.city,
    st.state,
    ts.arrival_time,
    ts.departure_time,
    CASE
        WHEN ts.arrival_time IS NULL OR ts.departure_time IS NULL THEN 0
        ELSE TIMESTAMPDIFF(MINUTE, ts.arrival_time, ts.departure_time)
    END AS halt_duration_minutes,
    ts.day_offset,
    ts.distance_km
FROM train t
JOIN train_stop ts ON t.train_id = ts.train_id
JOIN station st ON ts.station_id = st.station_id
ORDER BY t.train_id, ts.stop_seq ASC;

-- ------------------------------------------------------------------------------
-- 3. v_run_availability: Real-time seat inventory counts per class and quota
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_run_availability AS
SELECT
    tr.run_id,
    t.train_id,
    t.train_number,
    t.train_name,
    tr.journey_date,
    sc.class_code,
    sc.class_name,
    rs.quota_type,
    SUM(CASE WHEN rs.seat_status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_seats,
    SUM(CASE WHEN rs.seat_status = 'HELD' THEN 1 ELSE 0 END) AS held_seats,
    SUM(CASE WHEN rs.seat_status = 'BOOKED' THEN 1 ELSE 0 END) AS booked_seats,
    COUNT(rs.seat_id) AS total_quota_seats
FROM train_run tr
JOIN train t ON tr.train_id = t.train_id
JOIN coach c ON t.train_id = c.train_id
JOIN seat_class sc ON c.class_code = sc.class_code
JOIN seat s ON c.coach_id = s.coach_id
JOIN run_seat rs ON tr.run_id = rs.run_id AND s.seat_id = rs.seat_id
WHERE tr.run_status = 'SCHEDULED'
GROUP BY tr.run_id, t.train_id, t.train_number, t.train_name, tr.journey_date, sc.class_code, sc.class_name, rs.quota_type;

-- ------------------------------------------------------------------------------
-- 4. v_booking_summary: Complete reservation details for customer tickets
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_booking_summary AS
SELECT
    b.pnr,
    b.user_id,
    CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
    u.email AS customer_email,
    u.phone AS customer_phone,
    b.run_id,
    t.train_number,
    t.train_name,
    st_src.station_name AS source_station,
    st_src.station_code AS source_code,
    st_dst.station_name AS dest_station,
    st_dst.station_code AS dest_code,
    tr.journey_date,
    b.class_code,
    sc.class_name,
    b.booking_type,
    b.status,
    b.booking_time,
    b.expires_at,
    b.total_fare,
    COUNT(p.passenger_seq) AS passengers_count,
    pm.status AS payment_status,
    pm.txn_ref,
    pm.method AS payment_method,
    cn.refund_amount,
    cn.cancelled_at
FROM booking b
JOIN app_user u ON b.user_id = u.user_id
JOIN train_run tr ON b.run_id = tr.run_id
JOIN train t ON tr.train_id = t.train_id
JOIN station st_src ON b.source_station_id = st_src.station_id
JOIN station st_dst ON b.dest_station_id = st_dst.station_id
JOIN seat_class sc ON b.class_code = sc.class_code
LEFT JOIN passenger p ON b.pnr = p.pnr
LEFT JOIN payment pm ON b.pnr = pm.pnr
LEFT JOIN cancellation cn ON b.pnr = cn.pnr
GROUP BY
    b.pnr, b.user_id, u.first_name, u.last_name, u.email, u.phone,
    b.run_id, t.train_number, t.train_name, st_src.station_name, st_src.station_code,
    st_dst.station_name, st_dst.station_code, tr.journey_date, b.class_code, sc.class_name,
    b.booking_type, b.status, b.booking_time, b.expires_at, b.total_fare,
    pm.status, pm.txn_ref, pm.method, cn.refund_amount, cn.cancelled_at;

-- ------------------------------------------------------------------------------
-- 5. v_admin_revenue: Aggregated revenue, bookings, cancellations & occupancy %
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_admin_revenue AS
SELECT
    t.train_id,
    t.train_number,
    t.train_name,
    tr.run_id,
    tr.journey_date,
    COUNT(DISTINCT CASE WHEN b.status = 'CONFIRMED' THEN b.pnr END) AS confirmed_bookings,
    COUNT(DISTINCT CASE WHEN b.status = 'CANCELLED' THEN b.pnr END) AS cancellations,
    COALESCE(SUM(CASE WHEN b.status = 'CONFIRMED' THEN b.total_fare ELSE 0 END), 0) AS total_revenue,
    COALESCE(SUM(CASE WHEN b.status = 'CANCELLED' THEN cn.refund_amount ELSE 0 END), 0) AS total_refunds,
    COALESCE(SUM(CASE WHEN b.status = 'CONFIRMED' THEN b.total_fare ELSE 0 END), 0) -
    COALESCE(SUM(CASE WHEN b.status = 'CANCELLED' THEN cn.refund_amount ELSE 0 END), 0) AS net_revenue,
    ROUND(
        (COUNT(DISTINCT CASE WHEN rs.seat_status = 'BOOKED' THEN rs.seat_id END) * 100.0) /
        NULLIF(COUNT(DISTINCT rs.seat_id), 0),
        1
    ) AS occupancy_pct
FROM train_run tr
JOIN train t ON tr.train_id = t.train_id
LEFT JOIN booking b ON tr.run_id = b.run_id
LEFT JOIN cancellation cn ON b.pnr = cn.pnr
LEFT JOIN run_seat rs ON tr.run_id = rs.run_id
GROUP BY t.train_id, t.train_number, t.train_name, tr.run_id, tr.journey_date
ORDER BY tr.journey_date DESC, net_revenue DESC;
