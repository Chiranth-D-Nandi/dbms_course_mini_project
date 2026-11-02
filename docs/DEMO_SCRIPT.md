<!-- Owner: Person B -->
# Professor Viva Presentation & Evaluation Demo Script

**Project Title**: Tatkal High-Concurrency Train Booking System  
**Institution**: PES University — DBMS Experiential Learning Project (Level 3)  
**Team**:
- **Chiranth D Nandi (Person A)** — Data & Backend Architecture (`PES2UG24AM048`)
- **Jashruth K A (Person B)** — User Experience, Ops & Verification (`PES2UG24AM069`)

---

## 1. Five-Minute Presentation Outline

### Minute 1: System Overview & Problem Statement
- **Speaker**: Chiranth (Person A)
- **Key Points**:
  - The IRCTC Tatkal booking problem: extreme concurrency at 10:00:00 AM where thousands compete for dozens of seats.
  - Why standard web frameworks double-book: application-level checks allow race conditions between read and write.
  - Solution: In-database concurrency engine utilizing MySQL 8.0 InnoDB `SELECT ... FOR UPDATE SKIP LOCKED` and ChromaDB offline vector search.

### Minute 2: Database Design & Advanced Concepts
- **Speaker**: Chiranth (Person A)
- **Key Points**:
  - 15 relational tables normalized to 3NF / BCNF.
  - 6 stored procedures/functions (`sp_book_tickets`, `fn_calc_fare`, `sp_confirm_payment`).
  - 5 database triggers (audit log, route validity, passenger age constraints).
  - 5 database views (`v_run_availability`, `v_admin_revenue`).
  - 1 recurring MySQL event (`ev_release_expired_holds` running every 30s).
  - Least-privilege DB users: `app_rw` (Read-Write) vs `app_ro` (Read-Only).

### Minute 3: Vector Database & Offline Cognitive Retrieval
- **Speaker**: Jashruth (Person B)
- **Key Points**:
  - Why ChromaDB? Relational databases cannot understand semantic intent (e.g. *"overnight sleeper train to Chennai"* or *"can I get a refund on Tatkal ticket?"*).
  - 100% Offline: `all-MiniLM-L6-v2` embedding weights cached in `./models/all-MiniLM-L6-v2` with cosine distance space.

### Minute 4: Live Demonstration of Concurrency & Hold Sweep
- **Speaker**: Jashruth & Chiranth
- **Key Points**:
  - Execute live concurrency test: 16 simultaneous threads hammering the same seats.
  - Demonstrate **0 double-bookings** via SQL verification query.
  - Demonstrate 8-minute hold release mechanism.

### Minute 5: Frontend Experience & Next.js 14 Integration
- **Speaker**: Jashruth (Person B)
- **Key Points**:
  - Next.js 14 App Router with interactive coach seat map and live Tatkal countdown.
  - Idempotent payment submission with `Idempotency-Key`.
  - Admin analytics and audit log inspection.

---

## 2. Interactive Terminal Commands for Live Demonstration

### Command 1: Run Concurrency Demo
Demonstrates 16 threads hammering the same seats simultaneously with ZERO double-booking.
```powershell
.\.venv\Scripts\pytest.exe backend/tests/test_concurrency.py -v
```

### Command 2: Demonstrate ChromaDB Semantic Vector Search
Demonstrates natural language discovery of trains and policy FAQs.
```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); from chroma_svc.search import search_trains, search_faq; print('\n[Train Search Result]:'); print(search_trains('fast luxury night train to Delhi')[0]); print('\n[FAQ Search Result]:'); print(search_faq('can I cancel a Tatkal ticket?')[0])"
```

### Command 3: Verify Triggers & Audit Trail
Inspects trigger-populated audit trail rows after a booking mutation.
```powershell
.\.venv\Scripts\python.exe -c "import pymysql; conn=pymysql.connect(host='127.0.0.1', user='root', password='Chiranth@SQL', database='tatkal_db'); cur=conn.cursor(); cur.execute('SELECT log_id, entity_name, action, old_state, new_state, changed_at FROM audit_log ORDER BY changed_at DESC LIMIT 3'); print(cur.fetchall())"
```

### Command 4: Inspect View `v_admin_revenue`
Queries analytical revenue breakdown calculated directly in the database.
```powershell
.\.venv\Scripts\python.exe -c "import pymysql; conn=pymysql.connect(host='127.0.0.1', user='root', password='Chiranth@SQL', database='tatkal_db'); cur=conn.cursor(); cur.execute('SELECT * FROM v_admin_revenue LIMIT 3'); print(cur.fetchall())"
```
