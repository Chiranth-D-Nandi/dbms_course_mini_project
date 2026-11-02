# Owner: Person B
"""
Diagnostic runner for preflight health check.
Validates MySQL connectivity, table counts, and event scheduler status.
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

load_dotenv()

try:
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_ROOT_USER", "root"),
        password=os.getenv("MYSQL_ROOT_PASSWORD", "Chiranth@SQL"),
        database=os.getenv("MYSQL_DATABASE", "tatkal_db"),
    )
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = cur.fetchall()
    cur.execute("SHOW VARIABLES LIKE 'event_scheduler'")
    ev = cur.fetchone()[1]
    print(f"TABLE_COUNT:{len(tables)}|EVENT_SCHEDULER:{ev}")
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(1)
