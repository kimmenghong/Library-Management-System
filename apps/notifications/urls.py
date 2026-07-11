from django.urls import path

from . import views


app_name = "notifications"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification_list"),
    path("create/", views.NotificationCreateView.as_view(), name="notification_create"),
    path("run-reminders/", views.ReminderRunView.as_view(), name="run_reminders"),
    path("email-reminders/", views.EmailReminderListView.as_view(), name="email_reminder_list"),
    path("email-reminders/<int:pk>/", views.EmailReminderDetailView.as_view(), name="email_reminder_detail"),
    path("email-reminders/<int:pk>/retry/", views.EmailReminderRetryView.as_view(), name="email_reminder_retry"),
    path("members/<int:member_pk>/", views.MemberNotificationHistoryView.as_view(), name="member_history"),
    path("mark-all-read/", views.NotificationMarkAllReadView.as_view(), name="notification_mark_all_read"),
    path("<int:pk>/", views.NotificationDetailView.as_view(), name="notification_detail"),
    path("<int:pk>/read/", views.NotificationMarkReadView.as_view(), name="notification_mark_read"),
    path("<int:pk>/archive/", views.NotificationArchiveView.as_view(), name="notification_archive"),
]
