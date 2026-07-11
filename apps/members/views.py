from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .forms import (
    LibrarianProfileForm,
    MemberForm,
    MemberStatusForm,
    StaffProfileForm,
    StudentProfileForm,
    TeacherProfileForm,
)
from .models import LibrarianProfile, Member, StaffProfile, StudentProfile, TeacherProfile


class MemberListView(RolePermissionRequiredMixin, ListView):
    model = Member
    template_name = "members/member_list.html"
    context_object_name = "members"
    paginate_by = 20
    permission_codename = "members.view_member"

    def get_queryset(self):
        queryset = Member.objects.select_related("user", "user__role").order_by(
            "member_code"
        )
        query = self.request.GET.get("q", "").strip()
        member_type = self.request.GET.get("member_type", "").strip()
        status = self.request.GET.get("status", "").strip()
        if query:
            for term in query.split():
                queryset = queryset.filter(
                    Q(member_code__icontains=term)
                    | Q(user__username__icontains=term)
                    | Q(user__email__icontains=term)
                    | Q(user__first_name__icontains=term)
                    | Q(user__last_name__icontains=term)
                    | Q(phone__icontains=term)
                )
        if member_type in Member.MEMBER_TYPE_VALUES:
            queryset = queryset.filter(member_type=member_type)
        if status in dict(Member.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_types"] = Member.MEMBER_TYPE_CHOICES
        context["statuses"] = Member.STATUS_CHOICES
        context["summary"] = {
            "total": Member.objects.count(),
            "active": Member.objects.active().count(),
            "pending": Member.objects.filter(status=Member.PENDING).count(),
            "suspended": Member.objects.filter(status=Member.SUSPENDED).count(),
            "expired": Member.objects.filter(status=Member.EXPIRED).count(),
        }
        return context


class MemberDetailView(RolePermissionRequiredMixin, DetailView):
    model = Member
    template_name = "members/member_detail.html"
    context_object_name = "member"
    permission_codename = "members.view_member"

    def get_queryset(self):
        return Member.objects.select_related(
            "user",
            "user__role",
            "student_profile",
            "teacher_profile",
            "staff_profile",
            "librarian_profile",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.object.specialized_profile
        context["total_borrows"] = self.object.borrow_records.count()
        context["active_borrows"] = self.object.borrow_records.filter(
            status__in=["borrowed", "overdue"]
        ).count()
        context["reservation_count"] = self.object.reservations.count()
        context["fine_count"] = self.object.fines.exclude(
            status__in=["paid", "waived"]
        ).count()
        return context


class MemberCreateView(RolePermissionRequiredMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = "members/member_form.html"
    permission_codename = "members.add_member"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Member record created successfully.")
        return response

    def get_success_url(self):
        return reverse("members:member_detail", kwargs={"pk": self.object.pk})


class MemberUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = "members/member_form.html"
    permission_codename = "members.edit_member"

    def get_queryset(self):
        return Member.objects.select_related("user", "user__role")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Member record updated successfully.")
        return response

    def get_success_url(self):
        return reverse("members:member_detail", kwargs={"pk": self.object.pk})


class MemberStatusUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Member
    form_class = MemberStatusForm
    template_name = "members/member_status_form.html"
    permission_codename = "members.suspend_member"

    def get_queryset(self):
        return Member.objects.select_related("user")

    def form_valid(self, form):
        previous_status = self.get_object().status
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Membership status changed from {dict(Member.STATUS_CHOICES)[previous_status]} "
            f"to {self.object.get_status_display()}.",
        )
        return response

    def get_success_url(self):
        return reverse("members:member_detail", kwargs={"pk": self.object.pk})


class SpecializedProfileCreateView(RolePermissionRequiredMixin, CreateView):
    template_name = "members/profile_form.html"
    permission_codename = "members.add_member"
    page_title = "Create Profile"
    allowed_member_types = ()

    def dispatch(self, request, *args, **kwargs):
        self.member = None
        member_pk = kwargs.get("member_pk")
        if member_pk:
            self.member = get_object_or_404(
                Member.objects.select_related("user"),
                pk=member_pk,
                member_type__in=self.allowed_member_types,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["member"] = self.member
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if self.member and self.model is LibrarianProfile:
            initial["employee_type"] = self.member.member_type
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["member"] = self.member
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"{self.page_title} completed successfully.")
        return response

    def get_success_url(self):
        return reverse("members:member_detail", kwargs={"pk": self.object.member_id})


class SpecializedProfileUpdateView(RolePermissionRequiredMixin, UpdateView):
    template_name = "members/profile_form.html"
    permission_codename = "members.edit_member"
    page_title = "Edit Profile"

    def get_queryset(self):
        return self.model.objects.select_related("member", "member__user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["member"] = self.object.member
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"{self.page_title} completed successfully.")
        return response

    def get_success_url(self):
        return reverse("members:member_detail", kwargs={"pk": self.object.member_id})


class StudentProfileCreateView(SpecializedProfileCreateView):
    model = StudentProfile
    form_class = StudentProfileForm
    page_title = "Create Student Profile"
    allowed_member_types = (Member.STUDENT,)


class StudentProfileUpdateView(SpecializedProfileUpdateView):
    model = StudentProfile
    form_class = StudentProfileForm
    page_title = "Edit Student Profile"


class TeacherProfileCreateView(SpecializedProfileCreateView):
    model = TeacherProfile
    form_class = TeacherProfileForm
    page_title = "Create Teacher Profile"
    allowed_member_types = (Member.TEACHER,)


class TeacherProfileUpdateView(SpecializedProfileUpdateView):
    model = TeacherProfile
    form_class = TeacherProfileForm
    page_title = "Edit Teacher Profile"


class StaffProfileCreateView(SpecializedProfileCreateView):
    model = StaffProfile
    form_class = StaffProfileForm
    page_title = "Create Staff Profile"
    allowed_member_types = (Member.STAFF,)


class StaffProfileUpdateView(SpecializedProfileUpdateView):
    model = StaffProfile
    form_class = StaffProfileForm
    page_title = "Edit Staff Profile"


class LibrarianProfileCreateView(SpecializedProfileCreateView):
    model = LibrarianProfile
    form_class = LibrarianProfileForm
    page_title = "Create Librarian Profile"
    allowed_member_types = (Member.LIBRARIAN, Member.ASSISTANT_LIBRARIAN)


class LibrarianProfileUpdateView(SpecializedProfileUpdateView):
    model = LibrarianProfile
    form_class = LibrarianProfileForm
    page_title = "Edit Librarian Profile"
