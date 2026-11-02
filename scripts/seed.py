# Owner: Person B
"""
scripts/seed.py: Comprehensive Realistic Database Seeder
Seeds ~30 stations, ~25 trains with realistic stops, running days, coaches, seats,
runs for the next 10 days, calls sp_generate_run_inventory, and seeds demo users & analytics bookings.
"""

import os
import sys
import datetime
import hashlib
from dotenv import load_dotenv
import pymysql

# Load environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_ROOT_USER = os.getenv("MYSQL_ROOT_USER", "root")
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "Chiranth@SQL")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "tatkal_db")

def hash_pw(password: str) -> str:
    # Django PBKDF2 compatible format or standard SHA256 test hash
    # For DRF compatibility, we store a PBKDF2 SHA256 hashed string
    salt = "tatkalprs2026"
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"pbkdf2_sha256$100000${salt}${h.hex()}"

def main():
    print("==> Connecting to MySQL database tatkal_db...")
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_ROOT_USER,
        password=MYSQL_ROOT_PASSWORD,
        database=MYSQL_DATABASE,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    cur = conn.cursor()

    print("==> Seeding Travel Classes (seat_class)...")
    classes = [
        ("SL", "Sleeper Class", False, 0.60, "11:00:00", 25, 30.00, 100.00, 200.00),
        ("3A", "AC 3 Tier", True, 1.80, "10:00:00", 20, 30.00, 300.00, 400.00),
        ("2A", "AC 2 Tier", True, 2.60, "10:00:00", 15, 30.00, 400.00, 500.00),
        ("1A", "AC First Class", True, 3.80, "10:00:00", 10, 30.00, 400.00, 500.00),
        ("CC", "AC Chair Car", True, 1.40, "10:00:00", 20, 30.00, 125.00, 225.00),
    ]
    cur.executemany(
        """
        INSERT INTO seat_class (class_code, class_name, is_ac, fare_per_km, tatkal_open_time,
                                tatkal_quota_pct, tatkal_surcharge_pct, tatkal_min_charge, tatkal_max_charge)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE class_name=VALUES(class_name)
        """,
        classes
    )

    print("==> Seeding 30 Major Railway Stations...")
    stations = [
        ("SBC", "KSR Bengaluru City", "Bengaluru", "Karnataka"),
        ("MAS", "Puratchi Thalaivar Dr. MGR Chennai Central", "Chennai", "Tamil Nadu"),
        ("NDLS", "New Delhi", "New Delhi", "Delhi"),
        ("MMCT", "Mumbai Central", "Mumbai", "Maharashtra"),
        ("HWH", "Howrah Junction", "Kolkata", "West Bengal"),
        ("BWT", "Bangarapet", "Kolar", "Karnataka"),
        ("KPD", "Katpadi Junction", "Vellore", "Tamil Nadu"),
        ("AJJ", "Arakkonam Junction", "Ranipet", "Tamil Nadu"),
        ("PER", "Perambur", "Chennai", "Tamil Nadu"),
        ("CNB", "Kanpur Central", "Kanpur", "Uttar Pradesh"),
        ("PRYJ", "Prayagraj Junction", "Prayagraj", "Uttar Pradesh"),
        ("DDU", "Pt. Deen Dayal Upadhyaya Junction", "Mughalsarai", "Uttar Pradesh"),
        ("BSL", "Bhusaval Junction", "Bhusawal", "Maharashtra"),
        ("BRC", "Vadodara Junction", "Vadodara", "Gujarat"),
        ("ST", "Surat", "Surat", "Gujarat"),
        ("PUNE", "Pune Junction", "Pune", "Maharashtra"),
        ("SC", "Secunderabad Junction", "Hyderabad", "Telangana"),
        ("BZA", "Vijayawada Junction", "Vijayawada", "Andhra Pradesh"),
        ("TVC", "Thiruvananthapuram Central", "Thiruvananthapuram", "Kerala"),
        ("ERS", "Ernakulam Junction", "Kochi", "Kerala"),
        ("CBE", "Coimbatore Junction", "Coimbatore", "Tamil Nadu"),
        ("MDU", "Madurai Junction", "Madurai", "Tamil Nadu"),
        ("GHY", "Guwahati", "Guwahati", "Assam"),
        ("PNBE", "Patna Junction", "Patna", "Bihar"),
        ("LKO", "Lucknow Charbagh", "Lucknow", "Uttar Pradesh"),
        ("BPL", "Bhopal Junction", "Bhopal", "Madhya Pradesh"),
        ("NGP", "Nagpur Junction", "Nagpur", "Maharashtra"),
        ("R", "Raipur Junction", "Raipur", "Chhattisgarh"),
        ("VSKP", "Visakhapatnam Junction", "Visakhapatnam", "Andhra Pradesh"),
        ("ADI", "Ahmedabad Junction", "Ahmedabad", "Gujarat"),
    ]
    cur.executemany(
        """
        INSERT INTO station (station_code, station_name, city, state)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE station_name=VALUES(station_name)
        """,
        stations
    )

    # Station ID lookup
    cur.execute("SELECT station_code, station_id FROM station")
    st_map = {r["station_code"]: r["station_id"] for r in cur.fetchall()}

    print("==> Seeding 25 Express, Superfast & Rajdhani Trains...")
    trains_data = [
        ("12658", "Bengaluru - Chennai Mail", "SUPERFAST", [
            ("SBC", None, "22:40:00", 0, 0),
            ("BWT", "23:43:00", "23:45:00", 0, 70),
            ("KPD", "02:08:00", "02:10:00", 1, 232),
            ("AJJ", "03:03:00", "03:05:00", 1, 293),
            ("PER", "03:53:00", "03:55:00", 1, 356),
            ("MAS", "04:15:00", None, 1, 362)
        ]),
        ("12657", "Chennai - Bengaluru Mail", "SUPERFAST", [
            ("MAS", None, "22:50:00", 0, 0),
            ("PER", "23:03:00", "23:05:00", 0, 6),
            ("AJJ", "23:53:00", "23:55:00", 0, 69),
            ("KPD", "00:48:00", "00:50:00", 1, 130),
            ("BWT", "02:58:00", "03:00:00", 1, 292),
            ("SBC", "04:30:00", None, 1, 362)
        ]),
        ("12007", "Chennai - Mysuru Shatabdi Express", "SHATABDI", [
            ("MAS", None, "06:00:00", 0, 0),
            ("KPD", "07:38:00", "07:40:00", 0, 130),
            ("SBC", "10:45:00", "10:50:00", 0, 362)
        ]),
        ("12008", "Mysuru - Chennai Shatabdi Express", "SHATABDI", [
            ("SBC", None, "16:20:00", 0, 0),
            ("KPD", "19:23:00", "19:25:00", 0, 232),
            ("MAS", "21:30:00", None, 0, 362)
        ]),
        ("12951", "Mumbai Rajdhani Express", "RAJDHANI", [
            ("MMCT", None, "17:00:00", 0, 0),
            ("ST", "19:23:00", "19:28:00", 0, 263),
            ("BRC", "21:06:00", "21:16:00", 0, 392),
            ("NDLS", "08:32:00", None, 1, 1384)
        ]),
        ("12952", "New Delhi - Mumbai Rajdhani Express", "RAJDHANI", [
            ("NDLS", None, "16:55:00", 0, 0),
            ("BRC", "03:40:00", "03:50:00", 1, 992),
            ("ST", "05:13:00", "05:18:00", 1, 1121),
            ("MMCT", "08:35:00", None, 1, 1384)
        ]),
        ("12301", "Howrah Rajdhani Express", "RAJDHANI", [
            ("HWH", None, "16:50:00", 0, 0),
            ("DDU", "00:45:00", "00:55:00", 1, 672),
            ("PRYJ", "02:33:00", "02:35:00", 1, 825),
            ("CNB", "04:40:00", "04:45:00", 1, 1019),
            ("NDLS", "10:05:00", None, 1, 1451)
        ]),
        ("12302", "New Delhi - Howrah Rajdhani Express", "RAJDHANI", [
            ("NDLS", None, "16:50:00", 0, 0),
            ("CNB", "21:32:00", "21:37:00", 0, 432),
            ("PRYJ", "23:43:00", "23:45:00", 0, 626),
            ("DDU", "01:37:00", "01:47:00", 1, 779),
            ("HWH", "09:55:00", None, 1, 1451)
        ]),
        ("12627", "Karnataka Express", "SUPERFAST", [
            ("SBC", None, "19:20:00", 0, 0),
            ("BWT", "20:28:00", "20:30:00", 0, 70),
            ("BPL", "16:45:00", "16:55:00", 1, 1718),
            ("NDLS", "09:00:00", None, 2, 2408)
        ]),
        ("12628", "New Delhi - Bengaluru Karnataka Express", "SUPERFAST", [
            ("NDLS", None, "20:20:00", 0, 0),
            ("BPL", "10:45:00", "10:55:00", 1, 690),
            ("BWT", "10:18:00", "10:20:00", 2, 2338),
            ("SBC", "12:00:00", None, 2, 2408)
        ]),
        ("12295", "Sanghamitra Superfast Express", "SUPERFAST", [
            ("SBC", None, "09:00:00", 0, 0),
            ("KPD", "13:00:00", "13:05:00", 0, 232),
            ("BZA", "21:40:00", "21:50:00", 0, 668),
            ("DDU", "17:45:00", "17:55:00", 1, 2480),
            ("PNBE", "23:55:00", None, 1, 2698)
        ]),
        ("12296", "Danapur - Bengaluru Sanghamitra Express", "SUPERFAST", [
            ("PNBE", None, "20:15:00", 0, 0),
            ("DDU", "23:15:00", "23:25:00", 0, 218),
            ("BZA", "18:50:00", "19:00:00", 1, 2030),
            ("KPD", "03:50:00", "03:55:00", 2, 2466),
            ("SBC", "08:10:00", None, 2, 2698)
        ]),
        ("12137", "Punjab Mail", "MAIL", [
            ("MMCT", None, "19:35:00", 0, 0),
            ("BSL", "02:05:00", "02:10:00", 1, 444),
            ("BPL", "09:40:00", "09:45:00", 1, 843),
            ("NDLS", "21:30:00", None, 1, 1544)
        ]),
        ("12138", "New Delhi - Mumbai Punjab Mail", "MAIL", [
            ("NDLS", None, "05:15:00", 0, 0),
            ("BPL", "16:30:00", "16:35:00", 0, 701),
            ("BSL", "23:35:00", "23:40:00", 0, 1100),
            ("MMCT", "07:35:00", None, 1, 1544)
        ]),
        ("12625", "Kerala Express", "SUPERFAST", [
            ("TVC", None, "12:30:00", 0, 0),
            ("ERS", "16:20:00", "16:25:00", 0, 206),
            ("CBE", "20:55:00", "21:00:00", 0, 448),
            ("BZA", "10:15:00", "10:25:00", 1, 1378),
            ("NDLS", "13:15:00", None, 2, 3036)
        ]),
        ("12626", "New Delhi - Thiruvananthapuram Kerala Express", "SUPERFAST", [
            ("NDLS", None, "20:10:00", 0, 0),
            ("BZA", "22:10:00", "22:20:00", 1, 1658),
            ("CBE", "10:25:00", "10:30:00", 2, 2588),
            ("ERS", "15:25:00", "15:30:00", 2, 2830),
            ("TVC", "21:50:00", None, 2, 3036)
        ]),
        ("12839", "Howrah - Chennai Mail", "MAIL", [
            ("HWH", None, "23:55:00", 0, 0),
            ("VSKP", "13:50:00", "14:10:00", 1, 882),
            ("BZA", "20:00:00", "20:15:00", 1, 1232),
            ("MAS", "03:45:00", None, 2, 1662)
        ]),
        ("12840", "Chennai - Howrah Mail", "MAIL", [
            ("MAS", None, "19:00:00", 0, 0),
            ("BZA", "01:50:00", "02:05:00", 1, 430),
            ("VSKP", "07:50:00", "08:10:00", 1, 780),
            ("HWH", "23:00:00", None, 1, 1662)
        ]),
        ("12615", "Grand Trunk Express", "SUPERFAST", [
            ("MAS", None, "18:50:00", 0, 0),
            ("BZA", "00:50:00", "01:00:00", 1, 430),
            ("NGP", "11:30:00", "11:35:00", 1, 1092),
            ("BPL", "18:40:00", "18:45:00", 1, 1482),
            ("NDLS", "06:35:00", None, 2, 2182)
        ]),
        ("12616", "New Delhi - Chennai Grand Trunk Express", "SUPERFAST", [
            ("NDLS", None, "16:10:00", 0, 0),
            ("BPL", "03:15:00", "03:20:00", 1, 700),
            ("NGP", "10:15:00", "10:20:00", 1, 1090),
            ("BZA", "21:40:00", "21:50:00", 1, 1752),
            ("MAS", "04:30:00", None, 2, 2182)
        ]),
        ("12050", "Gatimaan Superfast Express", "SHATABDI", [
            ("NDLS", None, "08:10:00", 0, 0),
            ("CNB", "13:30:00", None, 0, 440)
        ]),
        ("12049", "Kanpur - New Delhi Gatimaan Express", "SHATABDI", [
            ("CNB", None, "15:05:00", 0, 0),
            ("NDLS", "20:45:00", None, 0, 440)
        ]),
        ("12932", "Ahmedabad - Mumbai Double Decker", "SUPERFAST", [
            ("ADI", None, "06:00:00", 0, 0),
            ("BRC", "07:23:00", "07:28:00", 0, 100),
            ("ST", "08:52:00", "08:57:00", 0, 230),
            ("MMCT", "13:05:00", None, 0, 492)
        ]),
        ("12931", "Mumbai - Ahmedabad Double Decker", "SUPERFAST", [
            ("MMCT", None, "14:30:00", 0, 0),
            ("ST", "18:05:00", "18:10:00", 0, 262),
            ("BRC", "19:40:00", "19:45:00", 0, 392),
            ("ADI", "21:25:00", None, 0, 492)
        ]),
        ("12723", "Telangana Express", "SUPERFAST", [
            ("SC", None, "06:00:00", 0, 0),
            ("NGP", "15:20:00", "15:25:00", 0, 575),
            ("BPL", "23:40:00", "23:45:00", 0, 965),
            ("NDLS", "09:05:00", None, 1, 1665)
        ]),
    ]

    for t_num, t_name, t_type, stops in trains_data:
        cur.execute(
            """
            INSERT INTO train (train_number, train_name, train_type, is_active)
            VALUES (%s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE train_name=VALUES(train_name)
            """,
            (t_num, t_name, t_type)
        )
        cur.execute("SELECT train_id FROM train WHERE train_number = %s", (t_num,))
        train_id = cur.fetchone()["train_id"]

        # Running days (0-6 daily)
        running_days = [(train_id, d) for d in range(7)]
        cur.executemany(
            """
            INSERT INTO train_running_day (train_id, day_of_week)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE day_of_week=VALUES(day_of_week)
            """,
            running_days
        )

        # Train stops
        stop_seq = 1
        for st_code, arr, dep, day_off, dist in stops:
            st_id = st_map[st_code]
            cur.execute(
                """
                INSERT INTO train_stop (train_id, stop_seq, station_id, arrival_time, departure_time, day_offset, distance_km)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE arrival_time=VALUES(arrival_time), departure_time=VALUES(departure_time)
                """,
                (train_id, stop_seq, st_id, arr, dep, day_off, dist)
            )
            stop_seq += 1

        # Train coaches composition
        # Standard: 2 x 3A (B1, B2), 1 x 2A (A1), 2 x SL (S1, S2)
        coach_configs = [
            ("3A", "B1", 16),
            ("3A", "B2", 16),
            ("2A", "A1", 12),
            ("SL", "S1", 20),
            ("SL", "S2", 20),
        ]
        if t_type == "SHATABDI":
            coach_configs = [
                ("CC", "C1", 20),
                ("CC", "C2", 20),
                ("1A", "E1", 10),
            ]
        elif t_type == "RAJDHANI":
            coach_configs = [
                ("1A", "H1", 10),
                ("2A", "A1", 16),
                ("3A", "B1", 24),
                ("3A", "B2", 24),
            ]

        for cls_code, c_num, seat_count in coach_configs:
            cur.execute(
                """
                INSERT INTO coach (train_id, class_code, coach_number)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE class_code=VALUES(class_code)
                """,
                (train_id, cls_code, c_num)
            )
            cur.execute("SELECT coach_id FROM coach WHERE train_id = %s AND coach_number = %s", (train_id, c_num))
            coach_id = cur.fetchone()["coach_id"]

            # Physical Seats
            berth_pattern = ['LB', 'MB', 'UB', 'LB', 'MB', 'UB', 'SL', 'SU']
            if cls_code == 'CC':
                berth_pattern = ['WS', 'MS', 'AS', 'AS', 'MS', 'WS']

            seat_rows = []
            for s_num in range(1, seat_count + 1):
                b_type = berth_pattern[(s_num - 1) % len(berth_pattern)]
                seat_rows.append((coach_id, s_num, b_type))

            cur.executemany(
                """
                INSERT INTO seat (coach_id, seat_number, berth_type)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE berth_type=VALUES(berth_type)
                """,
                seat_rows
            )

    print("==> Generating Train Runs for Next 10 Days & Running sp_generate_run_inventory...")
    today = datetime.date.today()
    cur.execute("SELECT train_id FROM train")
    all_train_ids = [r["train_id"] for r in cur.fetchall()]

    for i in range(10):
        j_date = today + datetime.timedelta(days=i)
        for t_id in all_train_ids:
            cur.execute(
                """
                INSERT INTO train_run (train_id, journey_date, run_status)
                VALUES (%s, %s, 'SCHEDULED')
                ON DUPLICATE KEY UPDATE run_status='SCHEDULED'
                """,
                (t_id, j_date)
            )
            cur.execute("SELECT run_id FROM train_run WHERE train_id = %s AND journey_date = %s", (t_id, j_date))
            run_id = cur.fetchone()["run_id"]

            # Call Stored Procedure to populate inventory
            cur.execute("CALL sp_generate_run_inventory(%s)", (run_id,))

    print("==> Seeding Demo Users (ADMIN and CUSTOMER roles)...")
    users = [
        ("Chiranth", "Nandi", "chiranth@example.com", "9876543210", hash_pw("Customer@123"), "CUSTOMER"),
        ("Jashruth", "K A", "jashruth@example.com", "9876543211", hash_pw("Customer@123"), "CUSTOMER"),
        ("PRS", "Admin", "admin@tatkal.com", "9876543212", hash_pw("Admin@123"), "ADMIN"),
        ("Ramesh", "Kumar", "ramesh@example.com", "9876543213", hash_pw("Customer@123"), "CUSTOMER"),
        ("Priya", "Sharma", "priya@example.com", "9876543214", hash_pw("Customer@123"), "CUSTOMER"),
        ("Anand", "Verma", "anand@example.com", "9876543215", hash_pw("Customer@123"), "CUSTOMER"),
    ]
    cur.executemany(
        """
        INSERT INTO app_user (first_name, last_name, email, phone, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        ON DUPLICATE KEY UPDATE role=VALUES(role), password_hash=VALUES(password_hash)
        """,
        users
    )

    print("==> Seeding Historical Bookings for Analytical Views & Reports...")
    # Seed 5 sample confirmed bookings with payments and 1 cancellation
    cur.execute("SELECT user_id FROM app_user WHERE email = 'chiranth@example.com'")
    user1_id = cur.fetchone()["user_id"]
    cur.execute("SELECT user_id FROM app_user WHERE email = 'jashruth@example.com'")
    user2_id = cur.fetchone()["user_id"]

    cur.execute("SELECT run_id FROM train_run LIMIT 1")
    first_run_id = cur.fetchone()["run_id"]

    sbc_id = st_map["SBC"]
    mas_id = st_map["MAS"]

    # Historical Booking 1: General Confirmed
    cur.execute(
        """
        INSERT INTO booking (user_id, run_id, source_station_id, dest_station_id, class_code, booking_type, status, booking_time, expires_at, total_fare)
        VALUES (%s, %s, %s, %s, '3A', 'GENERAL', 'CONFIRMED', NOW() - INTERVAL 2 DAY, NULL, 1360.00)
        """,
        (user1_id, first_run_id, sbc_id, mas_id)
    )
    pnr1 = cur.lastrowid
    cur.execute(
        """
        INSERT INTO payment (pnr, amount, method, status, txn_ref, idempotency_key, created_at)
        VALUES (%s, 1360.00, 'UPI', 'SUCCESS', 'TXN_SEED_HIST_001', 'IDEMP_SEED_001', NOW() - INTERVAL 2 DAY)
        """,
        (pnr1,)
    )

    # Historical Booking 2: Tatkal Confirmed
    cur.execute(
        """
        INSERT INTO booking (user_id, run_id, source_station_id, dest_station_id, class_code, booking_type, status, booking_time, expires_at, total_fare)
        VALUES (%s, %s, %s, %s, '3A', 'TATKAL', 'CONFIRMED', NOW() - INTERVAL 1 DAY, NULL, 1760.00)
        """,
        (user2_id, first_run_id, sbc_id, mas_id)
    )
    pnr2 = cur.lastrowid
    cur.execute(
        """
        INSERT INTO payment (pnr, amount, method, status, txn_ref, idempotency_key, created_at)
        VALUES (%s, 1760.00, 'CARD', 'SUCCESS', 'TXN_SEED_HIST_002', 'IDEMP_SEED_002', NOW() - INTERVAL 1 DAY)
        """,
        (pnr2,)
    )

    # Historical Booking 3: Cancelled
    cur.execute(
        """
        INSERT INTO booking (user_id, run_id, source_station_id, dest_station_id, class_code, booking_type, status, booking_time, expires_at, total_fare)
        VALUES (%s, %s, %s, %s, 'SL', 'GENERAL', 'CANCELLED', NOW() - INTERVAL 3 DAY, NULL, 480.00)
        """,
        (user1_id, first_run_id, sbc_id, mas_id)
    )
    pnr3 = cur.lastrowid
    cur.execute(
        """
        INSERT INTO cancellation (pnr, cancelled_at, refund_amount, reason)
        VALUES (%s, NOW() - INTERVAL 2 DAY, 432.00, 'Customer requested voluntary cancellation')
        """,
        (pnr3,)
    )

    cur.close()
    conn.close()
    print("==> Database Seeding Finished Successfully!")

if __name__ == "__main__":
    main()
