from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from apps.accounts.mixins import RolePermissionRequiredMixin
from apps.members.models import Member

from .forms import ManualNotificationForm, ReminderRunForm
from .models import EmailReminder, Notification
from .services import (
    create_notification,
    retry_notification_email,
    send_due_date_notifications,
    send_overdue_notifications,
)


def _is_notification_operator(user):
    return user.is_superuser or user.has_role(
        "super_admin", "admin", "librarian", "assistant_librarian"
    )


class NotificationListView(RolePermissionRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20
    permission_codename = "notifications.view_notification"

    def get_queryset(self):
        queryset = Notification.objects.select_related(
            "recipient__user", "related_book_copy__book", "related_borrow_record"
        ).visible_to(self.request.user)
        query = self.request.GET.get("q", "").strip()
        notification_type = self.request.GET.get("type", "").strip()
        status = self.request.GET.get("status", "").strip()
        priority = self.request.GET.get("priority", "").strip()
        for term in query.split():
            queryset = queryset.filter(
                Q(recipient__member_code__icontains=term)
                | Q(recipient__user__username__icontains=term)
                | Q(recipient__user__first_name__icontains=term)
                | Q(recipient__user__last_name__icontains=term)
                | Q(title__icontains=term)
                | Q(message__icontains=term)
            )
        if notification_type in dict(Notification.TYPE_CHOICES):
            queryset = queryset.filter(notification_type=notification_type)
        if status in dict(Notification.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        if priority in dict(Notification.PRIORITY_CHOICES):
            queryset = queryset.filter(priority=priority)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible = Notification.objects.visible_to(self.request.user)
        context.update(
            {
                "types": Notification.TYPE_CHOICES,
                "statuses": Notification.STATUS_CHOICES,
                "priorities": Notification.PRIORITY_CHOICES,
                "summary": visible.aggregate(
                    total=Count("id"),
                    unread=Count("id", filter=Q(status=Notification.UNREAD)),
                    read=Count("id", filter=Q(status=Notification.READ)),
                    archived=Count("id", filter=Q(status=Notification.ARCHIVED)),
                    emailed=Count("id", filter=Q(is_email_sent=True)),
                ),
            }
        )
        return context


class MemberNotificationHistoryView(NotificationListView):
    template_name = "notifications/member_notification_history.html"

    def dispatch(self, request, *args, **kwargs):
        members = Member.objects.select_related("user")
        if not _is_notification_operator(request.user):
            members = members.filter(user=request.user)
        self.member = get_object_or_404(members, pk=kwargs["member_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(recipient=self.member)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member"] = self.member
        return context


class NotificationDetailView(RolePermissionRequiredMixin, DetailView):
    model = Notification
    template_name = "notifications/notification_detail.html"
    context_object_name = "notification"
    permission_codename = "notifications.view_notification"

    def get_queryset(self):
        return (
            Notification.objects.select_related(
                "recipient__user",
                "related_borrow_record__book_copy__book",
                "related_book_copy__book",
                "created_by",
            )
            .prefetch_related("email_logs")
            .visible_to(self.request.user)
        )


class NotificationCreateView(RolePermissionRequiredMixin, FormView):
    template_name = "notifications/notification_form.html"
    form_class = ManualNotificationForm
    permission_codename = "notifications.send_notification"

    def form_valid(self, form):
        try:
            notification = create_notification(
                recipient=form.cleaned_data["recipient"],
                title=form.cleaned_data["title"],
                message=form.cleaned_data["message"],
                notification_type=form.cleaned_data["notification_type"],
                channel=form.cleaned_data["channel"],
                priority=form.cleaned_data["priority"],
                related_borrow_record=form.cleaned_data["related_borrow_record"],
                related_book_copy=form.cleaned_data["related_book_copy"],
                created_by=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Notification created successfully.")
        return redirect("notifications:notification_detail", pk=notification.pk)


class NotificationMarkReadView(RolePermissionRequiredMixin, View):
    permission_codename = "notifications.view_notification"

    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(
            Notification.objects.visible_to(request.user),
            pk=kwargs["pk"],
        )
        notification.mark_read()
        messages.success(request, "Notification marked as read.")
        return redirect("notifications:notification_detail", pk=notification.pk)


class NotificationMarkAllReadView(RolePermissionRequiredMixin, View):
    permission_codename = "notifications.view_notification"

    def post(self, request, *args, **kwargs):
        updated = Notification.objects.visible_to(request.user).unread().update(
            status=Notification.READ,
            read_at=timezone.now(),
            updated_at=timezone.now(),
        )
        messages.success(request, f"Marked {updated} notification(s) as read.")
        return redirect("notifications:notification_list")


class NotificationArchiveView(RolePermissionRequiredMixin, View):
    permission_codename = "notifications.view_notification"

    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(
            Notification.objects.visible_to(request.user),
            pk=kwargs["pk"],
        )
        notification.archive()
        messages.success(request, "Notification archived.")
        return redirect("notifications:notification_list")


class ReminderRunView(RolePermissionRequiredMixin, FormView):
    template_name = "notifications/reminder_run.html"
    form_class = ReminderRunForm
    permission_codename = "notifications.send_notification"

    def form_valid(self, form):
        due_count = overdue_count = 0
        if form.cleaned_data["send_due_date_reminders"]:
            due_count = len(
                send_due_date_notifications(
                    days=form.cleaned_data["due_within_days"],
                    created_by=self.request.user,
                    send_email=form.cleaned_data["send_email"],
                )
            )
        if form.cleaned_data["send_overdue_reminders"]:
            overdue_count = len(
                send_overdue_notifications(
                    created_by=self.request.user,
                    send_email=form.cleaned_data["send_email"],
                )
            )
        messages.success(
            self.request,
            f"Generated {due_count} due-date and {overdue_count} overdue notification(s).",
        )
        return redirect("notifications:notification_list")


class EmailReminderListView(RolePermissionRequiredMixin, ListView):
    model = EmailReminder
    template_name = "notifications/email_reminder_list.html"
    context_object_name = "email_reminders"
    paginate_by = 20
    permission_codename = "notifications.view_notification"

    def get_queryset(self):
        queryset = EmailReminder.objects.select_related(
            "notification", "member__user", "borrow_record__book_copy__book"
        ).visible_to(self.request.user)
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        for term in query.split():
            queryset = queryset.filter(
                Q(email_to__icontains=term)
                | Q(subject__icontains=term)
                | Q(member__member_code__icontains=term)
                | Q(member__user__username__icontains=term)
            )
        if status in dict(EmailReminder.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible = EmailReminder.objects.visible_to(self.request.user)
        context["statuses"] = EmailReminder.STATUS_CHOICES
        context["summary"] = visible.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=EmailReminder.PENDING)),
            sent=Count("id", filter=Q(status=EmailReminder.SENT)),
            failed=Count("id", filter=Q(status=EmailReminder.FAILED)),
        )
        return context


class EmailReminderDetailView(RolePermissionRequiredMixin, DetailView):
    model = EmailReminder
    template_name = "notifications/email_reminder_detail.html"
    context_object_name = "email_reminder"
    permission_codename = "notifications.view_notification"

    def get_queryset(self):
        return EmailReminder.objects.select_related(
            "notification__recipient__user",
            "member__user",
            "borrow_record__book_copy__book",
        ).visible_to(self.request.user)


class EmailReminderRetryView(RolePermissionRequiredMixin, View):
    permission_codename = "notifications.send_notification"

    def post(self, request, *args, **kwargs):
        reminder = get_object_or_404(
            EmailReminder.objects.select_related("notification"),
            pk=kwargs["pk"],
            status=EmailReminder.FAILED,
            notification__isnull=False,
        )
        try:
            attempt = retry_notification_email(reminder.notification)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            if attempt.status == EmailReminder.SENT:
                messages.success(request, "Email delivered successfully.")
            else:
                messages.warning(request, "Email retry failed; the error was recorded.")
        return redirect("notifications:email_reminder_list")
