# Owner: Person A
"""
URL Routing for tatkal_core booking_engine application.
Matches OpenAPI 3 specification defined in docs/api_contract.yaml.
"""

from django.urls import path
from .auth_views import RegisterView, LoginView, ProfileView
from .train_views import StationListView, TrainSearchView, TrainDetailView
from .seat_views import SeatMapView, TatkalStatusView
from .booking_views import BookTicketView, UserBookingsListView, BookingDetailByPnrView
from .payment_views import ConfirmPaymentView, CancelBookingView
from .search_views import VectorTrainSearchView, VectorFaqSearchView
from .admin_views import (
    AdminRevenueView,
    AdminAuditLogsView,
    AdminCreateRunView,
    AdminReleaseHoldsView,
)

urlpatterns = [
    # Auth endpoints
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/me", ProfileView.as_view(), name="auth-me"),

    # Stations and Train Search endpoints
    path("stations/", StationListView.as_view(), name="stations-list"),
    path("trains/search/", TrainSearchView.as_view(), name="trains-search"),
    path("trains/<int:pk>/", TrainDetailView.as_view(), name="train-detail"),

    # Seat Map and Tatkal Timing endpoints
    path("runs/<int:run_id>/seats/", SeatMapView.as_view(), name="run-seat-map"),
    path("tatkal/status/", TatkalStatusView.as_view(), name="tatkal-status"),

    # Booking Engine endpoints
    path("bookings/", BookTicketView.as_view(), name="booking-create"),
    path("bookings/my/", UserBookingsListView.as_view(), name="user-bookings"),
    path("bookings/<str:pnr>/", BookingDetailByPnrView.as_view(), name="booking-detail"),
    path("bookings/<str:pnr>/cancel/", CancelBookingView.as_view(), name="booking-cancel"),

    # Payment Confirmation endpoint
    path("payments/confirm/", ConfirmPaymentView.as_view(), name="payment-confirm"),

    # Semantic Vector Search endpoints (ChromaDB)
    path("search/trains/", VectorTrainSearchView.as_view(), name="vector-search-trains"),
    path("search/faq/", VectorFaqSearchView.as_view(), name="vector-search-faq"),

    # Admin Management & Analytics endpoints
    path("admin/revenue/", AdminRevenueView.as_view(), name="admin-revenue"),
    path("admin/audit-logs/", AdminAuditLogsView.as_view(), name="admin-audit-logs"),
    path("admin/runs/", AdminCreateRunView.as_view(), name="admin-create-run"),
    path("admin/release-holds/", AdminReleaseHoldsView.as_view(), name="admin-release-holds"),
]
