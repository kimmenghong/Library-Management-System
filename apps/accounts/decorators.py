from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*role_slugs):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.has_role(*role_slugs):
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to access this page.")
            return redirect("accounts:dashboard")

        return wrapper

    return decorator


def role_permission_required(codename):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.has_role_permission(codename):
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to perform this action.")
            return redirect("accounts:dashboard")

        return wrapper

    return decorator
