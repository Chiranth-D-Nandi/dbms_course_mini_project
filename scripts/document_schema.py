"""Generate the data dictionary from MySQL and optionally execute the read-only SQL demos."""
import argparse
import os
from pathlib import Path
import sys
import pymysql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from booking_engine.management.commands.init_db import statements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-queries', action='store_true')
    args = parser.parse_args()
    load_dotenv(ROOT / '.env')
    database = os.getenv('MYSQL_DATABASE', 'tatkal_db')
    conn = pymysql.connect(host=os.getenv('MYSQL_HOST', '127.0.0.1'), port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('DB_APP_RO_USER', 'app_ro'), password=os.getenv('DB_APP_RO_PASSWORD', 'TatkalRo_SecurePass#2026'),
        database=database, charset='utf8mb4', autocommit=True, cursorclass=pymysql.cursors.DictCursor)
    lines = ['# Data dictionary', '', 'Generated from the configured MySQL schema. `db/01_schema.sql` and `db/02_alter_demo.sql` are the SQL source of truth.', '',
        'The booking primary key is `pnr`; `train_running_day`, `train_stop`, `run_seat` and `passenger` use composite primary keys. Only active passenger allocations retain run/seat references.', '']
    try:
        with conn.cursor() as c:
            c.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME", [database])
            tables = [row['TABLE_NAME'] for row in c.fetchall()]
            for table in tables:
                lines += [f'## `{table}`', '', '| Column | Type | Nullable | Key | Default | Extra |', '| --- | --- | --- | --- | --- | --- |']
                c.execute('SELECT COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_KEY,COLUMN_DEFAULT,EXTRA FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION', [database,table])
                for row in c.fetchall():
                    values = [str(row[k]) if row[k] is not None else 'NULL' for k in ('COLUMN_NAME','COLUMN_TYPE','IS_NULLABLE','COLUMN_KEY','COLUMN_DEFAULT','EXTRA')]
                    lines.append('| ' + ' | '.join('`'+v.replace('|','\\|')+'`' for v in values) + ' |')
                c.execute('SELECT CONSTRAINT_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY CONSTRAINT_NAME,ORDINAL_POSITION', [database,table])
                foreign = c.fetchall()
                if foreign:
                    lines += ['', 'Foreign keys:']
                    grouped = {}
                    for row in foreign:
                        grouped.setdefault(row['CONSTRAINT_NAME'], []).append(row)
                    for rows in grouped.values():
                        columns = ', '.join(r['COLUMN_NAME'] for r in rows)
                        target = ', '.join(r['REFERENCED_COLUMN_NAME'] for r in rows)
                        lines.append(f"- `({columns})` → `{rows[0]['REFERENCED_TABLE_NAME']}({target})`")
                c.execute('SELECT INDEX_NAME,COLUMN_NAME,NON_UNIQUE FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY INDEX_NAME,SEQ_IN_INDEX', [database,table])
                grouped = {}
                for row in c.fetchall():
                    grouped.setdefault(row['INDEX_NAME'], []).append(row)
                lines += ['', 'Indexes:']
                for name, rows in grouped.items():
                    columns = ', '.join(r['COLUMN_NAME'] for r in rows)
                    lines.append(f"- `{name}({columns})`" + (' (unique)' if not rows[0]['NON_UNIQUE'] else ''))
                lines.append('')
            (ROOT / 'docs' / 'data_dictionary.md').write_text('\n'.join(lines).rstrip()+'\n', encoding='utf-8')
            print(f'Documented {len(tables)} tables.')
            if args.check_queries:
                count = 0
                for name in ('07_queries.sql', '08_explain_demo.sql'):
                    for query in statements((ROOT / 'db' / name).read_text(encoding='utf-8')):
                        if query.strip().upper().startswith('USE '):
                            continue  # Already connected to MYSQL_DATABASE; never select another schema.
                        c.execute(query)
                        c.fetchall()
                        count += 1
                    print(f'Executed {name} successfully.')
                print(f'Verified {count} SQL query/plan demonstrations using the read-only account.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
