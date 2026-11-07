"""Provision a selected database; resetting existing tables requires --reset."""
import os
import re
from pathlib import Path
import pymysql
from django.core.management.base import BaseCommand, CommandError


def statements(content):
    delimiter = ";"
    pending = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split()[1]
            continue
        line = re.sub(r";\s*--.*$", ";", line)
        pending.append(line)
        if line.rstrip().endswith(delimiter):
            yield "\n".join(pending).rstrip()[:-len(delimiter)]
            pending = []
    if pending:
        yield "\n".join(pending)


class Command(BaseCommand):
    help = "Initialize MYSQL_DATABASE without touching any other database."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Explicitly replace existing project tables and data.")
        parser.add_argument("--skip-reset", action="store_true", help="Compatibility flag: refuses existing project tables.")
        parser.add_argument("--if-empty", action="store_true", help="Keep existing tables and return successfully.")
        parser.add_argument("--update-objects", action="store_true", help="Refresh routines, triggers, views and events without changing table data.")

    def handle(self, *args, **options):
        database = os.getenv("MYSQL_DATABASE", "tatkal_db")
        rw = os.getenv("DB_APP_RW_USER", "app_rw")
        ro = os.getenv("DB_APP_RO_USER", "app_ro")
        for value in (database, rw, ro):
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value):
                raise CommandError("Database and account names must contain only letters, numbers, and underscores.")
        conn = pymysql.connect(host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")), user=os.getenv("MYSQL_ROOT_USER", "root"),
            password=os.getenv("MYSQL_ROOT_PASSWORD", ""), autocommit=True, charset="utf8mb4", init_command="SET time_zone = '+05:30'")
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_type='BASE TABLE'", [database])
                existing_tables = cur.fetchone()[0]
                if options["update_objects"] and not existing_tables:
                    raise CommandError("Initialize the empty database before updating objects.")
                if existing_tables and not options["reset"] and not options["update_objects"]:
                    if options["if_empty"]:
                        self.stdout.write("Existing project schema preserved.")
                        return
                    raise CommandError("Database contains tables. Choose a new MYSQL_DATABASE or explicitly pass --reset to erase project data.")
                root = Path(__file__).resolve().parents[4]
                files = ("00_reset.sql", "01_schema.sql", "02_alter_demo.sql", "03_procedures.sql", "04_triggers.sql", "05_views.sql", "06_events.sql")
                for name in (files[3:] if options["update_objects"] else files):
                    content = (root / "db" / name).read_text(encoding="utf-8")
                    content = content.replace("tatkal_db", database)
                    content = content.replace("'app_rw'", "'" + rw + "'").replace("'app_ro'", "'" + ro + "'")
                    content = content.replace("TatkalRw_SecurePass#2026", pymysql.converters.escape_string(os.getenv("DB_APP_RW_PASSWORD", "TatkalRw_SecurePass#2026")))
                    content = content.replace("TatkalRo_SecurePass#2026", pymysql.converters.escape_string(os.getenv("DB_APP_RO_PASSWORD", "TatkalRo_SecurePass#2026")))
                    for sql in statements(content):
                        cur.execute(sql)
                        while cur.nextset():
                            pass
                    self.stdout.write(self.style.SUCCESS("Applied " + name))
                # Earlier installations granted the read-only account every routine.
                # A DEFINER procedure could then write despite table-level SELECT-only access.
                for host in ("localhost", "127.0.0.1"):
                    cur.execute(f"SHOW GRANTS FOR '{ro}'@'{host}'")
                    grants = [row[0] for row in cur.fetchall()]
                    if any(f"ON `{database}`.*" in grant and "EXECUTE" in grant.split(" ON ")[0] for grant in grants):
                        cur.execute(f"REVOKE EXECUTE ON `{database}`.* FROM '{ro}'@'{host}'")
        finally:
            conn.close()
