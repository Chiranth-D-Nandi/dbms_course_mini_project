<!-- Owner: Person B -->
# Tatkal High-Concurrency Train Booking System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.x](https://img.shields.io/badge/django-5.2-green.svg)](https://docs.djangoproject.com/)
[![MySQL 8.0](https://img.shields.io/badge/mysql-8.0-orange.svg)](https://www.mysql.com/)
[![ChromaDB](https://img.shields.io/badge/chromadb-vector-purple.svg)](https://www.trychroma.com/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, high-concurrency railway ticketing engine designed to eliminate the fundamental concurrency bottlenecks of the IRCTC Tatkal booking rush. Built for the PES University DBMS Experiential Learning Project (Level 3).

---

## 1. Project Overview & Key Features

During the opening minutes of the Tatkal booking window (10:00 AM for AC classes, 11:00 AM for Non-AC classes), thousands of concurrent requests compete for dozens of berths. Traditional systems suffer from race conditions, deadlocks, and double-booking (lost updates).

This project solves these challenges at the **database layer**:
- **Zero Double-Booking Guarantee**: Employs MySQL 8.0 InnoDB row-level locking via `SELECT ... FOR UPDATE SKIP LOCKED` inside compiled stored procedures.
- **Sub-15ms Booking Latency**: Transactional seat hold, dynamic fare computation (`fn_calc_fare`), and PNR issuance executed directly in MySQL memory.
- **Autonomous 8-Minute Hold Release**: Unconfirmed seats are swept every 30 seconds by a native MySQL Event (`ev_release_expired_holds`).
- **Cognitive Vector Discovery (ChromaDB)**: 100% offline semantic search over trains and 35+ railway policy FAQs using local sentence-transformer embeddings (`all-MiniLM-L6-v2`).
- **Idempotent Payment Confirmation**: Enforces `Idempotency-Key` headers preventing duplicate charges on network retries.
- **Tiered Cancellation Refunds**: Implements official Indian Railway refund slabs (>48 hrs, 48-12 hrs, 12-4 hrs, <4 hrs, Tatkal 0% refund).

---

## 2. Advanced Database Concepts Implemented

| Concept | Implementation in this Codebase |
| :--- | :--- |
| **ACID Transactions** | Multi-table atomic reservations (`run_seat` + `booking` + `passenger`) in `sp_book_tickets`. |
| **Row-Level Concurrency** | `SELECT ... FOR UPDATE SKIP LOCKED` eliminates wait queues and lock contention. |
| **Stored Procedures** | `sp_generate_run_inventory`, `sp_search_trains`, `sp_book_tickets`, `sp_confirm_payment`, `sp_cancel_booking`, `sp_release_expired_holds`. |
| **Stored Functions** | `fn_calc_fare` computing mileage rates and class-specific Tatkal surcharges. |
| **Database Triggers** | `trg_booking_status_audit`, `trg_run_seat_audit`, `trg_passenger_validate`, `trg_booking_route_check`, `trg_prevent_booked_seat_delete`. |
| **Relational Views** | `v_run_availability`, `v_train_route`, `v_booking_summary`, `v_admin_revenue`, `v_passenger_age`. |
| **Full-Text Search** | MySQL `FULLTEXT` natural language index on `station(station_code, station_name, city)`. |
| **Vector Similarity Search** | ChromaDB HNSW cosine distance search on `train_info` and `policy_faq` collections. |
| **MySQL Event Scheduler** | `ev_release_expired_holds` running every 30 seconds to reclaim unconfirmed holds. |
| **Database-Level Validation** | `CHECK` constraints on age ($1 \le age \le 120$), distances, platforms, and `ENUM` domains. |
| **Least-Privilege Roles** | Dual connection separation: `app_rw` (Read-Write) and `app_ro` (Read-Only). |

---

## 3. Team & 50/50 Work Split

See [CONTRIBUTORS.md](file:///CONTRIBUTORS.md) and [OWNERSHIP.csv](file:///OWNERSHIP.csv) for granular file-by-file ownership tracking.

| Contributor | Role | Core Ownership |
| :--- | :--- | :--- |
| **Chiranth D Nandi** (`PES2UG24AM048`) | **Person A (Data & Backend)** | MySQL DDL, stored procedures, triggers, views, events, Django backend, REST APIs, Chroma query service, concurrency tests, schema docs. |
| **Jashruth K A** (`PES2UG24AM069`) | **Person B (Experience & Ops)** | Next.js 14 frontend, seat map UI, hold timer, seed data generator, Chroma ingestion, Locust load test, runner scripts, functional docs. |

---

## 4. Quickstart Guide (Local Setup)

### Prerequisites
- Windows 10/11, macOS, or Linux
- Python 3.11+
- Node.js 18+ (Node 20+ recommended)
- Local MySQL 8.0 server running on port `3306`

### 4.1 Automated Setup Script

**Windows (PowerShell)**:
```powershell
.\scripts\setup.ps1
```

**Linux / macOS (Bash)**:
```bash
chmod +x ./scripts/*.sh
./scripts/setup.sh
```

### 4.2 Step-by-Step Manual Setup

1. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your local MySQL root password (e.g., MYSQL_ROOT_PASSWORD=YourPassword)
   ```

2. **Python Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Initialize Database Schema & Objects**:
   ```bash
   python backend/manage.py init_db
   ```

4. **Seed Realistic Train Data & Users**:
   ```bash
   python scripts/seed.py
   ```

5. **Ingest ChromaDB Vector Collections (Offline Cache)**:
   ```bash
   python scripts/ingest_chroma.py
   ```

6. **Install Frontend Dependencies & Build**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

---

## 5. Running the Application

Start both the Django backend and Next.js frontend with a single command:

**Windows (PowerShell)**:
```powershell
.\scripts\dev.ps1
```

**Linux / macOS (Bash)**:
```bash
./scripts/dev.sh
```

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://127.0.0.1:8000/api/`
- **Demo Customer Credentials**: `chiranth@example.com` / `Customer@123`
- **Demo Admin Credentials**: `admin@tatkal.com` / `Admin@123`

---

## 6. Running Tests

### 6.1 Backend Pytest & Concurrency Suite
```bash
.\.venv\Scripts\pytest.exe backend/tests -v
```

### 6.2 Locust Load Test (Simulated Rush)
```bash
.\.venv\Scripts\locust.exe -f scripts/locustfile.py --headless -u 100 -r 20 -t 30s --host http://127.0.0.1:8000
```

### 6.3 Frontend Typecheck
```bash
cd frontend
npm run typecheck
```

---

## 7. Interactive Demo Scripts for Viva Evaluation

| Script | Purpose | Command |
| :--- | :--- | :--- |
| `demo_concurrency.ps1` | Proves ZERO double-booking under 16 concurrent threads | `.\scripts\demo_concurrency.ps1` |
| `demo_expiry.ps1` | Demonstrates 8-minute hold timeout and seat recovery | `.\scripts\demo_expiry.ps1` |
| `demo_tatkal_window.ps1` | Tests 10:00 AM / 11:00 AM Tatkal window rules | `.\scripts\demo_tatkal_window.ps1` |
| `demo_reset.ps1` | Flushes and reseeds clean database state | `.\scripts\demo_reset.ps1` |
| `preflight.ps1` | Validates MySQL, Chroma, Node, and Python preflight health | `.\scripts\preflight.ps1` |
