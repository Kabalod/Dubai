from rest_framework.permissions import BasePermission


class IsPaidUser(BasePermission):
    message = 'Paid subscription required.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = getattr(getattr(user, 'profile', None), 'role', 'free')
        return role in ('paid', 'admin') or user.is_superuser


class IsAdminUserStrict(BasePermission):
    message = 'Admin access required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or getattr(getattr(user, 'profile', None), 'role', '') == 'admin'))


