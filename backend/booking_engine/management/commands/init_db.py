# Owner: Person A
"""
Django Management Command: init_db
Executes RAW SQL files in order from the db/ directory to provision:
00_reset.sql, 01_schema.sql, 02_alter_demo.sql, 03_procedures.sql,
04_triggers.sql, 05_views.sql, and 06_events.sql.
"""

import os
import subprocess
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
import pymysql

class Command(BaseCommand):
    help = "Initializes MySQL database objects by running raw SQL scripts in db/ sequentially."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-reset",
            action="store_true",
            help="Skip running 00_reset.sql",
        )

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        db_dir = base_dir / "db"

        sql_files = [
            "00_reset.sql",
            "01_schema.sql",
            "02_alter_demo.sql",
            "03_procedures.sql",
            "04_triggers.sql",
            "05_views.sql",
            "06_events.sql",
        ]

        if options["skip_reset"]:
            sql_files = sql_files[1:]

        mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1")
        mysql_port = os.getenv("MYSQL_PORT", "3306")
        root_user = os.getenv("MYSQL_ROOT_USER", "root")
        root_password = os.getenv("MYSQL_ROOT_PASSWORD", "Chiranth@SQL")
        database = os.getenv("MYSQL_DATABASE", "tatkal_db")

        mysql_bin = shutil.which("mysql")

        self.stdout.write(self.style.NOTICE("==> Starting database initialization..."))

        for sql_file in sql_files:
            file_path = db_dir / sql_file
            if not file_path.exists():
                self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
                continue

            self.stdout.write(self.style.NOTICE(f"--> Executing {sql_file}..."))

            if mysql_bin:
                # Use mysql CLI to natively handle DELIMITER and multi-statement SQL
                cmd = [
                    mysql_bin,
                    "-h", mysql_host,
                    "-P", mysql_port,
                    "-u", root_user,
                    f"-p{root_password}",
                    "--default-character-set=utf8mb4",
                ]
                if sql_file != "00_reset.sql":
                    cmd.append(database)

                with open(file_path, "r", encoding="utf-8") as f:
                    result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)

                if result.returncode != 0:
                    self.stderr.write(self.style.ERROR(f"Error in {sql_file}: {result.stderr}"))
                    raise Exception(f"Failed to execute {sql_file}: {result.stderr}")
                else:
                    self.stdout.write(self.style.SUCCESS(f"  [OK] Successfully executed {sql_file}"))
            else:
                # Fallback pymysql runner
                conn = pymysql.connect(
                    host=mysql_host,
                    port=int(mysql_port),
                    user=root_user,
                    password=root_password,
                    database=None if sql_file == "00_reset.sql" else database,
                    autocommit=True,
                    client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
                )
                with conn.cursor() as cur:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # Strip DELIMITER commands for pymysql
                    statements = []
                    current = []
                    delimiter = ";"
                    for line in content.splitlines():
                        stripped = line.strip()
                        if stripped.upper().startswith("DELIMITER"):
                            delimiter = stripped.split()[1]
                            continue
                        if stripped.endswith(delimiter):
                            current.append(stripped[:-len(delimiter)])
                            stmt = "\n".join(current).strip()
                            if stmt:
                                statements.append(stmt)
                            current = []
                        else:
                            current.append(line)
                    if current and "\n".join(current).strip():
                        statements.append("\n".join(current).strip())

                    for stmt in statements:
                        if stmt:
                            cur.execute(stmt)
                conn.close()
                self.stdout.write(self.style.SUCCESS(f"  [OK] Successfully executed {sql_file}"))

        self.stdout.write(self.style.SUCCESS("==> Database initialization completed successfully!"))
