from django.urls import path
from . import views

app_name = "merger"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("merge/", views.merge_view, name="merge"),
    path("history/", views.history, name="history"),
]
