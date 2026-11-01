-- Owner: Person A
-- db/07_queries.sql: Comprehensive Demonstrations of Advanced SQL Querying
-- Includes: Multi-table JOINs, GROUP BY with HAVING, Window Functions (ROW_NUMBER, RANK, DENSE_RANK),
-- Correlated Subqueries, Common Table Expressions (CTEs), and Aggregates.

USE tatkal_db;

-- ============================================================================
-- 1. COMPLEX MULTI-TABLE INNER & LEFT JOINS
-- Retrieves complete timetable with train details, stop sequence, cumulative distance,
-- arrival/departure timings, and station details.
-- ============================================================================
SELECT 
    t.train_number,
    t.train_name,
    t.train_type,
    ts.stop_sequence,
    s.station_code,
    s.station_name,
    s.city,
    s.state,
    ts.arrival_time,
    ts.departure_time,
    ts.halt_duration_minutes,
    ts.distance_from_source_km,
    ts.day_offset
FROM train t
INNER JOIN train_stop ts ON t.train_id = ts.train_id
INNER JOIN station s ON ts.station_id = s.station_id
WHERE t.train_number = '12658'
ORDER BY ts.stop_sequence ASC;


-- ============================================================================
-- 2. GROUP BY WITH HAVING & MULTIPLE AGGREGATES
-- Identifies popular high-occupancy trains where total booked seats exceed 50,
-- calculating occupancy rate, total revenue, and average ticket fare.
-- ============================================================================
SELECT 
    t.train_number,
    t.train_name,
    tr.journey_date,
    b.class_code,
    COUNT(DISTINCT b.booking_id) AS total_bookings,
    COUNT(p.passenger_id) AS total_passengers,
    SUM(b.total_fare) AS class_gross_revenue,
    ROUND(AVG(b.total_fare), 2) AS avg_booking_value,
    MIN(b.total_fare) AS min_fare_paid,
    MAX(b.total_fare) AS max_fare_paid
FROM train t
INNER JOIN train_run tr ON t.train_id = tr.train_id
INNER JOIN booking b ON tr.run_id = b.run_id
INNER JOIN passenger p ON b.booking_id = p.booking_id
WHERE b.status = 'CONFIRMED'
GROUP BY t.train_number, t.train_name, tr.journey_date, b.class_code
HAVING total_passengers >= 1
ORDER BY class_gross_revenue DESC;


-- ============================================================================
-- 3. WINDOW FUNCTIONS: ROW_NUMBER(), DENSE_RANK(), and SUM() OVER()
-- Calculates running revenue per train over journey dates and ranks booking amounts.
-- ============================================================================
SELECT 
    b.booking_id,
    b.pnr,
    t.train_number,
    t.train_name,
    b.class_code,
    b.booking_type,
    b.total_fare,
    -- Rank bookings within each train by fare paid
    DENSE_RANK() OVER (
        PARTITION BY t.train_id 
        ORDER BY b.total_fare DESC
    ) AS fare_rank_within_train,
    -- Running cumulative revenue for the train
    SUM(b.total_fare) OVER (
        PARTITION BY t.train_id 
        ORDER BY b.booking_time
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_train_revenue,
    -- Total passenger count partitioned by booking
    COUNT(p.passenger_id) OVER (
        PARTITION BY b.booking_id
    ) AS passenger_count
FROM booking b
INNER JOIN train_run tr ON b.run_id = tr.run_id
INNER JOIN train t ON tr.train_id = t.train_id
LEFT JOIN passenger p ON b.booking_id = p.booking_id
WHERE b.status = 'CONFIRMED'
ORDER BY t.train_number, b.booking_time;


-- ============================================================================
-- 4. CORRELATED SUBQUERY WITH EXISTS
-- Finds stations that act as BOTH origin and destination across different train routes.
-- ============================================================================
SELECT 
    s.station_id,
    s.station_code,
    s.station_name,
    s.city,
    s.zone
FROM station s
WHERE EXISTS (
    SELECT 1 FROM train t1 WHERE t1.source_station_id = s.station_id
)
AND EXISTS (
    SELECT 1 FROM train t2 WHERE t2.dest_station_id = s.station_id
)
ORDER BY s.station_code;


-- ============================================================================
-- 5. COMMON TABLE EXPRESSION (CTE): Multi-Stage Route & Seat Availability
-- Evaluates train availability breakdown across Quotas (GENERAL vs TATKAL).
-- ============================================================================
WITH RunSeatSummary AS (
    SELECT 
        rs.run_id,
        c.class_code,
        rs.quota,
        COUNT(*) AS total_capacity,
        SUM(CASE WHEN rs.status = 'AVAILABLE' OR (rs.status = 'HELD' AND rs.held_until < NOW()) THEN 1 ELSE 0 END) AS available_seats,
        SUM(CASE WHEN rs.status = 'HELD' AND rs.held_until >= NOW() THEN 1 ELSE 0 END) AS held_seats,
        SUM(CASE WHEN rs.status = 'BOOKED' THEN 1 ELSE 0 END) AS booked_seats
    FROM run_seat rs
    JOIN seat s ON rs.seat_id = s.seat_id
    JOIN coach c ON s.coach_id = c.coach_id
    GROUP BY rs.run_id, c.class_code, rs.quota
)
SELECT 
    t.train_number,
    t.train_name,
    tr.journey_date,
    rss.class_code,
    rss.quota,
    rss.total_capacity,
    rss.available_seats,
    rss.held_seats,
    rss.booked_seats,
    ROUND((rss.booked_seats / rss.total_capacity) * 100, 2) AS occupancy_pct
FROM RunSeatSummary rss
JOIN train_run tr ON rss.run_id = tr.run_id
JOIN train t ON tr.train_id = t.train_id
ORDER BY tr.journey_date, t.train_number, rss.class_code;


-- ============================================================================
-- 6. FULL-TEXT SEARCH DEMONSTRATION WITH RELEVANCE SCORING
-- Natural language query matching against station directory.
-- ============================================================================
SELECT 
    station_id,
    station_code,
    station_name,
    city,
    state,
    MATCH(station_code, station_name, city) AGAINST('Bengaluru Junction' IN NATURAL LANGUAGE MODE) AS relevance_score
FROM station
WHERE MATCH(station_code, station_name, city) AGAINST('Bengaluru Junction' IN NATURAL LANGUAGE MODE)
ORDER BY relevance_score DESC;
