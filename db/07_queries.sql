-- Read-only SQL demonstrations for the implemented schema.
USE tatkal_db;

-- 1. Three-table timetable join, exposed through a derived view.
SELECT train_number, train_name, stop_seq, station_code, station_name,
       arrival_time, departure_time, halt_duration_minutes, day_offset, distance_km
FROM v_train_route WHERE train_number='12658' ORDER BY stop_seq;

-- 2. GROUP BY / HAVING without multiplying ticket fares by passenger count.
WITH PassengerCount AS (
    SELECT pnr, COUNT(*) AS passengers FROM passenger GROUP BY pnr
)
SELECT t.train_number, t.train_name, tr.journey_date, b.class_code,
       COUNT(*) AS total_bookings, SUM(pc.passengers) AS total_passengers,
       SUM(b.total_fare) AS gross_fare, ROUND(AVG(b.total_fare),2) AS average_booking_fare
FROM booking b JOIN train_run tr ON tr.run_id=b.run_id
JOIN train t ON t.train_id=tr.train_id
JOIN PassengerCount pc ON pc.pnr=b.pnr
WHERE b.status='CONFIRMED'
GROUP BY t.train_number,t.train_name,tr.journey_date,b.class_code
HAVING SUM(pc.passengers)>=1 ORDER BY gross_fare DESC;

-- 3. Window functions over one row per booking.
SELECT b.pnr,t.train_number,b.total_fare,
       ROW_NUMBER() OVER (PARTITION BY t.train_id ORDER BY b.total_fare DESC,b.pnr) AS row_number_in_train,
       DENSE_RANK() OVER (PARTITION BY t.train_id ORDER BY b.total_fare DESC) AS fare_rank,
       SUM(b.total_fare) OVER (PARTITION BY t.train_id ORDER BY b.booking_time,b.pnr ROWS UNBOUNDED PRECEDING) AS cumulative_fare
FROM booking b JOIN train_run tr ON tr.run_id=b.run_id
JOIN train t ON t.train_id=tr.train_id
WHERE b.status='CONFIRMED' ORDER BY t.train_number,b.booking_time,b.pnr;

-- 4. Correlated EXISTS: stations serving as origins and destinations.
SELECT s.station_code,s.station_name,s.city FROM station s
WHERE EXISTS (SELECT 1 FROM train_stop a WHERE a.station_id=s.station_id AND a.stop_seq=1)
AND EXISTS (SELECT 1 FROM train_stop z WHERE z.station_id=s.station_id
    AND z.stop_seq=(SELECT MAX(last_stop.stop_seq) FROM train_stop last_stop WHERE last_stop.train_id=z.train_id))
ORDER BY s.station_code;

-- 5. CTE inventory aggregation by run, class and quota.
WITH Inventory AS (
    SELECT rs.run_id,c.class_code,rs.quota_type,COUNT(*) AS capacity,
           SUM(rs.seat_status='AVAILABLE') AS available_seats,
           SUM(rs.seat_status='HELD') AS held_seats,
           SUM(rs.seat_status='BOOKED') AS booked_seats
    FROM run_seat rs JOIN seat s ON s.seat_id=rs.seat_id
    JOIN coach c ON c.coach_id=s.coach_id GROUP BY rs.run_id,c.class_code,rs.quota_type
)
SELECT t.train_number,tr.journey_date,i.*,
       ROUND(100.0*i.booked_seats/NULLIF(i.capacity,0),2) AS occupancy_pct
FROM Inventory i JOIN train_run tr ON tr.run_id=i.run_id
JOIN train t ON t.train_id=tr.train_id ORDER BY tr.journey_date,t.train_number,i.class_code,i.quota_type;

-- 6. FULLTEXT ranking using the actual indexed columns.
SELECT station_code,station_name,city,
       MATCH(station_name,city) AGAINST('Bengaluru Junction' IN NATURAL LANGUAGE MODE) AS relevance
FROM station WHERE MATCH(station_name,city) AGAINST('Bengaluru Junction' IN NATURAL LANGUAGE MODE)
ORDER BY relevance DESC;
