# Owner: Person A
"""
Relational models mapping with 100% precision to MySQL 8.0 `tatkal_db` schema (01_schema.sql).
All models have `managed = False`.
"""

from django.db import models

class AppUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, default="CUSTOMER")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "app_user"
        managed = False

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Station(models.Model):
    station_id = models.AutoField(primary_key=True)
    station_code = models.CharField(max_length=10, unique=True)
    station_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    class Meta:
        db_table = "station"
        managed = False

    def __str__(self):
        return f"{self.station_code} - {self.station_name}"


class Train(models.Model):
    train_id = models.AutoField(primary_key=True)
    train_number = models.CharField(max_length=10, unique=True)
    train_name = models.CharField(max_length=100)
    train_type = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "train"
        managed = False

    def __str__(self):
        return f"{self.train_number} - {self.train_name}"


class TrainRunningDay(models.Model):
    train = models.ForeignKey(Train, on_delete=models.DO_NOTHING, db_column="train_id", primary_key=True)
    day_of_week = models.IntegerField()

    class Meta:
        db_table = "train_running_day"
        managed = False
        unique_together = (("train", "day_of_week"),)


class TrainStop(models.Model):
    train = models.ForeignKey(Train, on_delete=models.DO_NOTHING, db_column="train_id", primary_key=True)
    stop_seq = models.IntegerField()
    station = models.ForeignKey(Station, on_delete=models.DO_NOTHING, db_column="station_id")
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    day_offset = models.IntegerField(default=0)
    distance_km = models.IntegerField(default=0)

    class Meta:
        db_table = "train_stop"
        managed = False
        unique_together = (("train", "stop_seq"),)


class SeatClass(models.Model):
    class_code = models.CharField(max_length=10, primary_key=True)
    class_name = models.CharField(max_length=50)
    is_ac = models.BooleanField(default=False)
    fare_per_km = models.DecimalField(max_digits=6, decimal_places=2)
    tatkal_open_time = models.TimeField()
    tatkal_quota_pct = models.IntegerField()
    tatkal_surcharge_pct = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    tatkal_min_charge = models.DecimalField(max_digits=8, decimal_places=2, default=100.00)
    tatkal_max_charge = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)

    class Meta:
        db_table = "seat_class"
        managed = False

    def __str__(self):
        return f"{self.class_code} ({self.class_name})"


class Coach(models.Model):
    coach_id = models.AutoField(primary_key=True)
    train = models.ForeignKey(Train, on_delete=models.DO_NOTHING, db_column="train_id")
    class_code = models.ForeignKey(SeatClass, on_delete=models.DO_NOTHING, db_column="class_code")
    coach_number = models.CharField(max_length=10)

    class Meta:
        db_table = "coach"
        managed = False
        unique_together = (("train", "coach_number"),)


class Seat(models.Model):
    seat_id = models.AutoField(primary_key=True)
    coach = models.ForeignKey(Coach, on_delete=models.DO_NOTHING, db_column="coach_id")
    seat_number = models.IntegerField()
    berth_type = models.CharField(max_length=10)

    class Meta:
        db_table = "seat"
        managed = False
        unique_together = (("coach", "seat_number"),)


class TrainRun(models.Model):
    run_id = models.AutoField(primary_key=True)
    train = models.ForeignKey(Train, on_delete=models.DO_NOTHING, db_column="train_id")
    journey_date = models.DateField()
    run_status = models.CharField(max_length=20, default="SCHEDULED")

    class Meta:
        db_table = "train_run"
        managed = False
        unique_together = (("train", "journey_date"),)


class Booking(models.Model):
    pnr = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AppUser, on_delete=models.DO_NOTHING, db_column="user_id")
    run = models.ForeignKey(TrainRun, on_delete=models.DO_NOTHING, db_column="run_id")
    source_station = models.ForeignKey(Station, on_delete=models.DO_NOTHING, db_column="source_station_id", related_name="src_bookings")
    dest_station = models.ForeignKey(Station, on_delete=models.DO_NOTHING, db_column="dest_station_id", related_name="dst_bookings")
    class_code = models.CharField(max_length=10)
    booking_type = models.CharField(max_length=10, default="GENERAL")
    status = models.CharField(max_length=20, default="PENDING")
    booking_time = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "booking"
        managed = False


