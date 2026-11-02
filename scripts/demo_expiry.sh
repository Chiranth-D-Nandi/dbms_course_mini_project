#!/usr/bin/env bash
# Owner: Person B
# scripts/demo_expiry.sh: Demonstrate 8-Minute Seat Hold Expiration and Sweep
set -e

echo "======================================================================"
echo "  DEMO: Automated Seat Hold Expiration & Sweep Mechanism"
echo "======================================================================"

./.venv/bin/python -c "
import json
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()
conn = pymysql.connect(
    host=os.getenv('MYSQL_HOST', '127.0.0.1'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    user=os.getenv('MYSQL_ROOT_USER', 'root'),
    password=os.getenv('MYSQL_ROOT_PASSWORD', 'Chiranth@SQL'),
    database=os.getenv('MYSQL_DATABASE', 'tatkal_db'),
    autocommit=True
)
cur = conn.cursor()

print('--> Step 1: Placing candidate seat on HOLD via sp_book_tickets...')
cur.execute('SELECT run_id FROM train_run LIMIT 1')
run_id = cur.fetchone()[0]

cur.execute('SELECT ts1.station_id, ts2.station_id FROM train_stop ts1 JOIN train_stop ts2 ON ts1.train_id=ts2.train_id AND ts1.stop_seq=1 AND ts2.stop_seq=2 LIMIT 1')
src_id, dst_id = cur.fetchone()

cur.execute('SELECT user_id FROM app_user LIMIT 1')
user_id = cur.fetchone()[0]

p_json = json.dumps([{'name': 'Expiry Test', 'dob': '1990-01-01', 'gender': 'MALE', 'id_proof_type': 'AADHAAR', 'id_proof_no': '999988887777'}])
cur.execute('CALL sp_book_tickets(%s, %s, %s, %s, %s, %s, %s, @p_pnr, @p_status, @p_message)', [user_id, run_id, '3A', src_id, dst_id, 'GENERAL', p_json])
cur.execute('SELECT @p_pnr, @p_status')
pnr, b_status = cur.fetchone()
print(f'  [HOLD CREATED] PNR: {pnr}, Status: {b_status}')

cur.execute('SELECT rs.seat_status FROM passenger p JOIN run_seat rs ON p.run_id=rs.run_id AND p.seat_id=rs.seat_id WHERE p.pnr=%s', [pnr])
seat_status = cur.fetchone()[0]
print(f'  [SEAT STATUS] Seat is currently: {seat_status}')

print('--> Step 2: Simulating passage of 8-minute hold window (setting expires_at to past)...')
cur.execute('UPDATE booking SET expires_at = NOW() - INTERVAL 10 SECOND WHERE pnr = %s', [pnr])
cur.execute('UPDATE run_seat SET hold_expires_at = NOW() - INTERVAL 10 SECOND WHERE held_by_pnr = %s', [pnr])

print('--> Step 3: Triggering automated hold release sweep (CALL sp_release_expired_holds)...')
cur.execute('CALL sp_release_expired_holds(@p_count)')
cur.execute('SELECT @p_count')
released = cur.fetchone()[0]
print(f'  [SWEEPER EXECUTED] Released {released} expired booking holds.')

cur.execute('SELECT status FROM booking WHERE pnr = %s', [pnr])
final_b_status = cur.fetchone()[0]
print(f'  [FINAL BOOKING STATUS] Booking {pnr} is now: {final_b_status}')

cur.execute('SELECT rs.seat_status FROM passenger p JOIN run_seat rs ON p.run_id=rs.run_id AND p.seat_id=rs.seat_id WHERE p.pnr=%s', [pnr])
final_s_status = cur.fetchone()[0]
print(f'  [FINAL SEAT STATUS] Seat status returned to: {final_s_status}')

assert final_b_status == 'EXPIRED', 'Booking status must be EXPIRED'
assert final_s_status == 'AVAILABLE', 'Seat status must be AVAILABLE'
print('\n--> [SUCCESS] 8-Minute Seat Hold Expiration and Sweep verified perfectly!')
"
