# Owner: Person A
"""
Serializers for tatkal_core REST endpoints.
Includes request validation for registration, train search, seat maps,
high-concurrency booking payloads, and payment confirmation.
"""

from rest_framework import serializers
from .models import AppUser
from datetime import date

class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ["user_id", "first_name", "last_name", "email", "phone", "role", "created_at"]


class RegisterRequestSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField(max_length=100)
    phone = serializers.RegexField(r"^[0-9]{10}$")
    password = serializers.CharField(min_length=6, write_only=True)
    role = serializers.ChoiceField(choices=["CUSTOMER"], default="CUSTOMER")


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PassengerInputSerializer(serializers.Serializer):
    passenger_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=1, max_value=120, required=False)
    dob = serializers.DateField(required=False)
    gender = serializers.ChoiceField(choices=["MALE", "FEMALE", "OTHER"])
    id_card_type = serializers.ChoiceField(choices=["AADHAAR", "PAN", "PASSPORT", "VOTER_ID"])
    id_card_number = serializers.CharField(max_length=50)
    berth_preference = serializers.ChoiceField(
        choices=["LOWER", "MIDDLE", "UPPER", "SIDE_LOWER", "SIDE_UPPER", "WINDOW", "ANY"],
        default="ANY",
        required=False
    )

    def validate(self, data):
        if "dob" in data:
            today = date.today()
            dob = data["dob"]
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if not 1 <= age <= 120:
                raise serializers.ValidationError({"dob": "Passenger age must be between one and 120 years."})
            data["age"] = age
        elif "age" not in data:
            raise serializers.ValidationError("Date of birth or age is required.")
        return data


class BookingCreateRequestSerializer(serializers.Serializer):
    run_id = serializers.IntegerField(min_value=1)
    source_station_id = serializers.IntegerField(min_value=1)
    dest_station_id = serializers.IntegerField(min_value=1)
    class_code = serializers.CharField(max_length=10)
    booking_type = serializers.ChoiceField(choices=["GENERAL", "TATKAL"], default="GENERAL")
    passengers = PassengerInputSerializer(many=True)

    def validate_passengers(self, value):
        if not (1 <= len(value) <= 6):
            raise serializers.ValidationError("Booking must contain between 1 and 6 passengers.")
        return value

    def validate(self, data):
        if data["source_station_id"] == data["dest_station_id"]:
            raise serializers.ValidationError("Choose different source and destination stations.")
        if data["booking_type"] == "TATKAL" and len(data["passengers"]) > 4:
            raise serializers.ValidationError("Tatkal bookings allow at most four passengers.")
        return data


class PaymentConfirmRequestSerializer(serializers.Serializer):
    pnr = serializers.IntegerField(min_value=1)
    idempotency_key = serializers.CharField(max_length=128)
    payment_method = serializers.ChoiceField(choices=["UPI", "CARD", "NETBANKING", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING"])


class CancellationRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
