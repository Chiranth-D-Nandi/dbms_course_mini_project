# Owner: Person A
"""
Station and Train search endpoints.
Invokes MySQL FULLTEXT indexing for station autocomplete and
executes `sp_search_trains` stored procedure for route matching and seat availability.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connections
from .models import Station, Train, TrainStop

class StationListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            with connections["readonly"].cursor() as cursor:
                cursor.execute("SELECT station_id, station_code, station_name, city, state FROM station ORDER BY station_name LIMIT 50")
                rows = cursor.fetchall()
                results = [{"station_id": r[0], "station_code": r[1], "station_name": r[2], "city": r[3], "state": r[4]} for r in rows]
                return Response(results)

        with connections["readonly"].cursor() as cursor:
            # Query FULLTEXT index (station_name, city) or code prefix
            cursor.execute(
                """
                SELECT station_id, station_code, station_name, city, state
                FROM station
                WHERE MATCH(station_name, city) AGAINST(%s IN NATURAL LANGUAGE MODE)
                   OR station_code LIKE %s
                   OR station_name LIKE %s
                   OR city LIKE %s
                LIMIT 20
                """,
                [query, f"{query}%", f"{query}%", f"{query}%"]
            )
            rows = cursor.fetchall()
            results = [{"station_id": r[0], "station_code": r[1], "station_name": r[2], "city": r[3], "state": r[4]} for r in rows]
            return Response(results)


class TrainSearchView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        source_param = request.query_params.get("source", "").strip()
        dest_param = request.query_params.get("dest", "").strip()
        journey_date = request.query_params.get("date", "").strip()
        quota = request.query_params.get("quota", "GENERAL").strip() or "GENERAL"

        if not (source_param and dest_param and journey_date):
            return Response({
                "error": {
                    "code": "MISSING_PARAMETERS",
                    "message": "source, dest, and date parameters are required.",
                    "details": {}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        with connections["readonly"].cursor() as cursor:
            # Resolve source
            if source_param.isdigit():
                cursor.execute("SELECT station_id, station_code, station_name FROM station WHERE station_id = %s", [int(source_param)])
            else:
                cursor.execute("SELECT station_id, station_code, station_name FROM station WHERE station_code = %s", [source_param.upper()])
            src_row = cursor.fetchone()
            if not src_row:
                return Response({"error": {"code": "STATION_NOT_FOUND", "message": f"Source station '{source_param}' not found."}}, status=status.HTTP_404_NOT_FOUND)
            source_id = src_row[0]

            # Resolve destination
            if dest_param.isdigit():
                cursor.execute("SELECT station_id, station_code, station_name FROM station WHERE station_id = %s", [int(dest_param)])
            else:
                cursor.execute("SELECT station_id, station_code, station_name FROM station WHERE station_code = %s", [dest_param.upper()])
            dst_row = cursor.fetchone()
            if not dst_row:
                return Response({"error": {"code": "STATION_NOT_FOUND", "message": f"Destination station '{dest_param}' not found."}}, status=status.HTTP_404_NOT_FOUND)
            dest_id = dst_row[0]

            # Execute sp_search_trains(p_src_station_id, p_dst_station_id, p_journey_date)
            cursor.callproc("sp_search_trains", (source_id, dest_id, journey_date))
            rows = cursor.fetchall()

            columns = [col[0] for col in cursor.description]
            trains = []
            for r in rows:
                row_dict = {}
                for col_name, val in zip(columns, r):
                    if hasattr(val, "total_seconds"):  # timedelta
                        total_secs = int(val.total_seconds())
                        row_dict[col_name] = f"{total_secs // 3600:02d}:{(total_secs % 3600) // 60:02d}:{total_secs % 60:02d}"
                    elif hasattr(val, "isoformat"):  # date / datetime
                        row_dict[col_name] = val.isoformat()
                    elif isinstance(val, (int, float, str, bool)) or val is None:
                        row_dict[col_name] = val
                    else:
                        row_dict[col_name] = str(val)
                trains.append(row_dict)

            return Response({
                "source": {"station_id": src_row[0], "station_code": src_row[1], "station_name": src_row[2]},
                "destination": {"station_id": dst_row[0], "station_code": dst_row[1], "station_name": dst_row[2]},
                "journey_date": journey_date,
                "quota": quota,
                "count": len(trains),
                "trains": trains
            })


class TrainDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk):
        with connections["readonly"].cursor() as cursor:
            cursor.execute("SELECT train_id, train_number, train_name, train_type, is_active FROM train WHERE train_id = %s", [pk])
            t_row = cursor.fetchone()
            if not t_row:
                return Response({"error": {"code": "NOT_FOUND", "message": f"Train {pk} not found."}}, status=status.HTTP_404_NOT_FOUND)

            cursor.execute(
                """
                SELECT ts.stop_seq, s.station_id, s.station_code, s.station_name, s.city,
                       ts.arrival_time, ts.departure_time, ts.day_offset, ts.distance_km
                FROM train_stop ts
                JOIN station s ON ts.station_id = s.station_id
                WHERE ts.train_id = %s
                ORDER BY ts.stop_seq ASC
                """,
                [pk]
            )
            s_rows = cursor.fetchall()
            stops = []
            for sr in s_rows:
                stops.append({
                    "stop_sequence": sr[0],
                    "station_id": sr[1],
                    "station_code": sr[2],
                    "station_name": sr[3],
                    "city": sr[4],
                    "arrival_time": str(sr[5]) if sr[5] else None,
                    "departure_time": str(sr[6]) if sr[6] else None,
                    "day_offset": sr[7],
                    "distance_km": sr[8]
                })

            return Response({
                "train_id": t_row[0],
                "train_number": t_row[1],
                "train_name": t_row[2],
                "train_type": t_row[3],
                "is_active": bool(t_row[4]),
                "stops": stops
            })
