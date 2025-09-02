from django.urls import path
from .views import report_view

app_name = "building_reports"

urlpatterns = [
    path("report/", report_view, name="report"),
]
