from .models import ActivityLog
from .threadlocals import get_current_ip


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def module_from_path(path):
    cleaned = path.strip("/")
    if not cleaned:
        return "dashboard"
    return cleaned.split("/")[0]


def log_activity(
    user=None,
    action="Action",
    module="",
    description="",
    request=None,
    method="",
    path="",
    status_code=None,
):
    if request:
        user = user or (request.user if getattr(request, "user", None) and request.user.is_authenticated else None)
        method = method or getattr(request, "method", "") or ""
        path = path or getattr(request, "path", "") or ""
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
    else:
        ip_address = get_current_ip()
        user_agent = ""

    return ActivityLog.objects.create(
        user=user,
        action=action,
        module=module or module_from_path(path),
        description=description,
        method=method,
        path=path,
        status_code=status_code,
        ip_address=ip_address,
        user_agent=user_agent,
    )
