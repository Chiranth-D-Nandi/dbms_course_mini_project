<!-- Owner: Person A -->
# Local MySQL 8.0 Setup & Database Security Guide

This guide details the procedure for configuring local MySQL 8.0, setting the Event Scheduler, and provisioning application database roles.

---

## 1. Prerequisites
- **MySQL 8.0+** Community Server installed on `localhost:3306`.
- Root user access to execute bootstrap and privilege assignments.

---

## 2. Event Scheduler Verification

The Tatkal booking system relies on recurring MySQL Events (`ev_release_expired_holds`) to automatically release seat holds that have timed out past 5 minutes.

To verify or enable the event scheduler in the active session:
```sql
-- Check current status
SELECT @@event_scheduler;

-- Enable dynamically
SET GLOBAL event_scheduler = ON;
```

### Persisting in Configuration (`my.ini` / `my.cnf`)
To ensure the event scheduler remains active across MySQL service restarts, add the following line under the `[mysqld]` section of your `my.ini` (Windows: `C:\ProgramData\MySQL\MySQL Server 8.0\my.ini`) or `my.cnf` (Linux/macOS: `/etc/mysql/my.cnf`):

```ini
[mysqld]
event_scheduler=ON
default-storage-engine=INNODB
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
```

---

## 3. Database Role Separation & Principle of Least Privilege

In compliance with enterprise database security standards, the application backend never connects as `root`. Two specialized roles are provisioned:

| User | Host | Privileges | Purpose |
| :--- | :--- | :--- | :--- |
| `app_rw` | `localhost`, `127.0.0.1` | `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `EXECUTE`, `SHOW VIEW` | Primary connection pool for Django REST backend. Executes stored procedures and interacts with transactional tables. |
| `app_ro` | `localhost`, `127.0.0.1` | `SELECT`, `SHOW VIEW` | Read-only reporting connection pool for data analytics, BI tools, and audit log inspection. |

---

## 4. Bootstrapping Database from Scratch

Run the following command in PowerShell / Bash to reset and provision the schema:

```bash
# Windows PowerShell
Get-Content db/00_reset.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p tatkal_db
Get-Content db/01_schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p tatkal_db
Get-Content db/03_procedures.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p tatkal_db
Get-Content db/04_triggers.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p tatkal_db
Get-Content db/05_views.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p tatkal_db
Get-Content db/06_events.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p tatkal_db
```

Or execute via the unified Django command:
```bash
python manage.py init_db
```
