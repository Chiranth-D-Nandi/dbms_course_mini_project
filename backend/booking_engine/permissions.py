# Owner: Person A
"""
Role-based access control (RBAC) permissions for tatkal_core.
Enforces ADMIN vs CUSTOMER authorization boundaries.
"""

from rest_framework.permissions import BasePermission

class IsAuthenticatedCustom(BasePermission):
    """Allows access only to authenticated users."""
    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "is_authenticated", False))


class IsAdminUserRole(BasePermission):
    """Allows access only to users with the ADMIN role."""
    def has_permission(self, request, view):
        if not bool(request.user and getattr(request.user, "is_authenticated", False)):
            return False
        return getattr(request.user, "role", None) == "ADMIN"


class IsCustomerUserRole(BasePermission):
    """Allows access only to users with the CUSTOMER role."""
    def has_permission(self, request, view):
        if not bool(request.user and getattr(request.user, "is_authenticated", False)):
            return False
        return getattr(request.user, "role", None) == "CUSTOMER"
