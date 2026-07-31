import threading


_storage = threading.local()


def set_current_request(request):
    _storage.request = request


def clear_current_request():
    if hasattr(_storage, "request"):
        del _storage.request


def get_current_request():
    return getattr(_storage, "request", None)


def get_current_user():
    request = get_current_request()
    if not request:
        return None
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return user
    return None


def get_current_ip():
    request = get_current_request()
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
