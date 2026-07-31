import logging

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

audit_logger = logging.getLogger("library.audit")


def _client_ip(request):
    if request is None:
        return "unknown"
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    audit_logger.info(
        "auth.login_success user_id=%s username=%s ip=%s",
        user.pk,
        user.get_username(),
        _client_ip(request),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is None:
        return
    audit_logger.info(
        "auth.logout user_id=%s username=%s ip=%s",
        user.pk,
        user.get_username(),
        _client_ip(request),
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get("username", "unknown")
    audit_logger.warning(
        "auth.login_failed username=%s ip=%s",
        username,
        _client_ip(request),
    )
