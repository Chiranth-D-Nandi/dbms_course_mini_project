<!-- Owner: Person A -->
# REST API Contract & Specification

This document serves as the formal API contract between **Person A (Data & Backend)** and **Person B (Experience & Ops)**. Both halves code strictly against this specification.

Base URL: `http://127.0.0.1:8000/api`

---

## 1. Authentication & Session Management

All protected endpoints require an `Authorization: Bearer <access_token>` header.

### 1.1 `POST /api/auth/register`
Creates a new customer account.
- **Request Body**:
  ```json
  {
    "first_name": "Chiranth",
    "last_name": "Nandi",
    "email": "chiranth@example.com",
    "phone": "9876543210",
    "password": "StrongPassword123"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "user": {
      "user_id": 1,
      "first_name": "Chiranth",
      "last_name": "Nandi",
      "email": "chiranth@example.com",
      "phone": "9876543210",
      "role": "CUSTOMER"
    },
    "tokens": {
      "access": "eyJhbGciOi...",
      "refresh": "eyJhbGciOi..."
    }
  }
  ```
- **Errors**: `400 Bad Request` (duplicate email/phone, invalid phone digits), `422 Unprocessable Entity`.

### 1.2 `POST /api/auth/login`
Authenticates a user with hashed password verification.
- **Request Body**:
  ```json
  {
    "email": "chiranth@example.com",
    "password": "StrongPassword123"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "user": {
      "user_id": 1,
      "email": "chiranth@example.com",
      "first_name": "Chiranth",
      "last_name": "Nandi",
      "role": "CUSTOMER"
    },
    "tokens": {
      "access": "eyJhbGci...",
      "refresh": "eyJhbGci..."
    }
  }
  ```

### 1.3 `POST /api/auth/refresh`
Refreshes an expired access token.
- **Request Body**: `{"refresh": "token"}`
- **Response `200 OK`**: `{"access": "token"}`

### 1.4 `GET /api/auth/me`
Fetches the currently authenticated profile.
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**: User profile object.

---

## 2. Public Train & Station Endpoints

### 2.1 `GET /api/stations?q=<query>`
Performs full-text search across station names and cities.
- **Response `200 OK`**:
  ```json
  [
    {
      "station_id": 1,
      "station_code": "SBC",
      "station_name": "KSR Bengaluru City",
      "city": "Bengaluru",
      "state": "Karnataka"
    }
  ]
  ```

### 2.2 `GET /api/trains/search?from=<id>&to=<id>&date=YYYY-MM-DD`
Calls stored procedure `sp_search_trains` to return valid routes, running schedules, and class-wise seat counts.
- **Response `200 OK`**:
  ```json
  [
    {
      "run_id": 101,
      "train_id": 1,
      "train_number": "12658",
      "train_name": "Bengaluru - Chennai Mail",
      "train_type": "SUPERFAST",
      "source_departure": "22:40:00",
      "dest_arrival": "04:15:00",
      "distance_km": 362,
      "journey_date": "2026-11-05",
      "availability": [
        {
          "class_code": "3A",
          "class_name": "AC 3 Tier",
          "general_available": 34,
          "tatkal_available": 8,
          "base_fare": 650.00,
          "tatkal_fare": 850.00
        }
      ]
    }
  ]
  ```

### 2.3 `GET /api/trains/{id}`
Returns complete schedule, intermediate stops in order (with calculated `halt_duration_minutes`), running days of the week, and coach composition.

### 2.4 `GET /api/runs/{run_id}/availability`
Returns real-time seat availability grouped by class and quota (`GENERAL`, `TATKAL`).

### 2.5 `GET /api/runs/{run_id}/seats`
Seat map view returning all coaches, seats, berth types (`LB`, `MB`, `UB`, `SL`, `SU`, `WS`, `MS`, `AS`), and their live status (`AVAILABLE`, `HELD`, `BOOKED`).

### 2.6 `GET /api/tatkal/status?run_id=<id>&class=<code>`
Calculates Tatkal window opening time for the given run:
- AC classes (1A, 2A, 3A, CC): opens at 10:00 AM on `journey_date - 1 day`.
- Non-AC classes (SL): opens at 11:00 AM on `journey_date - 1 day`.
- Returns:
  ```json
  {
    "run_id": 101,
    "class_code": "3A",
    "journey_date": "2026-11-05",
    "tatkal_open_time": "2026-11-04T10:00:00",
    "is_open": true,
    "seconds_remaining": 0,
    "quota_total": 16,
    "quota_available": 6
  }
  ```

---

## 3. High-Concurrency Booking Engine

