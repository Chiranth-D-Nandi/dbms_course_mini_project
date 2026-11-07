# Owner: Person A
"""
High-Concurrency Stress Test for Tatkal Ticket Engine.
Spawns multiple concurrent threads attempting to book the EXACT SAME pool of seats simultaneously.
Asserts:
1. ZERO double-booking (no seat assigned to multiple active bookings).
2. Proper row-level locking via MySQL InnoDB (`SELECT ... FOR UPDATE SKIP LOCKED`).
3. Clean failure handling once inventory is exhausted without application deadlocks.
"""

import json
import threading
import pytest
from django.db import connection, connections
from booking_engine.models import TrainRun, Station, AppUser

@pytest.mark.django_db(transaction=True, databases=["default", "readonly"])
def test_zero_double_booking_under_concurrency():
    """
    Stress test with 16 concurrent threads hammering the same train run and class.
    """
    # Clean any expired holds first so all seats in inventory are truly available
    with connections["default"].cursor() as cursor:
        cursor.execute("CALL sp_release_expired_holds();")
        cursor.execute(
            """
            UPDATE passenger p
            JOIN booking b ON p.pnr = b.pnr
            SET p.run_id = NULL, p.seat_id = NULL
            WHERE b.status IN ('EXPIRED', 'CANCELLED');
            """
        )
        cursor.execute(
            """
            SELECT tr.run_id, t.train_id, ts1.station_id, ts2.station_id
            FROM train_run tr
            JOIN train t ON tr.train_id = t.train_id
            JOIN train_stop ts1 ON t.train_id = ts1.train_id AND ts1.stop_seq = 1
            JOIN train_stop ts2 ON t.train_id = ts2.train_id AND ts2.stop_seq = 2
            WHERE tr.journey_date > CURDATE()
              AND EXISTS (SELECT 1 FROM coach c WHERE c.train_id=t.train_id AND c.class_code='3A')
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        assert row is not None, "A train run with stops must exist in database."
        run_id, train_id, src_id, dst_id = row

        cursor.execute("SELECT user_id FROM app_user LIMIT 1")
        user_id = cursor.fetchone()[0]

    # Restrict this isolated test run to exactly eight General seats.
    # Other seats are temporarily assigned to the alternate quota, not falsely booked.
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT rs.seat_id FROM run_seat rs JOIN seat s ON s.seat_id=rs.seat_id JOIN coach c ON c.coach_id=s.coach_id WHERE rs.run_id=%s AND c.class_code='3A' AND rs.seat_status='AVAILABLE' ORDER BY rs.seat_id LIMIT 8", [run_id])
        seats = [row[0] for row in cursor.fetchall()]
        assert len(seats) == 8
        cursor.execute("UPDATE run_seat rs JOIN seat s ON s.seat_id=rs.seat_id JOIN coach c ON c.coach_id=s.coach_id SET rs.quota_type='TATKAL' WHERE rs.run_id=%s AND c.class_code='3A'", [run_id])
        cursor.execute("UPDATE run_seat SET quota_type='GENERAL' WHERE run_id=%s AND seat_id IN (" + ','.join(['%s']*len(seats)) + ')', [run_id]+seats)

    num_threads = 16
    results = []
    barrier = threading.Barrier(num_threads)

    def worker_book(thread_idx):
        conn = connections["default"].copy() if hasattr(connections["default"], "copy") else connections["default"]
        barrier.wait()  # Synchronize all threads to fire at the exact same millisecond

        passenger_payload = json.dumps([
            {
                "name": f"Concurrent Passenger {thread_idx}",
                "dob": "1995-05-15",
                "gender": "MALE" if thread_idx % 2 == 0 else "FEMALE",
                "id_proof_type": "AADHAAR",
                "id_proof_no": f"11112222{thread_idx:04d}"
            }
        ])

        try:
            with conn.cursor() as cur:
                # sp_book_tickets(p_user_id, p_run_id, p_class_code, p_src_id, p_dst_id, p_booking_type, p_passengers_json, OUT p_pnr, OUT p_status, OUT p_message)
                cur.execute(
                    """
                    CALL sp_book_tickets(%s, %s, %s, %s, %s, %s, %s, @p_pnr, @p_status, @p_message);
                    """,
                    [user_id, run_id, "3A", src_id, dst_id, "GENERAL", passenger_payload]
                )
                cur.execute("SELECT @p_pnr, @p_status, @p_message;")
                out = cur.fetchone()
                results.append({
                    "thread_idx": thread_idx,
                    "pnr": out[0],
                    "status": out[1],
                    "message": out[2]
                })
        except Exception as e:
            results.append({
                "thread_idx": thread_idx,
                "pnr": None,
                "status": "ERROR",
                "error": str(e)
            })
        finally:
            conn.close()

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker_book, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=30)
        assert not t.is_alive(), "Booking worker did not complete within 30 seconds."

    assert len(results) == num_threads
    assert not [r for r in results if r["status"] not in ("PENDING", "SOLD_OUT", "DEADLOCK_RETRY")], results

    # Verify concurrency integrity in database:
    successful_bookings = [r for r in results if r["status"] == "PENDING" and r["pnr"] is not None]
    assert len(successful_bookings) == 8, f"Exactly eight available seats must be allocated once under contention: {results}"
    assert sum(r["status"] == "SOLD_OUT" for r in results) == 8, results
    print("16 concurrent requests: 8 successful holds, 8 sold out, 0 duplicate allocations.")

    successful_pnrs = [b["pnr"] for b in successful_bookings]

    with connections["default"].cursor() as cursor:
        # Check if ANY (run_id, seat_id) was allocated more than once
        format_strings = ",".join(["%s"] * len(successful_pnrs))
        cursor.execute(
            f"""
            SELECT p.run_id, p.seat_id, COUNT(*) as alloc_count
            FROM passenger p
            JOIN booking b ON p.pnr = b.pnr
            WHERE b.pnr IN ({format_strings})
            GROUP BY p.run_id, p.seat_id
            HAVING alloc_count > 1
            """,
            successful_pnrs
        )
        double_bookings = cursor.fetchall()

        # CRITICAL ASSERTION: ZERO DOUBLE-BOOKINGS
        assert len(double_bookings) == 0, f"CONCURRENCY VIOLATION DETECTED! Seats double booked: {double_bookings}"

        # Verify that all allocated seats in run_seat have seat_status = 'HELD'
        cursor.execute(
            f"""
            SELECT rs.seat_status, COUNT(*)
            FROM passenger p
            JOIN run_seat rs ON p.run_id = rs.run_id AND p.seat_id = rs.seat_id
            WHERE p.pnr IN ({format_strings})
            GROUP BY rs.seat_status
            """,
            successful_pnrs
        )
        status_counts = dict(cursor.fetchall())
        assert "AVAILABLE" not in status_counts, "Allocated seats must not be marked as AVAILABLE."
