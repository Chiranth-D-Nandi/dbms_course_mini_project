<!-- Owner: Person B -->
# Application Walkthrough & User Interface Showcase

This document illustrates the complete user experience of the Tatkal High-Concurrency Train Booking System, detailing screen layouts, interactive controls, and real-time state transitions.

---

## 1. Screen 1: Home Page & Station Autocomplete
- **Route**: `/`
- **Features**: Hero banner with dual search tabs: Traditional Relational Route Search and Cognitive Semantic Search.
- **Components**:
  - `StationAutocomplete`: Queries `/api/stations/?q=...` leveraging MySQL 8.0 `FULLTEXT` natural language index.
  - Date Picker: Defaults to tomorrow's date with min date restriction.
  - Travel Class & Quota Selectors: General, Tatkal, Premium Tatkal.

```
+-----------------------------------------------------------------------------------+
|  [Logo] TatkalPRS         Search Trains    Semantic Search    Help/FAQ    [Login] |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|                   High-Speed Railway Ticketing Engine                             |
|          Zero Double-Booking * Sub-10ms Locking * Offline Vector Search           |
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   |  From Station: [ Bengaluru (SBC)      ]   To Station: [ Chennai (MAS)   ] |   |
|   |  Date: [ 2026-11-03 ]   Class: [ 3A - AC 3-Tier ]   Quota: [ TATKAL v ]   |   |
|   |                                                                           |   |
|   |                      [ Search Available Trains -> ]                       |   |
|   +---------------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Screen 2: Cognitive Semantic Search (ChromaDB)
- **Route**: `/?tab=semantic` or `/help`
- **Features**: Powered by `sentence-transformers/all-MiniLM-L6-v2` against persistent ChromaDB collections.
- **Example Inquiries**:
  - *"Fast overnight train from Bangalore to Delhi with AC sleeper"* $\to$ Returns Bengaluru Rajdhani Express with 91.4% similarity.
  - *"Daytime business chair car to Coimbatore"* $\to$ Returns Chennai - Coimbatore Shatabdi Express.

---

## 3. Screen 3: Train Search Results & Route Availability
- **Route**: `/search?source=SBC&dest=MAS&date=2026-11-03&class=3A&quota=TATKAL`
- **Features**: Real-time train cards listing departure/arrival times, duration, travel classes, live available seats, and dynamic fares calculated via `fn_calc_fare`.

```
+-----------------------------------------------------------------------------------+
| Results: Bengaluru (SBC) -> Chennai (MAS) on 2026-11-03 (Tatkal Quota)            |
+-----------------------------------------------------------------------------------+
| [12658] Bengaluru - Chennai Superfast Express           Runs: Daily               |
| Departure: 06:00 (SBC) -------- (05h 45m) --------> Arrival: 11:45 (MAS)          |
|                                                                                   |
| Classes Available:                                                                |
| +---------------------+ +---------------------+ +-------------------------------+ |
| | Sleeper (SL)        | | AC 3 Tier (3A)      | | AC 2 Tier (2A)                | |
| | Available: 48 seats | | Available: 18 seats | | Available: 6 seats            | |
| | Fare: Rs 340.00     | | Fare: Rs 880.00     | | Fare: Rs 1,240.00             | |
| | [ Book Now ]        | | [ Book Tatkal ]     | | [ Book Tatkal ]               | |
| +---------------------+ +---------------------+ +-------------------------------+ |
+-----------------------------------------------------------------------------------+
```

---

## 4. Screen 4: Real-Time Tatkal Window Countdown & Seat Map
- **Route**: `/book/[runId]`
- **Features**:
  - Live server-synchronized countdown timer indicating seconds until 10:00 AM (AC) or 11:00 AM (Non-AC) Tatkal opening.
  - Interactive coach seat map with color-coded status badges: Green (Available), Amber (Held), Red (Booked).
  - Dynamic passenger form supporting 1 to 6 travelers with ID card validation.

---

## 5. Screen 5: 8-Minute Hold Timer & Payment Simulation
- **Route**: `/pay/[pnr]`
- **Features**:
  - Active reservation hold placed by `sp_book_tickets` with candidate seats locked via `FOR UPDATE SKIP LOCKED`.
  - Prominent 8-minute countdown clock (`07:49 remaining`).
  - Idempotent payment submission with unique `Idempotency-Key` header preventing duplicate transactions.

```
+-----------------------------------------------------------------------------------+
|  Seats Placed on Hold! PNR: 8492019482                                            |
|  [ Hold Countdown: 07:42 ] - Seats will be auto-released if payment expires.      |
|                                                                                   |
|  Train: 12658 Bengaluru - Chennai SF       Coach: B1 | Seat: 14, 15 (Lower, Middle)|
|  Total Fare Payable: Rs 1,760.00                                                  |
|                                                                                   |
|  Select Payment Method:                                                           |
|  (o) UPI / QR Code    ( ) Credit / Debit Card    ( ) Net Banking                  |
|                                                                                   |
|  [ Confirm & Pay Rs 1,760.00 (Idempotent Safe) ]                                  |
+-----------------------------------------------------------------------------------+
```

---

## 6. Screen 6: Confirmed Ticket & PNR View
- **Route**: `/bookings/[pnr]`
- **Features**:
  - Complete digital e-ticket displaying passenger names, allocated coach, seat numbers, berth types, and payment transaction ID.
  - Interactive "Cancel Ticket" modal displaying dynamic cancellation fees and refund estimates according to railway refund slabs.

---

## 7. Screen 7: Administrative Analytics Dashboard
- **Route**: `/admin`
- **Features**:
  - Restricted via RBAC (`IsAdminUserRole`).
  - Financial revenue tables derived from view `v_admin_revenue`.
  - Filterable trigger audit logs from table `audit_log`.
  - Manual hold sweep button triggering `sp_release_expired_holds`.
