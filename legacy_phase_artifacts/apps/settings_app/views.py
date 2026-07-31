from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin
from apps.circulation.models import BorrowingPolicy
from apps.circulation.forms import BorrowingPolicyForm

from .forms import BackupScheduleForm, LibraryProfileForm, RestoreBackupForm, SystemSettingForm
from .models import BackupRecord, BackupSchedule, LibraryProfile, SystemSetting
from .services import create_database_backup, restore_database_backup


class SettingsHomeView(RolePermissionRequiredMixin, TemplateView):
    template_name = "settings_app/settings_home.html"
    permission_codename = "settings.manage_settings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = LibraryProfile.objects.first()
        context["settings_count"] = SystemSetting.objects.count()
        context["backup_count"] = BackupRecord.objects.count()
        return context


class LibraryProfileUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = LibraryProfile
    form_class = LibraryProfileForm
    template_name = "settings_app/library_profile_form.html"
    success_url = reverse_lazy("settings_app:home")
    permission_codename = "settings.manage_settings"

    def get_object(self, queryset=None):
        obj, _ = LibraryProfile.objects.get_or_create(pk=1)
        return obj


class SystemSettingListView(RolePermissionRequiredMixin, ListView):
    model = SystemSetting
    template_name = "settings_app/systemsetting_list.html"
    context_object_name = "settings"
    permission_codename = "settings.manage_settings"


class SystemSettingCreateView(RolePermissionRequiredMixin, CreateView):
    model = SystemSetting
    form_class = SystemSettingForm
    template_name = "settings_app/systemsetting_form.html"
    success_url = reverse_lazy("settings_app:system_settings")
    permission_codename = "settings.manage_settings"


class SystemSettingUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = SystemSetting
    form_class = SystemSettingForm
    template_name = "settings_app/systemsetting_form.html"
    success_url = reverse_lazy("settings_app:system_settings")
    permission_codename = "settings.manage_settings"


class BorrowingPolicySettingsView(RolePermissionRequiredMixin, ListView):
    model = BorrowingPolicy
    template_name = "settings_app/borrowing_policy_settings.html"
    context_object_name = "policies"
    permission_codename = "settings.manage_settings"


class BorrowingPolicySettingsUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = BorrowingPolicy
    form_class = BorrowingPolicyForm
    template_name = "settings_app/borrowing_policy_form.html"
    success_url = reverse_lazy("settings_app:borrowing_policies")
    permission_codename = "settings.manage_settings"


class BackupScheduleUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = BackupSchedule
    form_class = BackupScheduleForm
    template_name = "settings_app/backup_schedule_form.html"
    success_url = reverse_lazy("settings_app:backup_history")
    permission_codename = "settings.manage_backup"

    def get_object(self, queryset=None):
        obj, _ = BackupSchedule.objects.get_or_create(pk=1)
        return obj


class BackupHistoryView(RolePermissionRequiredMixin, ListView):
    model = BackupRecord
    template_name = "settings_app/backup_history.html"
    context_object_name = "backups"
    permission_codename = "settings.manage_backup"


class CreateBackupView(RolePermissionRequiredMixin, View):
    permission_codename = "settings.manage_backup"

    def post(self, request, *args, **kwargs):
        backup = create_database_backup(user=request.user)
        messages.success(request, backup.message)
        return redirect("settings_app:backup_history")


class RestoreBackupView(RolePermissionRequiredMixin, TemplateView):
    template_name = "settings_app/restore_backup.html"
    permission_codename = "settings.manage_backup"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = RestoreBackupForm()
        return context

    def post(self, request, *args, **kwargs):
        form = RestoreBackupForm(request.POST)
        if form.is_valid():
            backup = restore_database_backup(form.cleaned_data["backup"], user=request.user)
            messages.success(request, backup.message)
            return redirect("settings_app:backup_history")
        return self.render_to_response({"form": form})
