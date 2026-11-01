# Owner: Person A
"""
Tests for unmanaged relational models in booking_engine.
Verifies object-relational mapping integrity against MySQL 8.0 schema.
"""

import pytest
from booking_engine.models import (
    AppUser, Station, Train, TrainRun, Coach, Seat,
    SeatClass, Booking, Payment, AuditLog
)

@pytest.mark.django_db
def test_app_user_query():
    users = AppUser.objects.all()
    assert users.count() >= 1
    admin = AppUser.objects.filter(role="ADMIN").first()
    assert admin is not None
    assert admin.role == "ADMIN"

@pytest.mark.django_db
def test_station_and_train_query():
    stations = Station.objects.all()
    assert stations.count() >= 10
    trains = Train.objects.all()
    assert trains.count() >= 5
    for t in trains[:3]:
        assert t.train_number is not None
        assert t.train_name is not None
        assert t.train_type is not None

@pytest.mark.django_db
def test_coach_and_seat_relations():
    coaches = Coach.objects.all()
    assert coaches.count() >= 10
    c = coaches.first()
    seats = Seat.objects.filter(coach=c)
    assert seats.count() > 0

@pytest.mark.django_db
def test_seat_classes_exist():
    classes = SeatClass.objects.all()
    class_codes = [sc.class_code for sc in classes]
    assert "SL" in class_codes
    assert "3A" in class_codes
    assert "2A" in class_codes
