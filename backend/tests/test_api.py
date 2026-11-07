# Owner: Person A
"""
Integration tests for tatkal_core REST API endpoints.
Tests authentication, fulltext search, stored procedure search,
booking workflow, payment idempotency, and admin analytics.
"""

import uuid
import pytest
from datetime import date, timedelta
from rest_framework import status

pytestmark = pytest.mark.django_db(databases=["default", "readonly"])

def test_auth_login_and_profile(api_client):
    # Test Login
    resp = api_client.post("/api/auth/login", {
        "email": "chiranth@example.com",
        "password": "Customer@123"
    }, format="json")
    assert resp.status_code == status.HTTP_200_OK, f"Login failed: {resp.data}"
    assert "tokens" in resp.data
    token = resp.data["tokens"]["access"]

    # Test /api/auth/me
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    me_resp = api_client.get("/api/auth/me")
    assert me_resp.status_code == status.HTTP_200_OK, f"/api/auth/me failed: {me_resp.data}"
    assert me_resp.data["user"]["email"] == "chiranth@example.com"


def test_station_search(api_client):
    # Test listing
    resp = api_client.get("/api/stations/")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data) > 0

    # Test search query
    search_resp = api_client.get("/api/stations/?q=Bengaluru")
    assert search_resp.status_code == status.HTTP_200_OK
    codes = [s["station_code"] for s in search_resp.data]
    assert "SBC" in codes


def test_train_catalog_and_timetable(api_client):
    catalog = api_client.get('/api/trains/')
    assert catalog.status_code == 200
    assert catalog.data
    response = api_client.get(f"/api/trains/{catalog.data[0]['train_id']}/")
    assert response.status_code == 200, response.data
    assert response.data['running_days']
    assert response.data['stops']
    assert all(isinstance(stop['halt_duration_minutes'], int) for stop in response.data['stops'])


def test_sp_search_trains_endpoint(api_client, sample_stations):
    today = date.today().isoformat()
    resp = api_client.get(f"/api/trains/search/?source=SBC&dest=MAS&date={today}&class=3A&quota=GENERAL")
    assert resp.status_code == status.HTTP_200_OK, f"Train search failed: {resp.data}"
    assert "trains" in resp.data
    assert resp.data["count"] > 0
    train = resp.data["trains"][0]
    assert "train_number" in train


def test_seat_map_and_tatkal_status(api_client, sample_run_id):
    resp = api_client.get(f"/api/runs/{sample_run_id}/seats/?class=3A")
    assert resp.status_code == status.HTTP_200_OK
    assert "coaches" in resp.data
    assert "tatkal_info" in resp.data

    tatkal_resp = api_client.get(f"/api/tatkal/status/?run_id={sample_run_id}&class=3A")
    assert tatkal_resp.status_code == status.HTTP_200_OK
    assert "status" in tatkal_resp.data
    assert "opening_time" in tatkal_resp.data


def test_booking_and_payment_flow(api_client, customer_auth_headers, sample_run_id, sample_stations):
    # Step 1: Create Booking (HOLD)
    booking_payload = {
        "run_id": sample_run_id,
        "source_station_id": sample_stations["source_id"],
        "dest_station_id": sample_stations["dest_id"],
        "class_code": "3A",
        "booking_type": "GENERAL",
        "passengers": [
            {
                "passenger_name": "Test Passenger",
                "age": 28,
                "gender": "MALE",
                "id_card_type": "AADHAAR",
                "id_card_number": "123456789012",
                "berth_preference": "ANY"
            }
        ]
    }

    resp = api_client.post("/api/bookings/", booking_payload, format="json", **customer_auth_headers)
    assert resp.status_code == status.HTTP_201_CREATED, f"Booking creation failed: {resp.data}"
    booking_data = resp.data["booking"]
    pnr = booking_data["pnr"]
    assert booking_data["status"] == "HOLD"
    assert len(booking_data["passengers"]) == 1

    # Step 2: Confirm Payment with Idempotency Key
    idempotency_key = f"test-idemp-{uuid.uuid4()}"
    pay_payload = {
        "pnr": pnr,
        "idempotency_key": idempotency_key,
        "payment_method": "UPI"
    }

    pay_resp1 = api_client.post(
        "/api/payments/confirm/",
        pay_payload,
        format="json",
        **customer_auth_headers,
        HTTP_IDEMPOTENCY_KEY=idempotency_key
    )
    assert pay_resp1.status_code == status.HTTP_200_OK, f"Payment failed: {pay_resp1.data}"
    assert pay_resp1.data["booking"]["status"] == "CONFIRMED"
    txn_id_1 = pay_resp1.data["payment"]["transaction_id"]

    # Step 3: Test Idempotent Retry (duplicate submit should succeed without double charge)
    pay_resp2 = api_client.post(
        "/api/payments/confirm/",
        pay_payload,
        format="json",
        **customer_auth_headers,
        HTTP_IDEMPOTENCY_KEY=idempotency_key
    )
    assert pay_resp2.status_code == status.HTTP_200_OK
    assert pay_resp2.data["payment"]["transaction_id"] == txn_id_1

    # Step 4: Verify Booking Details
    detail_resp = api_client.get(f"/api/bookings/{pnr}/", **customer_auth_headers)
    assert detail_resp.status_code == status.HTTP_200_OK
    assert detail_resp.data["status"] == "CONFIRMED"
    assert len(detail_resp.data["payments"]) == 1

    # Step 5: Cancel Booking
    cancel_resp = api_client.post(
        f"/api/bookings/{pnr}/cancel/",
        {"reason": "Changed travel plan"},
        format="json",
        **customer_auth_headers
    )
    assert cancel_resp.status_code == status.HTTP_200_OK
    assert cancel_resp.data["cancellation"]["status"] == "CANCELLED"
    assert cancel_resp.data["cancellation"]["refund_amount"] >= 0


def test_admin_endpoints(api_client, admin_auth_headers, customer_auth_headers):
    # Customer forbidden from admin revenue
    rev_forbidden = api_client.get("/api/admin/revenue/", **customer_auth_headers)
    assert rev_forbidden.status_code == status.HTTP_403_FORBIDDEN

    # Admin allowed
    rev_ok = api_client.get("/api/admin/revenue/", **admin_auth_headers)
    assert rev_ok.status_code == status.HTTP_200_OK
    assert "summary" in rev_ok.data
    assert "revenue_data" in rev_ok.data

    # Admin audit logs
    audit_ok = api_client.get("/api/admin/audit-logs/", **admin_auth_headers)
    assert audit_ok.status_code == status.HTTP_200_OK
    assert isinstance(audit_ok.data, list)
