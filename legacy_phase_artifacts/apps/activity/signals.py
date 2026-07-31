from decimal import Decimal

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db import connection
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from .models import ActivityLog, AuditLog
from .threadlocals import get_current_ip, get_current_request, get_current_user
from .utils import log_activity


EXCLUDED_APPS = {"activity", "admin", "auth", "contenttypes", "sessions"}
TRACKED_APPS = {
    "accounts",
    "members",
    "catalog",
    "circulation",
    "fines",
    "notifications",
    "status_tracking",
}


def should_audit_model(sender):
    app_label = sender._meta.app_label
    return app_label in TRACKED_APPS and app_label not in EXCLUDED_APPS


def serialize_instance(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        if field.name == "password":
            data[field.name] = "[redacted]" if value else ""
            continue
        if hasattr(value, "pk"):
            value = value.pk
        if isinstance(value, Decimal):
            value = str(value)
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        elif value is not None:
            value = str(value) if field.get_internal_type() == "FileField" else value
        data[field.name] = value
    return data


def changed_values(old_values, new_values):
    old_changed = {}
    new_changed = {}
    for key, new_value in new_values.items():
        old_value = old_values.get(key)
        if old_value != new_value:
            old_changed[key] = old_value
            new_changed[key] = new_value
    return old_changed, new_changed


def create_audit_log(instance, action_type, old_values=None, new_values=None):
    if AuditLog._meta.db_table not in connection.introspection.table_names():
        return
    user = get_current_user()
    AuditLog.objects.create(
        user=user,
        app_label=instance._meta.app_label,
        model_name=instance._meta.object_name,
        object_id=str(instance.pk or ""),
        object_repr=str(instance)[:255],
        action_type=action_type,
        old_values=old_values or {},
        new_values=new_values or {},
        ip_address=get_current_ip(),
    )


@receiver(pre_save)
def capture_old_values(sender, instance, **kwargs):
    if not should_audit_model(sender) or not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    instance._audit_old_values = serialize_instance(old_instance)


@receiver(post_save)
def audit_saved_model(sender, instance, created, **kwargs):
    if not should_audit_model(sender):
        return
    new_values = serialize_instance(instance)
    if created:
        create_audit_log(instance, AuditLog.CREATE, new_values=new_values)
        return
    old_values = getattr(instance, "_audit_old_values", {})
    old_changed, new_changed = changed_values(old_values, new_values)
    if old_changed or new_changed:
        create_audit_log(instance, AuditLog.UPDATE, old_values=old_changed, new_values=new_changed)


@receiver(pre_delete)
def capture_delete_values(sender, instance, **kwargs):
    if should_audit_model(sender):
        instance._audit_delete_values = serialize_instance(instance)


@receiver(post_delete)
def audit_deleted_model(sender, instance, **kwargs):
    if not should_audit_model(sender):
        return
    create_audit_log(
        instance,
        AuditLog.DELETE,
        old_values=getattr(instance, "_audit_delete_values", serialize_instance(instance)),
    )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_activity(user=user, action="User logged in", module="accounts", description="User logged in.", request=request)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    log_activity(user=user, action="User logged out", module="accounts", description="User logged out.", request=request)


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get("username", "unknown")
    log_activity(
        action="User login failed",
        module="accounts",
        description=f"Failed login attempt for {username}.",
        request=request or get_current_request(),
    )
