<!-- Owner: Person A -->
# System Architecture Specification

This document details the multi-tier architectural blueprint of the Tatkal High-Concurrency Train Booking System, encompassing presentation, application services, database engines, and offline vector intelligence.

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (Next.js 14 App Router)"]
        UI["Web Browser (React 18 + Tailwind CSS)"]
        State["Client State & JWT Token Storage"]
        UI <--> State
    end

    subgraph APILayer ["Application & API Layer (Django 5 + DRF)"]
        GW["REST API Gateway (tatkal_core)"]
        AuthMiddleware["JWT Auth Middleware & RBAC"]
        Throttle["TatkalBurstThrottle (Rate Limiter)"]
        Router["DRF Viewsets & API Controllers"]
        
        GW --> AuthMiddleware --> Throttle --> Router
    end

    subgraph DataLayer ["Data & Storage Layer"]
        subgraph RelationalDB ["MySQL 8.0 InnoDB (Local 3306)"]
            PoolRW["Read-Write Connection (app_rw)"]
            PoolRO["Read-Only Connection (app_ro)"]
            SP["Stored Procedures (sp_book_tickets, sp_confirm_payment)"]
            Trg["Triggers (Audit, Age, Route Validation)"]
            Views["Views (v_run_availability, v_admin_revenue)"]
            Event["MySQL Event (ev_release_expired_holds)"]
            
            PoolRW --> SP
            PoolRW --> Trg
            PoolRO --> Views
            Event -.->|Every 30s| SP
        end

        subgraph VectorDB ["ChromaDB & Sentence Transformers"]
            ChromaClient["ChromaDB Persistent Client (./chroma_data)"]
            LocalModel["all-MiniLM-L6-v2 Cached Weights (./models/)"]
            ColTrain["Collection: train_info"]
            ColFAQ["Collection: policy_faq"]
            
            LocalModel --> ChromaClient
            ChromaClient --> ColTrain
            ChromaClient --> ColFAQ
        end
    end

    UI -->|HTTP / JSON via NEXT_PUBLIC_API_URL| GW
    Router -->|DB Queries & Procedure Calls| PoolRW
    Router -->|Read Queries & Reports| PoolRO
    Router -->|Semantic Search| ChromaClient
```

---

## 2. Multi-Tier Layer Breakdown

### Layer 1: Client Presentation Tier (Person B)
- **Framework**: Next.js 14 App Router with React Server Components (RSC) and client-side hydration.
- **Language**: TypeScript with strict type checking enabled (`strict: true`).
- **Styling**: Tailwind CSS with custom responsive design and Lucide React icons.
- **State & Communication**:
  - Typed API client (`frontend/src/lib/api.ts`) managing automatic JWT access and refresh token rotation.
  - Custom HTTP header injection: `Idempotency-Key` and `Authorization: Bearer <token>`.
  - Tatkal countdown clock synchronizing against server time.
  - Interactive coach seat map with real-time status indicators (Available, Held, Booked).

### Layer 2: API & Application Engine (Person A)
- **Framework**: Python 3.11+ with Django 5.x and Django REST Framework (DRF).
- **Authentication & RBAC**: SimpleJWT customized via `CustomJWTAuthentication` reading from MySQL `app_user` table. Enforces role-based permissions (`IsAdminUserRole` vs `IsCustomerUserRole`).
- **Throttling**: `TatkalBurstThrottle` and `TatkalSustainedThrottle` defending against automated bot spam during rush minutes.
- **Deadlock Resilience**: Automatic exponential backoff retry loop intercepting MySQL Error 1213.

### Layer 3: Relational ACID Storage (Person A)
- **RDBMS**: MySQL 8.0 with InnoDB storage engine, UTF-8 (`utf8mb4`) encoding, and transactions.
- **Separation of Concerns**: Dual database connections:
  - `default`: Read-Write credentials (`app_rw`) executing bookings, payments, and administrative mutations.
  - `readonly`: Read-Only credentials (`app_ro`) serving high-throughput search queries and views.
- **Stored Procedures**: Core transactional logic (`sp_book_tickets`, `sp_confirm_payment`, `sp_cancel_booking`) compiled inside MySQL buffer pool.
- **Row-Level Concurrency**: `SELECT ... FOR UPDATE SKIP LOCKED` eliminates seat reservation race conditions.
- **Background Event**: `ev_release_expired_holds` sweeps abandoned holds every 30 seconds.

### Layer 4: Cognitive Vector Retrieval (Person A & B)
- **Engine**: ChromaDB local persistent client storing embeddings on disk (`./chroma_data`).
- **Offline Model**: `sentence-transformers/all-MiniLM-L6-v2` loaded strictly from local disk (`./models/all-MiniLM-L6-v2`).
- **Index Type**: Hierarchical Navigable Small World (HNSW) graph using cosine distance space.
- **Collections**:
  - `train_info`: Semantic embeddings of train descriptions, destinations, and amenities.
  - `policy_faq`: 14 chunks detailing Tatkal rules, cancellation slabs, and ID mandates.

---

## 3. Concurrency Pipeline: Seat Hold & Payment Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Passenger
    participant Web as Next.js 14 UI
    participant API as Django REST API
    participant MySQL as MySQL 8.0 (InnoDB)
    participant Event as MySQL Event Scheduler

    User->>Web: Clicks "Book Tatkal Ticket"
    Web->>API: POST /api/bookings/ (run_id, class, passengers)
    API->>MySQL: CALL sp_book_tickets()
    Note over MySQL: SELECT FOR UPDATE SKIP LOCKED<br/>Locks candidate seats exclusively
    MySQL-->>API: Returns booking_id, PNR, expires_at (8 min)
    API-->>Web: 201 Created (Status: HOLD, expires_at)
    Web->>User: Displays 8-minute Hold Timer & Pay Button

    alt Successful Payment within 8 Minutes
        User->>Web: Clicks "Confirm & Pay"
        Web->>API: POST /api/payments/confirm/ (Idempotency-Key)
        API->>MySQL: CALL sp_confirm_payment()
        Note over MySQL: Idempotency check passed.<br/>booking.status -> CONFIRMED<br/>run_seat.status -> BOOKED
        MySQL-->>API: Success
        API-->>Web: 200 OK (Confirmed Ticket with PNR)
        Web->>User: Renders Confirmed Ticket & Berth
    else Hold Timeout (> 8 Minutes)
        Note over Event: ev_release_expired_holds fires every 30s
        Event->>MySQL: CALL sp_release_expired_holds()
        Note over MySQL: booking.status -> EXPIRED<br/>run_seat.status -> AVAILABLE
        User->>Web: Attempts late payment
        Web->>API: POST /api/payments/confirm/
        API->>MySQL: CALL sp_confirm_payment()
        MySQL-->>API: Error: Hold has expired
        API-->>Web: 400 Bad Request (Hold expired)
        Web->>User: Displays "Hold Expired, Seats Released"
    end
```
