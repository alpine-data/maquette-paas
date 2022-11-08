from django.urls import path

from . import views

urlpatterns = [
    # ex: /api/
    path("<str:space_name>/push", views.push, name="push"),
    path(
        "<str:space_name>/push/<str:deployment_id>", views.push_logs, name="push_logs"
    ),
]
