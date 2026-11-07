-- Observe actual optimizer choices; no fixed timing or row-count claims.
USE tatkal_db;

-- 1. Primary-key point lookup used to lock one allocation candidate.
EXPLAIN FORMAT=TREE
SELECT seat_id FROM run_seat WHERE run_id=1 AND seat_id=1
AND quota_type='GENERAL' AND seat_status='AVAILABLE';

-- 2. Compare the inventory search index with an explicit ignored index.
EXPLAIN SELECT seat_id FROM run_seat FORCE INDEX(idx_run_seat_search)
WHERE run_id=1 AND quota_type='GENERAL' AND seat_status='AVAILABLE';
EXPLAIN SELECT seat_id FROM run_seat IGNORE INDEX(idx_run_seat_search)
WHERE run_id=1 AND quota_type='GENERAL' AND seat_status='AVAILABLE';

-- 3. Execute and inspect route matching (read-only).
EXPLAIN ANALYZE
SELECT t.train_number,a.departure_time,z.arrival_time,z.distance_km-a.distance_km AS distance_km
FROM train t JOIN train_stop a ON a.train_id=t.train_id
JOIN train_stop z ON z.train_id=t.train_id
WHERE a.station_id=(SELECT station_id FROM station WHERE station_code='SBC')
AND z.station_id=(SELECT station_id FROM station WHERE station_code='MAS')
AND a.stop_seq<z.stop_seq;

-- 4. Customer history index.
EXPLAIN FORMAT=JSON
SELECT pnr,status,total_fare,booking_time FROM booking
WHERE user_id=1 ORDER BY booking_time DESC LIMIT 10;
