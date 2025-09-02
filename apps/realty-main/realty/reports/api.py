# realty/reports/api.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import BuildingReport, BEDROOM_CHOICES


@require_GET
def building_bedrooms(request, building_id: int):
    keys = (
        BuildingReport.objects.filter(building_id=building_id)
        .values_list("bedrooms", flat=True)
        .distinct()
    )
    label_map = dict(BEDROOM_CHOICES)
    return JsonResponse(
        {"choices": [{"value": k, "label": label_map.get(k, k)} for k in keys]}
    )
