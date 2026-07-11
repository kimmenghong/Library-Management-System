from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("manage/<str:entity>/", views.entity_list, name="entity_list"),
    path("manage/<str:entity>/add/", views.entity_create, name="entity_create"),
    path(
        "manage/<str:entity>/<int:pk>/edit/",
        views.entity_update,
        name="entity_update",
    ),
    path(
        "manage/<str:entity>/<int:pk>/delete/",
        views.entity_delete,
        name="entity_delete",
    ),
    path("books/", views.book_list, name="book_list"),
    path("books/add/", views.book_create, name="book_create"),
    path("books/<int:pk>/edit/", views.book_update, name="book_update"),
    path("books/<int:pk>/delete/", views.book_delete, name="book_delete"),
    path("borrowing/", views.borrow_list, name="borrow_list"),
    path("borrowing/issue/", views.borrow_create, name="borrow_create"),
    path(
        "borrowing/<int:pk>/return/",
        views.borrow_return,
        name="borrow_return",
    ),
    path("fines/", views.fine_list, name="fine_list"),
    path("fines/add/", views.fine_create, name="fine_create"),
    path("fines/<int:pk>/pay/", views.fine_pay, name="fine_pay"),
    path("notifications/", views.notification_list, name="notification_list"),
    path(
        "notifications/add/",
        views.notification_create,
        name="notification_create",
    ),
    path(
        "notifications/<int:pk>/read/",
        views.notification_read,
        name="notification_read",
    ),
    path("reports/", views.report_list, name="report_list"),
    path("reports/generate/", views.report_create, name="report_create"),
]
