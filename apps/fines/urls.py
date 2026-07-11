from django.urls import path

from . import views


app_name = "fines"

urlpatterns = [
    path("", views.FineListView.as_view(), name="fine_list"),
    path("create/", views.FineCreateView.as_view(), name="fine_create"),
    path("<int:pk>/", views.FineDetailView.as_view(), name="fine_detail"),
    path("<int:pk>/edit/", views.FineUpdateView.as_view(), name="fine_update"),
    path("<int:pk>/waive/", views.FineWaiveView.as_view(), name="fine_waive"),
    path("<int:fine_pk>/payments/create/", views.PaymentCreateView.as_view(), name="payment_create_for_fine"),
    path("payments/", views.PaymentListView.as_view(), name="payment_list"),
    path("payments/create/", views.PaymentCreateView.as_view(), name="payment_create"),
    path("payments/<int:pk>/", views.PaymentDetailView.as_view(), name="payment_detail"),
    path("payments/<int:pk>/void/", views.PaymentVoidView.as_view(), name="payment_void"),
]
