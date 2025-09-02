# pfimport/apps.py
from django.apps import AppConfig


class PfimportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "realty.pfimport"
    verbose_name = "PropertyFinder JSON Import"
