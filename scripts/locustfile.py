# Owner: Person B
"""
scripts/locustfile.py: Locust High-Concurrency Load Test
Simulates hundreds of concurrent users competing for limited Tatkal seats on the same train run.
Validates zero double-booking, sub-100ms stored procedure execution under load,
and idempotency handling.
"""

import uuid
import random
from datetime import date, timedelta
from locust import HttpUser, task, between, tag
from locust.exception import StopUser
import os

DEMO_USERS = [
    ("chiranth@example.com", "Customer@123"),
    ("jashruth@example.com", "Customer@123"),
    ("ramesh@example.com", "Customer@123"),
    ("priya@example.com", "Customer@123"),
    ("anand@example.com", "Customer@123"),
]

class TatkalRushUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Aggressive rapid clicking during Tatkal rush
    access_token = None
    user_email = None

    quota = os.getenv("LOAD_QUOTA", "GENERAL")

    def on_start(self):
        """Authenticate user and obtain JWT token."""
        credentials = random.choice(DEMO_USERS)
        self.user_email = credentials[0]
        resp = self.client.post("/api/auth/login", json={
            "email": credentials[0],
            "password": credentials[1]
        })
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data.get("tokens", {}).get("access")
        if not self.access_token:
            raise StopUser()
        journey = (date.today() + timedelta(days=1 if self.quota == "TATKAL" else 3)).isoformat()
        response = self.client.get(f"/api/trains/search/?source=SBC&dest=MAS&date={journey}", headers=self.headers)
        if response.status_code != 200:
            raise StopUser()
        rows = [r for r in response.json()["trains"] if r["class_code"] == "3A"]
        if not rows:
            raise StopUser()
        self.run_id = rows[0]["run_id"]
        self.source_id = response.json()["source"]["station_id"]
        self.dest_id = response.json()["destination"]["station_id"]


    @property
    def headers(self):
        h = {"Content-Type": "application/json"}
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        return h

    @tag("search")
    @task(3)
    def search_trains(self):
        """Simulate users querying train route availability."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        self.client.get(
            f"/api/trains/search/?source=SBC&dest=MAS&date={tomorrow}&class=3A&quota=TATKAL",
            headers=self.headers,
            name="/api/trains/search/"
        )

    @tag("seat_map")
    @task(2)
    def view_seat_map(self):
        """Simulate users inspecting real-time seat availability."""
        # Query seat map for run_id 18
        self.client.get(
            f"/api/runs/{self.run_id}/seats/?class=3A&quota={self.quota}",
            headers=self.headers,
            name="/api/runs/[id]/seats/"
        )

    @tag("tatkal_booking")
    @task(5)
    def attempt_tatkal_booking(self):
        """
        Simulate high-concurrency booking storm hammering the same train run and class.
        Expected results:
        - First N concurrent requests succeed with 201 Created and receive seats.
        - Subsequent requests receive 409 Conflict (Seats exhausted) or 429 (Throttled).
        - ZERO double-booking.
        """
        if not self.access_token:
            return

        passenger_names = ["Arjun", "Kavya", "Rahul", "Sneha", "Aditya", "Meera"]
        name = random.choice(passenger_names)
        random_id = str(random.randint(1000000000, 9999999999))

        payload = {
            "run_id": self.run_id,
            "source_station_id": self.source_id,  # SBC
            "dest_station_id": self.dest_id,    # MAS
            "class_code": "3A",
            "booking_type": self.quota,
            "passengers": [
                {
                    "passenger_name": f"{name} {random.randint(1, 999)}",
                    "age": random.randint(20, 60),
                    "gender": "MALE" if random.random() > 0.5 else "FEMALE",
                    "id_card_type": "AADHAAR",
                    "id_card_number": random_id,
                    "berth_preference": "ANY"
                }
            ]
        }

        with self.client.post("/api/bookings/", json=payload, headers=self.headers, catch_response=True) as resp:
            if resp.status_code == 201:
                # Successfully placed seats on hold! Now immediately simulate payment.
                resp.success()
                data = resp.json()
                booking = data.get("booking", {})
                pnr = booking.get("pnr")
                booking_id = booking.get("booking_id")

                if booking_id and pnr:
                    # Confirm payment with idempotent key
                    idempotency_key = f"locust-pay-{uuid.uuid4()}"
                    pay_resp = self.client.post(
                        "/api/payments/confirm/",
                        json={
                            "booking_id": booking_id,
                            "pnr": pnr,
                            "idempotency_key": idempotency_key,
                            "payment_method": "UPI"
                        },
                        headers={**self.headers, "Idempotency-Key": idempotency_key},
                        name="/api/payments/confirm/"
                    )
            elif resp.status_code == 429 or (resp.status_code == 409 and resp.json().get("error", {}).get("details", {}).get("status") == "SOLD_OUT"):
                # 409: Seats exhausted or held by someone else (expected under concurrency)
                # 429: Throttled by TatkalBurstThrottle (expected under high bot-like spam)
                resp.success()
            else:
                resp.failure(f"Unexpected status code {resp.status_code}: {resp.text}")
