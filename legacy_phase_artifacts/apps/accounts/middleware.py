from django.contrib import messages
from django.shortcuts import redirect


class ForcePasswordChangeMiddleware:
    """Keep temporary credentials from being used beyond the password form."""

    EXEMPT_URL_NAMES = {
        "login",
        "logout",
        "password_change",
        "password_reset",
        "password_reset_done",
        "password_reset_confirm",
        "password_reset_complete",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user.is_authenticated or not user.must_change_password:
            return None

        match = request.resolver_match
        if match and match.namespace == "accounts" and match.url_name in self.EXEMPT_URL_NAMES:
            return None

        messages.warning(request, "Please change your temporary password before continuing.")
        return redirect("accounts:password_change")
