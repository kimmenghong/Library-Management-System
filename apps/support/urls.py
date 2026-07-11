from django.urls import path

from . import views


app_name = "support"

urlpatterns = [
    path("", views.HelpCenterView.as_view(), name="help"),
    path("faqs/", views.FAQListView.as_view(), name="faq_list"),
    path("faqs/create/", views.FAQCreateView.as_view(), name="faq_create"),
    path("faqs/<int:pk>/edit/", views.FAQUpdateView.as_view(), name="faq_update"),
    path("tickets/", views.TicketListView.as_view(), name="ticket_list"),
    path("tickets/create/", views.TicketCreateView.as_view(), name="ticket_create"),
    path("tickets/<int:pk>/edit/", views.TicketUpdateView.as_view(), name="ticket_update"),
    path("feedback/", views.FeedbackCreateView.as_view(), name="feedback"),
    path("feedback/list/", views.FeedbackListView.as_view(), name="feedback_list"),
]
