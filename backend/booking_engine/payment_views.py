# Owner: Person A
"""
Payment confirmation and ticket cancellation endpoints.
Invokes MySQL `sp_confirm_payment` with idempotency verification and
`sp_cancel_booking` with graded refund calculation.
"""

import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connections
from .models import Booking, Payment
from .serializers import PaymentConfirmRequestSerializer, CancellationRequestSerializer
from .permissions import IsAuthenticatedCustom

class ConfirmPaymentView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    def post(self, request):
        payload = request.data.copy()
        payload["pnr"] = payload.get("pnr") or payload.get("booking_id")
        header_key = request.headers.get("Idempotency-Key")
        if header_key and payload.get("idempotency_key") and header_key != payload["idempotency_key"]:
            return Response({"error": {"code": "KEY_MISMATCH", "message": "Header and body payment keys differ."}}, status=400)
        payload["idempotency_key"] = header_key or payload.get("idempotency_key")
        serializer = PaymentConfirmRequestSerializer(data=payload)
        if not serializer.is_valid():
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid payment parameters", "details": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        pnr = data["pnr"]
        idempotency_key = data["idempotency_key"]
        method = data.get("payment_method", "UPI")

        # Map UPI, CREDIT_CARD, etc. to schema ENUM: 'UPI', 'CARD', 'NETBANKING'
        if "CARD" in method.upper():
            db_method = "CARD"
        elif "NET" in method.upper() or "BANK" in method.upper():
            db_method = "NETBANKING"
        else:
            db_method = "UPI"

        if not pnr:
            return Response({"error": {"code": "MISSING_PARAM", "message": "pnr is required."}}, status=status.HTTP_400_BAD_REQUEST)

        pnr = int(pnr)

        with connections["default"].cursor() as cursor:
            # Fetch booking total_fare
            cursor.execute("SELECT total_fare, status, user_id FROM booking WHERE pnr = %s", [pnr])
            b_row = cursor.fetchone()
            if not b_row:
                return Response({"error": {"code": "BOOKING_NOT_FOUND", "message": f"PNR {pnr} not found."}}, status=status.HTTP_404_NOT_FOUND)

            total_fare = b_row[0]
            if b_row[2] != request.user.user_id and request.user.role != "ADMIN":
                return Response({"error": {"code": "FORBIDDEN", "message": "This booking belongs to another customer."}}, status=403)
            txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"

            # sp_confirm_payment(p_pnr, p_amount, p_method, p_txn_ref, p_idempotency_key, OUT p_status, OUT p_message)
            cursor.execute(
                """
                CALL sp_confirm_payment(%s, %s, %s, %s, %s, @p_status, @p_message);
                """,
                [pnr, total_fare, db_method, txn_ref, idempotency_key]
            )
            cursor.execute("SELECT @p_status, @p_message;")
            out_row = cursor.fetchone()
            payment_status, message = out_row

            if payment_status != "SUCCESS":
                return Response({
                    "error": {
                        "code": "PAYMENT_FAILED",
                        "message": message or "Payment confirmation failed.",
                        "details": {"status": payment_status}
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve transaction details
            cursor.execute(
                """
                SELECT payment_id, idempotency_key, txn_ref, amount, method, status, created_at
                FROM payment WHERE idempotency_key = %s
                """,
                [idempotency_key]
            )
            pay_row = cursor.fetchone()
            cursor.execute("SELECT status FROM booking WHERE pnr = %s", [pnr])
            current_status = cursor.fetchone()[0]

            return Response({
                "message": message or "Payment confirmed and ticket issued successfully.",
                "booking": {
                    "pnr": str(pnr),
                    "status": current_status
                },
                "payment": {
                    "payment_id": pay_row[0] if pay_row else None,
                    "idempotency_key": pay_row[1] if pay_row else idempotency_key,
                    "transaction_id": pay_row[2] if pay_row else txn_ref,
                    "amount": float(pay_row[3]) if pay_row else float(total_fare),
                    "payment_method": pay_row[4] if pay_row else db_method,
                    "status": pay_row[5] if pay_row else "SUCCESS",
                    "payment_time": pay_row[6].isoformat() if pay_row and pay_row[6] else None
                }
            }, status=status.HTTP_200_OK)


class CancelBookingView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    def post(self, request, pnr):
        serializer = CancellationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid cancellation data", "details": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        reason = serializer.validated_data.get("reason", "Customer request") or "Customer requested cancellation"
        pnr = int(pnr)
        user_id = request.user.user_id

        with connections["default"].cursor() as cursor:
            # sp_cancel_booking(p_pnr, p_user_id, p_reason, OUT p_status, OUT p_refund_amount, OUT p_message)
            cursor.execute(
                """
                CALL sp_cancel_booking(%s, %s, %s, @p_status, @p_refund_amount, @p_message);
                """,
                [pnr, user_id, reason]
            )
            cursor.execute("SELECT @p_status, @p_refund_amount, @p_message;")
            out_row = cursor.fetchone()
            cancel_status, refund_amount, message = out_row

            if cancel_status not in ("SUCCESS", "CANCELLED"):
                return Response({
                    "error": {
                        "code": "CANCELLATION_FAILED",
                        "message": message or "Cancellation failed.",
                        "details": {"status": cancel_status}
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "message": message or "Ticket cancelled successfully.",
                "cancellation": {
                    "pnr": str(pnr),
                    "status": "CANCELLED",
                    "refund_amount": float(refund_amount) if refund_amount is not None else 0.0,
                    "reason": reason
                }
            }, status=status.HTTP_200_OK)
