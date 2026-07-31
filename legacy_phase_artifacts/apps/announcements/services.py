from django.conf import settings
from django.core.mail import send_mail

from apps.accounts.models import User


def send_announcement_email(announcement):
    if not announcement.send_email or announcement.email_sent:
        return 0
    users = User.objects.filter(is_active=True, email__isnull=False).exclude(email="")
    if announcement.target_roles.exists():
        users = users.filter(role__in=announcement.target_roles.all())
    recipients = list(users.values_list("email", flat=True))
    if not recipients:
        return 0
    send_mail(
        announcement.title,
        announcement.content,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=True,
    )
    announcement.email_sent = True
    announcement.save(update_fields=["email_sent", "updated_at"])
    return len(recipients)
