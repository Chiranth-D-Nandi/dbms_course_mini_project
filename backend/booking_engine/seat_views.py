# Owner: Person A
"""
Seat layout, seat map, and real-time Tatkal window calculation endpoints.
Provides coach-by-coach layout and seat status (AVAILABLE, HELD, BOOKED).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connections
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from .models import TrainRun, SeatClass

def get_tatkal_window_info(journey_date: date, class_code: str):
    """
    Calculates whether the Tatkal booking window is OPEN, NOT_YET_OPEN, or CLOSED.
    Tatkal opens 1 day prior to journey_date:
    - 10:00 AM IST for AC classes (1A, 2A, 3A, CC, EC)
    - 11:00 AM IST for Non-AC classes (SL, 2S)
    """
    is_ac = class_code in ("1A", "2A", "3A", "CC", "EC")
    opening_time_str = "10:00:00" if is_ac else "11:00:00"
    open_hour = 10 if is_ac else 11

    booking_open_date = journey_date - timedelta(days=1)
    open_dt = datetime.combine(booking_open_date, time(open_hour, 0, 0))
    close_dt = datetime.combine(journey_date, time(23, 59, 59))

    now = datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)

    if now < open_dt:
        time_status = "NOT_OPEN"
        seconds_remaining = int((open_dt - now).total_seconds())
    elif now > close_dt:
        time_status = "CLOSED"
        seconds_remaining = 0
    else:
        time_status = "OPEN"
        seconds_remaining = int((close_dt - now).total_seconds())

    return {
        "class_code": class_code,
        "is_ac": is_ac,
        "opening_time": opening_time_str,
        "opens_at": open_dt.isoformat(),
        "closes_at": close_dt.isoformat(),
        "current_time": now.isoformat(),
        "status": time_status,
        "seconds_remaining": max(0, seconds_remaining)
    }

class SeatMapView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, run_id):
        class_code = request.query_params.get("class", "").strip() or None
        quota = request.query_params.get("quota", "GENERAL").strip() or "GENERAL"

        with connections["readonly"].cursor() as cursor:
            cursor.execute(
                """
                SELECT tr.run_id, tr.journey_date, tr.run_status, t.train_id, t.train_number, t.train_name
                FROM train_run tr
                JOIN train t ON tr.train_id = t.train_id
                WHERE tr.run_id = %s
                """,
                [run_id]
            )
            run_row = cursor.fetchone()
            if not run_row:
                return Response({"error": {"code": "RUN_NOT_FOUND", "message": f"Run {run_id} not found."}}, status=status.HTTP_404_NOT_FOUND)

            journey_date = run_row[1]

            query = """
                SELECT 
                    c.coach_id,
                    c.coach_number,
                    c.class_code,
                    s.seat_id,
                    s.seat_number,
                    s.berth_type,
                    rs.quota_type,
                    rs.seat_status AS effective_status,
                    rs.hold_expires_at
                FROM coach c
                JOIN seat s ON c.coach_id = s.coach_id
                JOIN run_seat rs ON s.seat_id = rs.seat_id AND rs.run_id = %s
                WHERE c.train_id = %s
            """
            params = [run_id, run_row[3]]

            if class_code:
                query += " AND c.class_code = %s"
                params.append(class_code)

            if quota:
                query += " AND rs.quota_type = %s"
                params.append(quota)

            query += " ORDER BY c.coach_number, s.seat_number"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            coaches_dict = {}
            for r in rows:
                c_code = r[1]
                if c_code not in coaches_dict:
                    coaches_dict[c_code] = {
                        "coach_id": r[0],
                        "coach_code": c_code,
                        "class_code": r[2],
                        "seats": []
                    }
                coaches_dict[c_code]["seats"].append({
                    "seat_id": r[3],
                    "seat_number": r[4],
                    "berth_type": r[5],
                    "quota": r[6],
                    "status": r[7],
                    "held_until": r[8].isoformat() if r[8] else None
                })

            tatkal_info = get_tatkal_window_info(journey_date, class_code or "3A")

            return Response({
                "run_id": run_id,
                "train_number": run_row[4],
                "train_name": run_row[5],
                "journey_date": journey_date.isoformat(),
                "tatkal_info": tatkal_info,
                "coaches": list(coaches_dict.values())
            })


class TatkalStatusView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        run_id = request.query_params.get("run_id")
        class_code = request.query_params.get("class", "3A")

        if not run_id:
            return Response({"error": {"code": "MISSING_PARAM", "message": "run_id is required."}}, status=status.HTTP_400_BAD_REQUEST)

        try:
            run = TrainRun.objects.using("readonly").get(run_id=run_id)
            info = get_tatkal_window_info(run.journey_date, class_code)
            return Response(info)
        except TrainRun.DoesNotExist:
            return Response({"error": {"code": "RUN_NOT_FOUND", "message": f"Run {run_id} not found."}}, status=status.HTTP_404_NOT_FOUND)
