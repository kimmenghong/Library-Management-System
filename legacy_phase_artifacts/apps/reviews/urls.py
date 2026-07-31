from django.urls import path

from . import views


app_name = "reviews"

urlpatterns = [
    path("", views.ReviewListView.as_view(), name="list"),
    path("create/", views.ReviewCreateView.as_view(), name="create"),
    path("<int:pk>/moderate/", views.ReviewModerateView.as_view(), name="moderate"),
]
