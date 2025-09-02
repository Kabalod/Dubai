from django.urls import path
from django.views.decorators.cache import cache_page
from realty.pfimport.views import pf_listings_rent_view
from realty.pfimport.views import pf_listings_sale_view

from realty.pfimport.views_creative import (
    pf_listings_rent_view as creative_pf_listings_rent_view,
)
from realty.pfimport.views_creative import (
    pf_listings_sale_view as creative_pf_listings_sale_view,
)
from realty.pfimport.creative_views import (
    pf_listings_sale_view as creative_pf_listings_sale_view_2,
)
from . import views

urlpatterns = [
    path("", views.rental_transactions_list, name="rental_transactions_list"),
    path(
        "autocomplete/", views.autocomplete_suggestions, name="autocomplete_suggestions"
    ),
    #   path('stats/', views.rental_transactions_stats, name='rental_transactions_stats'),#rental_transactions_stats_another
    # path('transactions/<int:pk>/', views.rental_transaction_detail, name='rental_transaction_detail'),
    # path('details/<str:metric>/', views.rental_transaction_metric_detail, name='rental_transaction_metric_detail'),
    path(
        "pf-listings/sale/",
        cache_page(3600)(pf_listings_sale_view),
        name="pf_listings_sale_view",
    ),
    path(
        "pf-listings/rent/",
        cache_page(3600)(pf_listings_rent_view),
        name="pf_listings_rent_view",
    ),
    path(
        "pf-listings/creative_sale/",
        cache_page(360)(creative_pf_listings_sale_view),
        name="creative_pf_listings_sale_view",
    ),
    path(
        "pf-listings/creative_rent/",
        cache_page(360)(creative_pf_listings_rent_view),
        name="creative_pf_listings_rent_view",
    ),
    path(
        "pf-listings/creative_sale_2/",
        cache_page(3600)(creative_pf_listings_sale_view_2),
        name="creative_pf_listings_sale_view_2",
    ),
]
# path("sale/", cache_page(3600)(pf_listings_sale_view), name="pf_listings_sale_view"),
