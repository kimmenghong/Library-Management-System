from django.urls import path

from . import views


app_name = "settings_app"

urlpatterns = [
    path("", views.SettingsHomeView.as_view(), name="home"),
    path("library/", views.LibraryProfileUpdateView.as_view(), name="library_profile"),
    path("system/", views.SystemSettingListView.as_view(), name="system_settings"),
    path("system/create/", views.SystemSettingCreateView.as_view(), name="system_setting_create"),
    path("system/<int:pk>/edit/", views.SystemSettingUpdateView.as_view(), name="system_setting_update"),
    path("borrowing-policies/", views.BorrowingPolicySettingsView.as_view(), name="borrowing_policies"),
    path("borrowing-policies/<int:pk>/edit/", views.BorrowingPolicySettingsUpdateView.as_view(), name="borrowing_policy_update"),
    path("backups/", views.BackupHistoryView.as_view(), name="backup_history"),
    path("backups/create/", views.CreateBackupView.as_view(), name="backup_create"),
    path("backups/restore/", views.RestoreBackupView.as_view(), name="backup_restore"),
    path("backups/schedule/", views.BackupScheduleUpdateView.as_view(), name="backup_schedule"),
]
