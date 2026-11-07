# Owner: Person A
"""
High-concurrency Tatkal and General ticket booking endpoints.
Invokes MySQL `sp_book_tickets` stored procedure with row-level locking (`SELECT ... FOR UPDATE SKIP LOCKED`),
exponential backoff deadlock retry (MySQL 1213), and request rate limiting.
"""

import json
import time
import random
from datetime import datetime, date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection, connections
import pymysql

from .models import Booking, Passenger, AppUser
from .serializers import BookingCreateRequestSerializer
from .permissions import IsAuthenticatedCustom
from .throttling import TatkalBurstThrottle, TatkalSustainedThrottle

MAX_DEADLOCK_RETRIES = 5
BASE_BACKOFF_MS = 50

class BookTicketView(APIView):
    permission_classes = [IsAuthenticatedCustom]
    throttle_classes = [TatkalBurstThrottle, TatkalSustainedThrottle]

    def post(self, request):
        serializer = BookingCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid booking parameters",
                    "details": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user_id = request.user.user_id

        # Format passenger details JSON matching sp_book_tickets schema:
        # name, dob, gender, id_proof_type, id_proof_no
        passengers_list = []
        for p in data["passengers"]:
            # Calculate approximate DOB from age if DOB not directly supplied
            age = p.get("age", 25)
            birth_year = date.today().year - age
            dob_str = str(p.get("dob") or f"{birth_year}-01-01")

            passengers_list.append({
                "name": p["passenger_name"],
                "dob": dob_str,
                "gender": p["gender"],
                "id_proof_type": p["id_card_type"],
                "id_proof_no": p["id_card_number"]
            })
        passengers_json = json.dumps(passengers_list)

        retries = 0
        while retries < MAX_DEADLOCK_RETRIES:
            try:
                with connections["default"].cursor() as cursor:
                    # sp_book_tickets(p_user_id, p_run_id, p_class_code, p_src_id, p_dst_id, p_booking_type, p_passengers_json, OUT p_pnr, OUT p_status, OUT p_message)
                    cursor.execute(
                        """
                        CALL sp_book_tickets(%s, %s, %s, %s, %s, %s, %s, @p_pnr, @p_status, @p_message);
                        """,
                        [
                            user_id,
                            data["run_id"],
                            data["class_code"],
                            data["source_station_id"],
                            data["dest_station_id"],
                            data["booking_type"],
                            passengers_json
                        ]
                    )

                    cursor.execute("SELECT @p_pnr, @p_status, @p_message;")
                    out_row = cursor.fetchone()
                    pnr, booking_status, message = out_row

                    if booking_status == "DEADLOCK_RETRY":
                        retries += 1
                        if retries >= MAX_DEADLOCK_RETRIES:
                            return Response({"error": {"code": "HIGH_CONCURRENCY_DEADLOCK", "message": "Please retry in a moment."}}, status=503)
                        time.sleep((BASE_BACKOFF_MS * 2 ** retries + random.randint(10, 50)) / 1000)
                        continue

                    if booking_status != "PENDING" or not pnr:
                        return Response({
                            "error": {
                                "code": "BOOKING_FAILED",
                                "message": message or "Could not secure requested seats.",
                                "details": {"status": booking_status}
                            }
                        }, status=status.HTTP_409_CONFLICT)

                    # Fetch assigned passenger seats and total fare
                    cursor.execute(
                        """
                        SELECT b.total_fare, b.booking_time, b.expires_at
                        FROM booking b WHERE b.pnr = %s
                        """,
                        [pnr]
                    )
                    b_info = cursor.fetchone()
                    total_fare = float(b_info[0]) if b_info else 0.0
                    booking_time = b_info[1].isoformat() if b_info and b_info[1] else None
                    expires_at = b_info[2].isoformat() if b_info and b_info[2] else None

                    cursor.execute(
                        """
                        SELECT 
                            p.name, p.dob, p.gender, p.id_proof_type, p.id_proof_no,
                            c.coach_number, s.seat_number, s.berth_type, p.fare_amount
                        FROM passenger p
                        JOIN seat s ON p.seat_id = s.seat_id
                        JOIN coach c ON s.coach_id = c.coach_id
                        WHERE p.pnr = %s
                        """,
                        [pnr]
                    )
                    p_rows = cursor.fetchall()
                    assigned_passengers = []
                    for pr in p_rows:
                        assigned_passengers.append({
                            "passenger_name": pr[0],
                            "dob": str(pr[1]),
                            "gender": pr[2],
                            "id_card_type": pr[3],
                            "id_card_number": pr[4],
                            "coach_code": pr[5],
                            "seat_number": pr[6],
                            "berth_type": pr[7],
                            "seat_fare": float(pr[8])
                        })

                    return Response({
                        "message": message or "Seats placed on hold successfully. Complete payment to confirm.",
                        "booking": {
                            "pnr": str(pnr),
                            "booking_id": pnr,  # PNR is the primary key in 01_schema.sql
                            "status": "HOLD",
                            "total_fare": total_fare,
                            "booking_type": data["booking_type"],
                            "class_code": data["class_code"],
                            "booking_time": booking_time,
                            "expires_at": expires_at,
                            "passengers": assigned_passengers
                        }
                    }, status=status.HTTP_201_CREATED)

            except Exception as e:
                err_code = getattr(e, "args", [None])[0]
                if err_code == 1213 or "Deadlock found" in str(e):
                    retries += 1
                    sleep_time = (BASE_BACKOFF_MS * (2 ** retries) + random.randint(10, 50)) / 1000.0
                    time.sleep(sleep_time)
                    if retries >= MAX_DEADLOCK_RETRIES:
                        return Response({
                            "error": {
                                "code": "HIGH_CONCURRENCY_DEADLOCK",
                                "message": "High traffic contention. Please try booking again in a moment.",
                                "details": {"retries": retries}
                            }
                        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                else:
                    return Response({
                        "error": {
                            "code": "DATABASE_ERROR",
                            "message": str(e),
                            "details": {}
                        }
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserBookingsListView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request):
        user_id = request.user.user_id
        with connections["readonly"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    b.pnr, b.status, b.booking_type, b.class_code, b.total_fare,
                    b.booking_time, b.expires_at,
                    t.train_number, t.train_name, tr.journey_date,
                    src.station_code AS src_code, src.station_name AS src_name,
                    dst.station_code AS dst_code, dst.station_name AS dst_name,
                    COUNT(p.passenger_seq) AS passenger_count
                FROM booking b
                JOIN train_run tr ON b.run_id = tr.run_id
                JOIN train t ON tr.train_id = t.train_id
                JOIN station src ON b.source_station_id = src.station_id
                JOIN station dst ON b.dest_station_id = dst.station_id
                LEFT JOIN passenger p ON b.pnr = p.pnr
                WHERE b.user_id = %s
                GROUP BY b.pnr, b.status, b.booking_type, b.class_code, b.total_fare,
                         b.booking_time, b.expires_at, t.train_number, t.train_name, tr.journey_date,
                         src.station_code, src.station_name, dst.station_code, dst.station_name
                ORDER BY b.booking_time DESC
                """,
                [user_id]
            )
            rows = cursor.fetchall()
            bookings = []
            for r in rows:
                bookings.append({
                    "booking_id": r[0],
                    "pnr": str(r[0]),
                    "status": r[1],
                    "booking_type": r[2],
                    "class_code": r[3],
                    "total_fare": float(r[4]),
                    "booking_time": r[5].isoformat() if r[5] else None,
                    "expires_at": r[6].isoformat() if r[6] else None,
                    "train_number": r[7],
                    "train_name": r[8],
                    "journey_date": r[9].isoformat() if r[9] else None,
                    "source": {"code": r[10], "name": r[11]},
                    "destination": {"code": r[12], "name": r[13]},
                    "passenger_count": r[14]
                })
            return Response(bookings)


class BookingDetailByPnrView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request, pnr):
        with connections["readonly"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    b.pnr, b.user_id, b.status, b.booking_type, b.class_code, b.total_fare,
                    b.booking_time, b.expires_at,
                    t.train_number, t.train_name, tr.journey_date,
                    src.station_code AS src_code, src.station_name AS src_name,
                    dst.station_code AS dst_code, dst.station_name AS dst_name
                FROM booking b
                JOIN train_run tr ON b.run_id = tr.run_id
                JOIN train t ON tr.train_id = t.train_id
                JOIN station src ON b.source_station_id = src.station_id
                JOIN station dst ON b.dest_station_id = dst.station_id
                WHERE b.pnr = %s
                """,
                [pnr]
            )
            b_row = cursor.fetchone()
            if not b_row:
                return Response({"error": {"code": "NOT_FOUND", "message": f"PNR {pnr} not found."}}, status=status.HTTP_404_NOT_FOUND)

            if request.user.role != "ADMIN" and b_row[1] != request.user.user_id:
                return Response({"error": {"code": "FORBIDDEN", "message": "Access denied."}}, status=status.HTTP_403_FORBIDDEN)

            # Fetch passengers
            cursor.execute(
                """
                SELECT 
                    p.passenger_seq, p.name, p.dob, p.gender, p.id_proof_type, p.id_proof_no,
                    c.coach_number, s.seat_number, s.berth_type, p.fare_amount
                FROM passenger p
                LEFT JOIN seat s ON p.seat_id = s.seat_id
                LEFT JOIN coach c ON s.coach_id = c.coach_id
                WHERE p.pnr = %s
                ORDER BY p.passenger_seq
                """,
                [pnr]
            )
            p_rows = cursor.fetchall()
            passengers = []
            for pr in p_rows:
                passengers.append({
                    "passenger_id": pr[0],
                    "passenger_name": pr[1],
                    "dob": str(pr[2]),
                    "gender": pr[3],
                    "id_card_type": pr[4],
                    "id_card_number": pr[5],
                    "coach_code": pr[6],
                    "seat_number": pr[7],
                    "berth_type": pr[8],
                    "seat_fare": float(pr[9])
                })

            # Fetch payments
            cursor.execute(
                """
                SELECT payment_id, idempotency_key, txn_ref, amount, method, status, created_at
                FROM payment WHERE pnr = %s
                """,
                [pnr]
            )
            pay_rows = cursor.fetchall()
            payments = []
            for pyr in pay_rows:
                payments.append({
                    "payment_id": pyr[0],
                    "idempotency_key": pyr[1],
                    "transaction_id": pyr[2],
                    "amount": float(pyr[3]),
                    "payment_method": pyr[4],
                    "payment_status": pyr[5],
                    "payment_time": pyr[6].isoformat() if pyr[6] else None
                })

            # Fetch cancellation if exists
            cursor.execute(
                """
                SELECT cancellation_id, cancelled_at, refund_amount, reason
                FROM cancellation WHERE pnr = %s
                """,
                [pnr]
            )
            can_row = cursor.fetchone()
            cancellation = None
            if can_row:
                cancellation = {
                    "cancellation_id": can_row[0],
                    "cancellation_time": can_row[1].isoformat() if can_row[1] else None,
                    "refund_amount": float(can_row[2]),
                    "reason": can_row[3]
                }

            return Response({
                "booking_id": b_row[0],
                "pnr": str(b_row[0]),
                "user_id": b_row[1],
                "status": b_row[2],
                "booking_type": b_row[3],
                "class_code": b_row[4],
                "total_fare": float(b_row[5]),
                "booking_time": b_row[6].isoformat() if b_row[6] else None,
                "expires_at": b_row[7].isoformat() if b_row[7] else None,
                "train_number": b_row[8],
                "train_name": b_row[9],
                "journey_date": b_row[10].isoformat() if b_row[10] else None,
                "source": {"code": b_row[11], "name": b_row[12]},
                "destination": {"code": b_row[13], "name": b_row[14]},
                "passengers": passengers,
                "payments": payments,
                "cancellation": cancellation
            })
