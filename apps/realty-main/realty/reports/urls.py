from django.urls import path

from .views import (
    ReportView,
    # dldbuilding_report_list,
    # dldbuilding_report_detail,
    # area_report_detail,
    # CombinedReportView,
    # area_report_detail_api,
    # dldbuilding_report_detail_api,
    # dldbuilding_report_list_api,
    # aggregated_report_api,
)
# from .views_3d import CombinedReportView2

from realty.reports.api import building_bedrooms


app_name = "reports"

urlpatterns = [
    path("", ReportView.as_view(), name="report"),
    # path(
    #     "dld-building-reports/", dldbuilding_report_list, name="dldbuilding_report_list"
    # ),
    # path(
    #     "dld-building-reports/<int:pk>/",
    #     dldbuilding_report_detail,
    #     name="dldbuilding_report_detail",
    # ),
    # path(
    #     "dld-building-area/",
    #     dldbuilding_report_detail,
    #     name="dldbuilding_report_detail",
    # ),
    # path("api/aggregated/", aggregated_report_api),
    # path("api/dldbuilding/", dldbuilding_report_list_api),
    # path("api/dldbuilding/<int:pk>/", dldbuilding_report_detail_api),
    # path("api/area/", area_report_detail_api),
    # path("combined/", CombinedReportView.as_view(), name="combined_report"),
    # path("combined3d/", CombinedReportView2.as_view(), name="combined_report2"),
]

urlpatterns += [
    path(
        "reports/api/building/<int:building_id>/bedrooms/",
        building_bedrooms,
        name="building-bedrooms-api",
    ),
]
