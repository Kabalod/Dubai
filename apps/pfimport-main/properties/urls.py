from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('health/', views.health_check, name='health_check'),
    path('properties/', views.properties_list, name='properties_list'),
    path('export/', views.export_view, name='export'),
    path('stats/', views.stats_view, name='stats'),
]