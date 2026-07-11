from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .forms import BookReviewForm, ReviewModerationForm
from .models import BookReview


class ReviewListView(RolePermissionRequiredMixin, ListView):
    model = BookReview
    template_name = "reviews/review_list.html"
    context_object_name = "reviews"
    permission_codename = "reviews.view_review"

    def get_queryset(self):
        queryset = BookReview.objects.select_related("book", "member__user", "moderated_by")
        status = self.request.GET.get("status")
        if not self.request.user.has_role_permission("reviews.moderate_review"):
            queryset = queryset.filter(status=BookReview.APPROVED) | queryset.filter(member__user=self.request.user)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = BookReview.STATUS_CHOICES
        return context


class ReviewCreateView(RolePermissionRequiredMixin, CreateView):
    model = BookReview
    form_class = BookReviewForm
    template_name = "reviews/review_form.html"
    success_url = reverse_lazy("reviews:list")
    permission_codename = "reviews.add_review"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.has_role_permission("reviews.moderate_review"):
            member = getattr(self.request.user, "member_profile", None)
            form.fields["member"].queryset = form.fields["member"].queryset.filter(user=self.request.user)
            form.fields["member"].initial = member
        return form

    def form_valid(self, form):
        if not self.request.user.has_role_permission("reviews.moderate_review"):
            member = getattr(self.request.user, "member_profile", None)
            if not member:
                form.add_error("member", "Your account is not linked to a library member profile.")
                return self.form_invalid(form)
            form.instance.member = member
        messages.success(self.request, "Review submitted for moderation.")
        return super().form_valid(form)


class ReviewModerateView(RolePermissionRequiredMixin, UpdateView):
    model = BookReview
    form_class = ReviewModerationForm
    template_name = "reviews/review_moderate.html"
    success_url = reverse_lazy("reviews:list")
    permission_codename = "reviews.moderate_review"

    def form_valid(self, form):
        form.instance.moderated_by = self.request.user
        messages.success(self.request, "Review moderation updated.")
        return super().form_valid(form)
