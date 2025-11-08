"""
Template tags for authentication and role checks.
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def is_admin(context):
    """Safely check if the current user is an admin."""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    user = request.user
    if not hasattr(user, 'profile'):
        return False
    
    try:
        return user.profile.is_admin()
    except AttributeError:
        return False


@register.simple_tag(takes_context=True)
def is_super_admin(context):
    """Safely check if the current user is a super admin (Django superuser)."""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    return request.user.is_superuser


@register.simple_tag(takes_context=True)
def can_create_event(context):
    """Safely check if the current user can create events (admin)."""
    return is_admin(context)


@register.filter
def user_is_admin(user):
    """Filter to check if a user object is an admin."""
    if not user or not user.is_authenticated:
        return False
    
    if not hasattr(user, 'profile'):
        return False
    
    try:
        return user.profile.is_admin()
    except AttributeError:
        return False

