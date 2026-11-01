# Owner: Person A
"""
Admin management and analytics endpoints.
Restricted to ADMIN role (`IsAdminUserRole`).
Provides access to `v_admin_revenue`, `audit_log`, manual hold sweep, and run creation.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connections
from .permissions import IsAdminUserRole

class AdminRevenueView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        with connections["readonly"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    journey_date, train_number, train_name,
                    confirmed_bookings, total_revenue, cancellations,
                    total_refunds, net_revenue, occupancy_pct
                FROM v_admin_revenue
                ORDER BY journey_date DESC
                LIMIT 100
                """
            )
            rows = cursor.fetchall()
            data = []
            total_net = 0.0
            total_tickets = 0
            for r in rows:
                net = float(r[7] or 0.0)
                total_net += net
                total_tickets += int(r[3] or 0)
                data.append({
                    "journey_date": r[0].isoformat() if r[0] else None,
                    "train_number": r[1],
                    "train_name": r[2],
                    "total_confirmed_tickets": int(r[3] or 0),
                    "gross_revenue": float(r[4] or 0.0),
                    "total_cancellations": int(r[5] or 0),
                    "total_refunded": float(r[6] or 0.0),
                    "net_revenue": net,
                    "occupancy_pct": float(r[8] or 0.0)
                })
            return Response({
                "summary": {
                    "total_revenue": total_net,
                    "total_tickets_sold": total_tickets,
                    "report_rows": len(data)
                },
                "revenue_data": data
            })


class AdminAuditLogsView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        entity = request.query_params.get("entity")
        action = request.query_params.get("action")

        query = "SELECT log_id, table_name, record_id, action, old_value, new_value, changed_at FROM audit_log"
        params = []
        clauses = []
        if entity:
            clauses.append("table_name = %s")
            params.append(entity)
        if action:
            clauses.append("action = %s")
            params.append(action)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY changed_at DESC LIMIT 100"

        with connections["readonly"].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                logs.append({
                    "log_id": r[0],
                    "entity_name": r[1],
                    "entity_id": r[2],
                    "action": r[3],
                    "old_state": r[4],
                    "new_state": r[5],
                    "changed_by": "SYSTEM",
                    "changed_at": r[6].isoformat() if r[6] else None
                })
            return Response(logs)


class AdminCreateRunView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request):
        train_id = request.data.get("train_id")
        journey_date = request.data.get("journey_date")

        if not (train_id and journey_date):
            return Response({"error": {"code": "MISSING_PARAM", "message": "train_id and journey_date are required."}}, status=status.HTTP_400_BAD_REQUEST)

        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT run_id FROM train_run WHERE train_id = %s AND journey_date = %s", [train_id, journey_date])
            existing = cursor.fetchone()
            if existing:
                return Response({"error": {"code": "RUN_EXISTS", "message": f"Run already exists with ID {existing[0]}."}}, status=status.HTTP_409_CONFLICT)

            cursor.execute(
                "INSERT INTO train_run (train_id, journey_date, run_status) VALUES (%s, %s, 'SCHEDULED')",
                [train_id, journey_date]
            )
            run_id = cursor.lastrowid

            cursor.execute("CALL sp_generate_run_inventory(%s)", [run_id])

            return Response({
                "message": f"Run created successfully with ID {run_id} and inventory generated.",
                "run_id": run_id,
                "train_id": train_id,
                "journey_date": journey_date
            }, status=status.HTTP_201_CREATED)


class AdminReleaseHoldsView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request):
        with connections["default"].cursor() as cursor:
            cursor.execute("CALL sp_release_expired_holds(@p_released_count);")
            cursor.execute("SELECT @p_released_count;")
            count = cursor.fetchone()[0] or 0
            return Response({
                "message": f"Hold sweep completed. Released {count} expired seat holds.",
                "released_count": count
            }, status=status.HTTP_200_OK)
