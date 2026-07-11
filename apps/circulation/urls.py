from django.urls import path

from . import views


app_name = "circulation"

urlpatterns = [
    path("", views.BorrowRecordListView.as_view(), name="borrow_list"),
    path("borrow/", views.BorrowBookView.as_view(), name="borrow_create"),
    path("borrows/<int:pk>/", views.BorrowRecordDetailView.as_view(), name="borrow_detail"),
    path("return/", views.ReturnBookView.as_view(), name="return_create"),
    path("borrows/<int:pk>/return/", views.ReturnBookView.as_view(), name="return_borrow"),
    path("borrows/<int:pk>/renew/", views.RenewBorrowView.as_view(), name="renew_borrow"),
    path("renewals/", views.RenewalListView.as_view(), name="renewal_list"),
    path("returns/", views.ReturnRecordListView.as_view(), name="return_list"),
    path("reservations/", views.ReservationListView.as_view(), name="reservation_list"),
    path("reservations/create/", views.ReservationCreateView.as_view(), name="reservation_create"),
    path("reservations/<int:pk>/edit/", views.ReservationUpdateView.as_view(), name="reservation_update"),
    path("policies/", views.BorrowingPolicyListView.as_view(), name="policy_list"),
    path("policies/<int:pk>/edit/", views.BorrowingPolicyUpdateView.as_view(), name="policy_update"),
]
