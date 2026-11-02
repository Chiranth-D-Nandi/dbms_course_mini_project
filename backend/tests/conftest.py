# Owner: Person A
"""
Pytest fixtures for tatkal_core backend tests.
Provides APIClient, authenticated headers for CUSTOMER and ADMIN roles,
and sample train run identifiers from seeded data.
"""

import pytest
from rest_framework.test import APIClient
from django.db import connection
from booking_engine.models import AppUser, TrainRun, Station
from booking_engine.auth_views import get_tokens_for_user

@pytest.fixture(scope="session")
def django_db_setup():
    """Use pre-seeded MySQL tatkal_db database directly without attempting CREATE DATABASE."""
    pass

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def customer_user():
    user = AppUser.objects.filter(email="chiranth@example.com").first()
    if not user:
        user = AppUser.objects.create(
            first_name="Chiranth",
            last_name="Nandi",
            email="test_customer@example.com",
            phone="9000000001",
            password_hash="test",
            role="CUSTOMER",
            is_active=True
        )
    return user

@pytest.fixture
def admin_user():
    user = AppUser.objects.filter(email="admin@tatkal.com").first()
    if not user:
        user = AppUser.objects.create(
            first_name="PRS",
            last_name="Admin",
            email="test_admin@tatkal.com",
            phone="9000000002",
            password_hash="test",
            role="ADMIN",
            is_active=True
        )
    return user

@pytest.fixture
def customer_auth_headers(customer_user):
    tokens = get_tokens_for_user(customer_user)
    return {
        "HTTP_AUTHORIZATION": f"Bearer {tokens['access']}",
    }

@pytest.fixture
def admin_auth_headers(admin_user):
    tokens = get_tokens_for_user(admin_user)
    return {
        "HTTP_AUTHORIZATION": f"Bearer {tokens['access']}",
    }

@pytest.fixture
def sample_run_id():
    import datetime
    from booking_engine.models import Coach
    train_ids = Coach.objects.filter(class_code="3A").values_list("train_id", flat=True)
    future_date = datetime.date.today() + datetime.timedelta(days=3)
    run = TrainRun.objects.filter(train_id__in=train_ids, run_status="SCHEDULED", journey_date__gte=future_date).first()
    if not run:
        run = TrainRun.objects.filter(train_id__in=train_ids, run_status="SCHEDULED").first()
    return run.run_id if run else 1

@pytest.fixture
def sample_stations(sample_run_id):
    from booking_engine.models import TrainStop
    run = TrainRun.objects.get(run_id=sample_run_id)
    stops = list(TrainStop.objects.filter(train_id=run.train_id).order_by("stop_seq"))
    if len(stops) >= 2:
        return {
            "source_id": stops[0].station_id,
            "dest_id": stops[1].station_id,
        }
    sbc = Station.objects.filter(station_code="SBC").first()
    mas = Station.objects.filter(station_code="MAS").first()
    return {
        "source_id": sbc.station_id if sbc else 1,
        "dest_id": mas.station_id if mas else 2,
    }
