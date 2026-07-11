from django.urls import path

from . import views


app_name = "status_tracking"

urlpatterns = [
    path("", views.BookStatusLogListView.as_view(), name="status_log_list"),
    path("lost/", views.LostBookListView.as_view(), name="lost_list"),
    path("lost/create/", views.LostBookCreateView.as_view(), name="lost_create"),
    path("lost/<int:pk>/", views.LostBookDetailView.as_view(), name="lost_detail"),
    path("lost/<int:pk>/edit/", views.LostBookUpdateView.as_view(), name="lost_update"),
    path("damaged/", views.DamagedBookListView.as_view(), name="damaged_list"),
    path("damaged/create/", views.DamagedBookCreateView.as_view(), name="damaged_create"),
    path("damaged/<int:pk>/", views.DamagedBookDetailView.as_view(), name="damaged_detail"),
    path("damaged/<int:pk>/edit/", views.DamagedBookUpdateView.as_view(), name="damaged_update"),
    path("repairs/", views.RepairRecordListView.as_view(), name="repair_list"),
    path("repairs/create/", views.RepairRecordCreateView.as_view(), name="repair_create"),
    path("repairs/<int:pk>/", views.RepairRecordDetailView.as_view(), name="repair_detail"),
    path("repairs/<int:pk>/edit/", views.RepairRecordUpdateView.as_view(), name="repair_update"),
]
