from django.urls import path
from django.views.decorators.cache import cache_page

from .reports_views import building_full_metrics_view
from .reports_views import building_report_view as new_building_report_view
from .views import pf_listings_rent_view
from .views import pf_listings_sale_view
from .map_views import (
    building_map,
    main_buildings_json,
    link_buildings,
    pf_buildings_json,
    buildings_map,
    buildings_geojson,
)

app_name = "pfimport"

urlpatterns = [
    path(
        "sale/", cache_page(3600)(pf_listings_sale_view), name="pf_listings_sale_view"
    ),
    path(
        "rent/", cache_page(3600)(pf_listings_rent_view), name="pf_listings_rent_view"
    ),
    # path(
    #     'building/<int:building_id>/report/',
    #     building_report_view,
    #     name='building_report_view'
    # ),
    # path("", building_full_metrics_view, name="building_full_metrics_view"),
    path("building-report/", new_building_report_view, name="building_report"),
    path("map2/", building_map, name="building_map"),
    path("map3/", buildings_map, name="buildings_map"),
    path("map/", building_map, name="building_map"),
    path("api/pf_buildings/", pf_buildings_json, name="pf_buildings_json"),  # НОВОЕ
    path("api/buildings/", main_buildings_json, name="main_buildings_json"),
    path("api/link/", link_buildings, name="link_buildings"),  # НОВОЕ
    path("api/buildings.geojson", buildings_geojson, name="buildings_geojson"),
]