class RunSeat(models.Model):
    run = models.ForeignKey(TrainRun, on_delete=models.DO_NOTHING, db_column="run_id", primary_key=True)
    seat = models.ForeignKey(Seat, on_delete=models.DO_NOTHING, db_column="seat_id")
    quota_type = models.CharField(max_length=10, default="GENERAL")
    seat_status = models.CharField(max_length=20, default="AVAILABLE")
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    held_by_pnr = models.ForeignKey(Booking, on_delete=models.DO_NOTHING, db_column="held_by_pnr", null=True, blank=True)
    version_no = models.IntegerField(default=0)

    class Meta:
        db_table = "run_seat"
        managed = False
        unique_together = (("run", "seat"),)


class Passenger(models.Model):
    pnr = models.ForeignKey(Booking, on_delete=models.DO_NOTHING, db_column="pnr", primary_key=True)
    passenger_seq = models.IntegerField()
    name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    id_proof_type = models.CharField(max_length=20)
    id_proof_no = models.CharField(max_length=50)
    fare_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="CONFIRMED")
    run_id = models.IntegerField(null=True, blank=True)
    seat_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "passenger"
        managed = False
        unique_together = (("pnr", "passenger_seq"),)


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    pnr = models.ForeignKey(Booking, on_delete=models.DO_NOTHING, db_column="pnr")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default="SUCCESS")
    txn_ref = models.CharField(max_length=64, unique=True)
    idempotency_key = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment"
        managed = False


class Cancellation(models.Model):
    cancellation_id = models.AutoField(primary_key=True)
    pnr = models.OneToOneField(Booking, on_delete=models.DO_NOTHING, db_column="pnr")
    cancelled_at = models.DateTimeField(auto_now_add=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()

    class Meta:
        db_table = "cancellation"
        managed = False


class AuditLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    table_name = models.CharField(max_length=64)
    record_id = models.CharField(max_length=64)
    action = models.CharField(max_length=20)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        managed = False


# Relational Views (Read-Only)
class VPassengerAge(models.Model):
    passenger_id = models.IntegerField(primary_key=True)
    pnr = models.BigIntegerField()
    passenger_seq = models.IntegerField()
    name = models.CharField(max_length=100)
    dob = models.DateField()
    current_age = models.IntegerField()
    gender = models.CharField(max_length=10)
    fare_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)

    class Meta:
        db_table = "v_passenger_age"
        managed = False


class VTrainRoute(models.Model):
    train_id = models.IntegerField(primary_key=True)
    train_number = models.CharField(max_length=10)
    train_name = models.CharField(max_length=100)
    train_type = models.CharField(max_length=20)
    stop_seq = models.IntegerField()
    station_id = models.IntegerField()
    station_code = models.CharField(max_length=10)
    station_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    day_offset = models.IntegerField()
    distance_km = models.IntegerField()
    halt_duration_minutes = models.IntegerField()

    class Meta:
        db_table = "v_train_route"
        managed = False


class VRunAvailability(models.Model):
    run_id = models.IntegerField(primary_key=True)
    train_id = models.IntegerField()
    train_number = models.CharField(max_length=10)
    train_name = models.CharField(max_length=100)
    journey_date = models.DateField()
    class_code = models.CharField(max_length=10)
    class_name = models.CharField(max_length=50)
    quota_type = models.CharField(max_length=10)
    total_capacity = models.IntegerField()
    available_seats = models.IntegerField()
    held_seats = models.IntegerField()
    booked_seats = models.IntegerField()

    class Meta:
        db_table = "v_run_availability"
        managed = False


class VBookingSummary(models.Model):
    pnr = models.BigIntegerField(primary_key=True)
    user_id = models.IntegerField()
    customer_name = models.CharField(max_length=100)
    customer_email = models.CharField(max_length=100)
    train_number = models.CharField(max_length=10)
    train_name = models.CharField(max_length=100)
    journey_date = models.DateField()
    source_station = models.CharField(max_length=10)
    dest_station = models.CharField(max_length=10)
    class_code = models.CharField(max_length=10)
    booking_type = models.CharField(max_length=10)
    status = models.CharField(max_length=20)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    booking_time = models.DateTimeField()
    passenger_count = models.IntegerField()

    class Meta:
        db_table = "v_booking_summary"
        managed = False


class VAdminRevenue(models.Model):
    journey_date = models.DateField(primary_key=True)
    train_number = models.CharField(max_length=10)
    train_name = models.CharField(max_length=100)
    class_code = models.CharField(max_length=10)
    total_confirmed_tickets = models.IntegerField()
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    total_cancellations = models.IntegerField()
    total_refunded = models.DecimalField(max_digits=12, decimal_places=2)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "v_admin_revenue"
        managed = False
