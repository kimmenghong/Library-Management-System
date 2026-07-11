from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.accounts.mixins import RolePermissionRequiredMixin

from .forms import FAQForm, FeedbackForm, SupportTicketAdminForm, SupportTicketForm
from .models import FAQ, Feedback, SupportTicket


class HelpCenterView(TemplateView):
    template_name = "support/help_center.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["faqs"] = FAQ.objects.filter(is_active=True)
        return context


class FAQListView(RolePermissionRequiredMixin, ListView):
    model = FAQ
    template_name = "support/faq_list.html"
    context_object_name = "faqs"
    permission_codename = "support.manage_support"


class FAQCreateView(RolePermissionRequiredMixin, CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = "support/faq_form.html"
    success_url = reverse_lazy("support:faq_list")
    permission_codename = "support.manage_support"


class FAQUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = FAQ
    form_class = FAQForm
    template_name = "support/faq_form.html"
    success_url = reverse_lazy("support:faq_list")
    permission_codename = "support.manage_support"


class TicketListView(RolePermissionRequiredMixin, ListView):
    model = SupportTicket
    template_name = "support/ticket_list.html"
    context_object_name = "tickets"
    permission_codename = "support.view_ticket"

    def get_queryset(self):
        queryset = SupportTicket.objects.select_related("user", "assigned_to")
        if not self.request.user.has_role_permission("support.manage_support"):
            queryset = queryset.filter(user=self.request.user)
        return queryset


class TicketCreateView(RolePermissionRequiredMixin, CreateView):
    model = SupportTicket
    form_class = SupportTicketForm
    template_name = "support/ticket_form.html"
    success_url = reverse_lazy("support:ticket_list")
    permission_codename = "support.add_ticket"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Support ticket submitted.")
        return super().form_valid(form)


class TicketUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = SupportTicket
    form_class = SupportTicketAdminForm
    template_name = "support/ticket_admin_form.html"
    success_url = reverse_lazy("support:ticket_list")
    permission_codename = "support.manage_support"


class FeedbackCreateView(CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = "support/feedback_form.html"
    success_url = reverse_lazy("support:help")

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        messages.success(self.request, "Thank you for your feedback.")
        return super().form_valid(form)


class FeedbackListView(RolePermissionRequiredMixin, ListView):
    model = Feedback
    template_name = "support/feedback_list.html"
    context_object_name = "feedback_entries"
    permission_codename = "support.manage_support"
