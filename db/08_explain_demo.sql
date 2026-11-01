-- Owner: Person A
-- db/08_explain_demo.sql: Query Optimization & EXPLAIN Execution Plan Analysis
-- Demonstrates query cost reduction, index selectivity, and B-Tree traversal
-- comparing unindexed full-table scans vs indexed index range/ref scans.

USE tatkal_db;

-- ============================================================================
-- DEMONSTRATION 1: High-Concurrency Seat Allocation Lookup
-- Query executed by sp_book_tickets to lock available seats.
-- ============================================================================

-- Query to analyze:
-- Finds available seats in a specific train run and class for booking lock.

-- Step A: Analyze performance WITH the composite index:
-- `idx_run_seat_status_quota` ON run_seat(run_id, quota, status)
EXPLAIN FORMAT=TREE
SELECT rs.run_seat_id, rs.seat_id
FROM run_seat rs
JOIN seat s ON rs.seat_id = s.seat_id
JOIN coach c ON s.coach_id = c.coach_id
WHERE rs.run_id = 1
  AND rs.quota = 'GENERAL'
  AND (rs.status = 'AVAILABLE' OR (rs.status = 'HELD' AND rs.held_until < NOW()))
  AND c.class_code = '3A'
LIMIT 2;

-- Step B: Detailed tabular execution plan with cost estimation
EXPLAIN
SELECT rs.run_seat_id, rs.seat_id
FROM run_seat rs
JOIN seat s ON rs.seat_id = s.seat_id
JOIN coach c ON s.coach_id = c.coach_id
WHERE rs.run_id = 1
  AND rs.quota = 'GENERAL'
  AND (rs.status = 'AVAILABLE' OR (rs.status = 'HELD' AND rs.held_until < NOW()))
  AND c.class_code = '3A'
LIMIT 2;

-- Expected Observation:
-- `type: ref` or `range` utilizing `idx_run_seat_status_quota`.
-- `rows examined`: < 100 instead of scanning all 300,000+ seat inventory rows.


-- ============================================================================
-- DEMONSTRATION 2: Train Route Matching Subquery
-- Executed during train search to locate trains visiting source before destination.
-- ============================================================================

-- Step A: EXPLAIN ANALYZE with composite indexes:
-- `idx_train_stop_station_train` ON train_stop(station_id, train_id)
-- `idx_train_stop_seq` ON train_stop(train_id, stop_sequence)
EXPLAIN ANALYZE
SELECT 
    t.train_id,
    t.train_number,
    t.train_name,
    ts1.departure_time AS src_dep,
    ts2.arrival_time AS dst_arr,
    (ts2.distance_from_source_km - ts1.distance_from_source_km) AS journey_km
FROM train t
JOIN train_stop ts1 ON t.train_id = ts1.train_id
JOIN train_stop ts2 ON t.train_id = ts2.train_id
WHERE ts1.station_id = 1    -- SBC
  AND ts2.station_id = 2    -- MAS
  AND ts1.stop_sequence < ts2.stop_sequence;

-- Expected Observation:
-- Nested loop join with index lookup (`ref` via `station_id`), actual time < 1ms.


-- ============================================================================
-- DEMONSTRATION 3: Customer Booking History Lookup
-- Executed on User Dashboard.
-- ============================================================================

-- Step A: Evaluates index on `booking(user_id, booking_time)`
EXPLAIN FORMAT=JSON
SELECT 
    b.booking_id,
    b.pnr,
    b.status,
    b.total_fare,
    b.booking_time
FROM booking b
WHERE b.user_id = 1
ORDER BY b.booking_time DESC
LIMIT 10;

-- Expected Observation:
-- Uses `idx_booking_user_time`, eliminating filesort (`Using filesort` is avoided).
-- Execution plan shows `backward_index_scan: true` for inverted time ordering.
