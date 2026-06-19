from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """Restrict view access to specific user roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'Profile not found.')
                return redirect('login')
            if request.user.profile.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    return role_required('admin')(view_func)


def rider_required(view_func):
    return role_required('rider')(view_func)


def customer_required(view_func):
    return role_required('customer')(view_func)


def send_notification(user, notif_type, message, order=None):
    """Create a notification for a user."""
    from .models import Notification
    Notification.objects.create(
        user=user,
        type=notif_type,
        message=message,
        order=order
    )