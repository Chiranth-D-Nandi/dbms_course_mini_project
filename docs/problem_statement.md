<!-- Owner: Person B -->
# Problem Statement: High-Concurrency Railway Ticketing & Tatkal Contention

## 1. Background & Context
Indian Railways operates one of the largest passenger transportation networks in the world, carrying over 23 million passengers daily across more than 13,000 passenger trains. Due to immense demand exceeding seat supply, ticket reservations open in stages:
- **General Quota**: Opens 120 days in advance.
- **Tatkal Quota**: Designed for emergency short-notice travel, opening precisely at **10:00 AM IST** for Air-Conditioned classes (1A, 2A, 3A, CC, EC) and **11:00 AM IST** for Non-AC classes (SL, 2S) on the day prior to journey departure.

## 2. The Core Technical Problem
During the opening minutes of the Tatkal booking window, ticketing infrastructure encounters severe transactional and computational challenges:

1. **Extreme Concurrency & Contention**:
   Thousands of simultaneous user requests attempt to reserve the same narrow block of available seats within milliseconds. Standard database architectures either suffer massive lock contention leading to thread starvation and deadlocks, or fail to isolate transactions, resulting in **double-booking (lost updates)** where the same seat is issued to multiple passengers.

2. **Inflexible Search & Cognitive Disconnect**:
   Passengers searching for trains are forced to know exact 5-digit train numbers or 3-to-4 letter station codes. Natural language inquiries (e.g., *"clean overnight train to Bangalore with AC berths"*) or policy queries (e.g., *"will I get a refund if my Tatkal ticket is waitlisted?"*) cannot be answered by traditional relational databases.

3. **Inconsistent Business Rule Enforcement**:
   Traditional web applications frequently enforce integrity rules only in application code (Python/Node/Java). Under concurrent stress or API bypass, data corruption occurs if constraints (e.g., age boundaries, seat capacity, non-overlapping route halts) are not strictly enforced at the **storage layer**.

4. **Hold Timeout & Inventory Leakage**:
   When users select seats and proceed to payment gateways, systems must temporarily lock seats. If users abandon checkout, close tabs, or experience payment failures, seats remain indefinitely locked unless an automated, transactional sweep mechanism safely returns them to the available pool.

## 3. Project Objectives
This project constructs a production-grade, full-stack Tatkal reservation engine that mathematically guarantees:
- **Zero Double-Bookings** under 500+ concurrent threads.
- Sub-millisecond database-layer seat locking via `SELECT ... FOR UPDATE SKIP LOCKED`.
- Autonomous 8-minute hold expiration via recurring MySQL events.
- Semantic vector discovery powered by an offline ChromaDB instance.
- Complete separation of concerns across a modern Next.js 14 frontend and Django REST backend.
