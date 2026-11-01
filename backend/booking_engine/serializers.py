# Owner: Person A
"""
Serializers for tatkal_core REST endpoints.
Includes request validation for registration, train search, seat maps,
high-concurrency booking payloads, and payment confirmation.
"""

from rest_framework import serializers
from .models import (
    AppUser, Station, Train, TrainStop, TrainRun,
    Booking, Passenger, Payment, Cancellation, AuditLog,
    VRunAvailability, VTrainRoute, VBookingSummary, VAdminRevenue
)

class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ["user_id", "first_name", "last_name", "email", "phone", "role", "created_at"]


class RegisterRequestSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField(max_length=100)
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(min_length=6, write_only=True)
    role = serializers.ChoiceField(choices=["CUSTOMER", "ADMIN"], default="CUSTOMER")


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ["station_id", "station_code", "station_name", "city", "state", "zone", "number_of_platforms"]


class TrainStopSerializer(serializers.ModelSerializer):
    station_code = serializers.CharField(source="station.station_code", read_only=True)
    station_name = serializers.CharField(source="station.station_name", read_only=True)
    city = serializers.CharField(source="station.city", read_only=True)

    class Meta:
        model = TrainStop
        fields = [
            "stop_id", "station_id", "station_code", "station_name", "city",
            "stop_sequence", "arrival_time", "departure_time",
            "halt_duration_minutes", "distance_from_source_km", "day_offset"
        ]


class TrainDetailSerializer(serializers.ModelSerializer):
    source_station_code = serializers.CharField(source="source_station.station_code", read_only=True)
    source_station_name = serializers.CharField(source="source_station.station_name", read_only=True)
    dest_station_code = serializers.CharField(source="dest_station.station_code", read_only=True)
    dest_station_name = serializers.CharField(source="dest_station.station_name", read_only=True)
    stops = TrainStopSerializer(many=True, read_only=True)

    class Meta:
        model = Train
        fields = [
            "train_id", "train_number", "train_name", "train_type",
            "source_station_id", "source_station_code", "source_station_name",
            "dest_station_id", "dest_station_code", "dest_station_name",
            "total_distance_km", "is_active", "stops"
        ]


class PassengerInputSerializer(serializers.Serializer):
    passenger_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=1, max_value=120)
    gender = serializers.ChoiceField(choices=["MALE", "FEMALE", "OTHER"])
    id_card_type = serializers.ChoiceField(choices=["AADHAAR", "PAN", "PASSPORT", "VOTER_ID", "DRIVING_LICENSE"])
    id_card_number = serializers.CharField(max_length=50)
    berth_preference = serializers.ChoiceField(
        choices=["LOWER", "MIDDLE", "UPPER", "SIDE_LOWER", "SIDE_UPPER", "WINDOW", "ANY"],
        default="ANY",
        required=False
    )


class BookingCreateRequestSerializer(serializers.Serializer):
    run_id = serializers.IntegerField(min_value=1)
    source_station_id = serializers.IntegerField(min_value=1)
    dest_station_id = serializers.IntegerField(min_value=1)
    class_code = serializers.CharField(max_length=10)
    booking_type = serializers.ChoiceField(choices=["GENERAL", "TATKAL", "PREMIUM_TATKAL"], default="GENERAL")
    passengers = PassengerInputSerializer(many=True)

    def validate_passengers(self, value):
        if not (1 <= len(value) <= 6):
            raise serializers.ValidationError("Booking must contain between 1 and 6 passengers.")
        return value


class PaymentConfirmRequestSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=100)
    payment_method = serializers.ChoiceField(choices=["UPI", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING"])


class CancellationRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class PassengerDetailSerializer(serializers.ModelSerializer):
    coach_code = serializers.CharField(source="run_seat.seat.coach.coach_code", read_only=True)
    seat_number = serializers.IntegerField(source="run_seat.seat.seat_number", read_only=True)
    berth_type = serializers.CharField(source="run_seat.seat.berth_type", read_only=True)

    class Meta:
        model = Passenger
        fields = [
            "passenger_id", "passenger_name", "age", "gender",
            "id_card_type", "id_card_number", "coach_code", "seat_number",
            "berth_type", "seat_fare"
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    passengers = PassengerDetailSerializer(many=True, read_only=True)
    train_number = serializers.CharField(source="run.train.train_number", read_only=True)
    train_name = serializers.CharField(source="run.train.train_name", read_only=True)
    journey_date = serializers.DateField(source="run.journey_date", read_only=True)
    source_code = serializers.CharField(source="source_station.station_code", read_only=True)
    dest_code = serializers.CharField(source="dest_station.station_code", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "booking_id", "pnr", "user_id", "run_id", "train_number", "train_name",
            "journey_date", "source_station_id", "source_code", "dest_station_id", "dest_code",
            "class_code", "booking_type", "status", "booking_time", "expires_at",
            "total_fare", "passengers"
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["log_id", "entity_name", "entity_id", "action", "old_state", "new_state", "changed_by", "changed_at"]
