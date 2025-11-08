"""
Role-based access control mixins for EventEase views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


class RoleRequiredMixin(AccessMixin):
    """Mixin to require specific user roles."""
    allowed_roles = []  # List of allowed roles: ['ADMIN', 'USER']
    require_superuser = False  # If True, requires Django superuser
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check superuser requirement
        if self.require_superuser:
            if not request.user.is_superuser:
                messages.error(request, 'This page requires superuser access.')
                return self.handle_no_permission()
            return super().dispatch(request, *args, **kwargs)
        
        # Check role requirement
        if self.allowed_roles:
            # Django superusers bypass role checks
            if request.user.is_superuser:
                return super().dispatch(request, *args, **kwargs)
            
            # Get user profile
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'User profile not found.')
                return self.handle_no_permission()
            
            user_role = request.user.profile.role
            if user_role not in self.allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('landing')


class SuperAdminRequiredMixin(RoleRequiredMixin):
    """Mixin that requires Django superuser (Super Admin)."""
    require_superuser = True


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin that requires ADMIN role."""
    allowed_roles = ['ADMIN']


class UserOrAboveMixin(RoleRequiredMixin):
    """Mixin that allows any authenticated user (users and above)."""
    allowed_roles = ['USER', 'ADMIN']


def has_role(user, roles):
    """Helper function to check if user has one of the specified roles."""
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, 'profile'):
        return False
    
    return user.profile.role in roles


def is_admin(user):
    """Helper function to check if user is Admin."""
    return has_role(user, ['ADMIN'])


def is_super_admin(user):
    """Helper function to check if user is Super Admin (Django superuser)."""
    return user.is_authenticated and user.is_superuser