### 3.1 `POST /api/bookings`
Initiates a transactional seat hold by invoking stored procedure `sp_book_tickets`.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "run_id": 101,
    "class_code": "3A",
    "source_station_id": 1,
    "dest_station_id": 5,
    "booking_type": "TATKAL",
    "passengers": [
      {
        "name": "Ramesh Kumar",
        "dob": "1995-04-12",
        "gender": "MALE",
        "id_proof_type": "AADHAAR",
        "id_proof_no": "9988-7766-5544"
      }
    ]
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "pnr": 1000000042,
    "status": "PENDING",
    "total_fare": 850.00,
    "booking_time": "2026-11-04T10:01:15Z",
    "expires_at": "2026-11-04T10:06:15Z",
    "hold_seconds_remaining": 300,
    "message": "Seats held successfully. Complete payment before hold expires."
  }
  ```
- **Error Codes**:
  - `409 Conflict`: `{"error": {"code": "SOLD_OUT", "message": "Requested seats are sold out in this quota."}}`
  - `423 Locked`: `{"error": {"code": "TATKAL_WINDOW_CLOSED", "message": "Tatkal window opens at 10:00 AM."}}`
  - `422 Unprocessable Entity`: Passenger limit exceeded (max 4 for Tatkal, max 6 for General), invalid route sequence, or invalid date of birth.
  - `429 Too Many Requests`: Rate limiter triggered on booking attempts.

### 3.2 `POST /api/bookings/{pnr}/pay`
Confirms ticket and seat booking by executing stored procedure `sp_confirm_payment`.
- **Headers**:
  - `Authorization: Bearer <token>`
  - `Idempotency-Key: <unique-uuid-or-key>`
- **Request Body**:
  ```json
  {
    "amount": 850.00,
    "method": "UPI"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "payment_id": 301,
    "pnr": 1000000042,
    "txn_ref": "TXN_20261104_100155_8921",
    "status": "SUCCESS",
    "booking_status": "CONFIRMED",
    "message": "Payment successful. Ticket confirmed!"
  }
  ```
- **Errors**:
  - `410 Gone`: Seat hold has expired (`HOLD_EXPIRED`). Booking marked `EXPIRED` and seats released.
  - `422 Unprocessable Entity`: Fare amount mismatch (`AMOUNT_MISMATCH`).

### 3.3 `POST /api/bookings/{pnr}/cancel`
Cancels booking and computes refund via `sp_cancel_booking`.
- **Refund Policy Rules**:
  - Cancellation > 48 hours before departure: 90% refund.
  - Cancellation 12 - 48 hours before departure: 50% refund.
  - Cancellation < 12 hours before departure: 0% refund.
  - Tatkal tickets: 0% refund (per standard railway guidelines).
- **Response `200 OK`**:
  ```json
  {
    "pnr": 1000000042,
    "status": "CANCELLED",
    "refund_amount": 0.00,
    "cancellation_time": "2026-11-04T12:00:00Z",
    "reason": "Customer cancellation"
  }
  ```

### 3.4 `GET /api/bookings/mine`
Returns all bookings for the active user.

### 3.5 `GET /api/bookings/{pnr}`
Returns ticket summary, passengers, assigned coach and berth numbers, and payment status.

---

## 4. Vector & Semantic Search Endpoints

### 4.1 `GET /api/search/trains?q=<query>&train_type=<optional>`
Natural language train query via ChromaDB collection `train_info` (cosine distance). Matched IDs are hydrated with live MySQL schedule and availability.
- **Example query**: `/api/search/trains?q=fast overnight train to chennai with ac`
- **Response `200 OK`**: Top 5 ranked trains with cosine similarity distance and route info.

### 4.2 `GET /api/search/faq?q=<query>&category=<optional>`
Vector semantic query on Tatkal rules, cancellation policies, and ID requirements via ChromaDB collection `policy_faq`.
- **Example query**: `/api/search/faq?q=what is the refund on cancelling tatkal ticket`
- **Response `200 OK`**: Top matched policy chunks with relevance score and source references.

---

## 5. Admin & Analytics Endpoints

Restricted to users with role `ADMIN`.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/admin/runs/{id}/generate-inventory` | `POST` | Calls `sp_generate_run_inventory` to create seat inventory for a train run |
| `/api/admin/runs/{id}/cancel` | `POST` | Cancels a train run and updates status |
| `/api/admin/reports/revenue` | `GET` | Aggregated revenue report per train and route (`v_admin_revenue`) |
| `/api/admin/reports/occupancy` | `GET` | Train occupancy percentage report |
| `/api/admin/reports/top-users` | `GET` | Most active customers by booking volume |
| `/api/admin/reports/tatkal-demand`| `GET` | Surge metrics comparing Tatkal vs General demand |
| `/api/admin/audit-log` | `GET` | Trigger-generated audit log table showing JSON old/new diffs |

---

## 6. Standard Error Format
All errors return the standardized structure:
```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable explanation.",
    "details": {}
  }
}
```
Standard HTTP status codes:
- `400`: Bad Request (malformed input)
- `401`: Unauthorized (missing or invalid token)
- `403`: Forbidden (insufficient role privileges)
- `404`: Not Found (resource does not exist)
- `409`: Conflict (`SOLD_OUT`, seat collision)
- `410`: Gone (`HOLD_EXPIRED`)
- `422`: Unprocessable Entity (`VALIDATION_ERROR`, route order mismatch, amount mismatch)
- `423`: Locked (`TATKAL_WINDOW_CLOSED`)
- `429`: Too Many Requests (`RATE_LIMITED`)
- `500`: Internal Server Error
