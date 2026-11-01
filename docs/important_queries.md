<!-- Owner: Person A -->
# Essential Relational SQL Queries & Analytical Demonstrations

This document documents and explains the key advanced SQL queries implemented in `db/07_queries.sql`, demonstrating the full spectrum of relational calculus: multi-table JOINs, aggregation with `GROUP BY` and `HAVING`, correlated subqueries, common table expressions (CTEs), window functions, and full-text search.

---

## Query 1: Multi-Table Timetable Reconstruction (Inner Joins)

### Business Context:
When a passenger selects a train to inspect its intermediate stops, the system must reconstruct the full transit timetable in chronological halt sequence, joining train metadata with station geographical details.

```sql
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
```

### Relational Algebra Representation:
$$\pi_{\text{train\_num, train\_name, stop\_seq, stn\_code, arr, dep}} \left( \sigma_{\text{train\_number}='12658'} (Train \bowtie TrainStop \bowtie Station) \right)$$

---

## Query 2: High-Occupancy Revenue Aggregation (`GROUP BY` + `HAVING`)

### Business Context:
The Commercial Railway Manager generates operational revenue reports for scheduled runs, aggregating tickets, gross income, and average ticket values, filtering for high-demand journeys where passenger counts meet minimum thresholds.

```sql
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
```

---

## Query 3: Window Functions (`DENSE_RANK`, `SUM() OVER`)

### Business Context:
Computes running cumulative financial revenue partitioned per train over time and computes fare ranks without collapsing individual passenger booking rows into aggregate groups.

```sql
SELECT 
    b.booking_id,
    b.pnr,
    t.train_number,
    t.train_name,
    b.class_code,
    b.booking_type,
    b.total_fare,
    DENSE_RANK() OVER (
        PARTITION BY t.train_id 
        ORDER BY b.total_fare DESC
    ) AS fare_rank_within_train,
    SUM(b.total_fare) OVER (
        PARTITION BY t.train_id 
        ORDER BY b.booking_time
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_train_revenue,
    COUNT(p.passenger_id) OVER (
        PARTITION BY b.booking_id
    ) AS passenger_count
FROM booking b
INNER JOIN train_run tr ON b.run_id = tr.run_id
INNER JOIN train t ON tr.train_id = t.train_id
LEFT JOIN passenger p ON b.booking_id = p.booking_id
WHERE b.status = 'CONFIRMED'
ORDER BY t.train_number, b.booking_time;
```

---

## Query 4: Correlated Subquery with `EXISTS`

### Business Context:
Identifies major transit hubs that serve both as journey origins and destinations for Indian Railways operations.

```sql
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
```

---

## Query 5: Multi-Stage Common Table Expression (CTE) for Quota Breakdown

### Business Context:
Calculates occupancy percentages and seat availability across General vs Tatkal quotas per travel class.

```sql
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
```

---

## Query 6: MySQL Full-Text Search with Relevance Ranking

### Business Context:
Powers the station search autocomplete input on the homepage, allowing users to type station codes, names, or city fragments with natural language relevance scoring.

```sql
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
```
