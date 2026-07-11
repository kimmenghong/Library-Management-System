from .threadlocals import clear_current_request, set_current_request
from .utils import log_activity, module_from_path


class CurrentRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        try:
            return self.get_response(request)
        finally:
            clear_current_request()


class ActivityLogMiddleware:
    TRACKED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    SKIPPED_PREFIXES = ("/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self.should_log(request):
            module = module_from_path(request.path)
            log_activity(
                request=request,
                action=f"{request.method} {module}",
                module=module,
                description=f"{request.method} request to {request.path}",
                status_code=response.status_code,
            )
        return response

    def should_log(self, request):
        if request.method not in self.TRACKED_METHODS:
            return False
        if any(request.path.startswith(prefix) for prefix in self.SKIPPED_PREFIXES):
            return False
        return True
