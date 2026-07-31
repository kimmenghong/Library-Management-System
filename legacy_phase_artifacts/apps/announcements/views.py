from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .forms import AnnouncementForm
from .models import Announcement
from .services import send_announcement_email


class AnnouncementListView(RolePermissionRequiredMixin, ListView):
    model = Announcement
    template_name = "announcements/announcement_list.html"
    context_object_name = "announcements"
    permission_codename = "announcements.view_announcement"

    def get_queryset(self):
        queryset = Announcement.objects.prefetch_related("target_roles")
        if not self.request.user.has_role_permission("announcements.manage_announcement"):
            now = timezone.now()
            queryset = queryset.filter(status=Announcement.PUBLISHED, publish_date__lte=now).filter(
                Q(expire_date__isnull=True) | Q(expire_date__gte=now)
            )
            if self.request.user.role:
                queryset = queryset.filter(target_roles=self.request.user.role) | queryset.filter(target_roles__isnull=True)
        return queryset.distinct()


class AnnouncementDetailView(RolePermissionRequiredMixin, DetailView):
    model = Announcement
    template_name = "announcements/announcement_detail.html"
    context_object_name = "announcement"
    permission_codename = "announcements.view_announcement"

    def get_queryset(self):
        queryset = Announcement.objects.prefetch_related("target_roles")
        if not self.request.user.has_role_permission("announcements.manage_announcement"):
            now = timezone.now()
            queryset = queryset.filter(status=Announcement.PUBLISHED, publish_date__lte=now).filter(
                Q(expire_date__isnull=True) | Q(expire_date__gte=now)
            )
            if self.request.user.role:
                queryset = queryset.filter(target_roles=self.request.user.role) | queryset.filter(target_roles__isnull=True)
        return queryset.distinct()


class AnnouncementCreateView(RolePermissionRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "announcements/announcement_form.html"
    success_url = reverse_lazy("announcements:list")
    permission_codename = "announcements.manage_announcement"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        if self.object.status == Announcement.PUBLISHED and self.object.send_email:
            count = send_announcement_email(self.object)
            messages.success(self.request, f"Announcement saved and emailed to {count} user(s).")
        else:
            messages.success(self.request, "Announcement saved.")
        return response


class AnnouncementUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "announcements/announcement_form.html"
    success_url = reverse_lazy("announcements:list")
    permission_codename = "announcements.manage_announcement"

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.status == Announcement.PUBLISHED and self.object.send_email and not self.object.email_sent:
            count = send_announcement_email(self.object)
            messages.success(self.request, f"Announcement updated and emailed to {count} user(s).")
        else:
            messages.success(self.request, "Announcement updated.")
        return response


class AnnouncementPublishView(RolePermissionRequiredMixin, View):
    permission_codename = "announcements.manage_announcement"

    def post(self, request, *args, **kwargs):
        announcement = Announcement.objects.get(pk=kwargs["pk"])
        announcement.status = Announcement.PUBLISHED
        announcement.save(update_fields=["status", "updated_at"])
        count = send_announcement_email(announcement)
        messages.success(request, f"Announcement published. Email sent to {count} user(s).")
        return redirect("announcements:list")
