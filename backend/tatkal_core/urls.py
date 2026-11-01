# Owner: Person A
"""
URL Configuration for tatkal_core project.
Routes /api/* to booking_engine.urls.
"""

from django.urls import path, include

urlpatterns = [
    path("api/", include("booking_engine.urls")),
]
