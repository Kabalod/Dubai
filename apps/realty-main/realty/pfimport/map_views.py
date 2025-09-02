from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST

from .models import Area as PfArea, Building as PfBuilding
from realty.main.models import Area as MainArea, MasterProject, Building as MainBuilding


def building_map(request):
    pf_areas = PfArea.objects.all()
    main_areas = MainArea.objects.all()
    main_master_projects = MasterProject.objects.order_by("english_name")
    return render(
        request,
        "pfimport/map2.html",
        {
            "pf_areas": pf_areas,
            "main_areas": main_areas,
            "main_master_projects": main_master_projects,
        },
    )


def pf_buildings_json(request):
    area_id = request.GET.get("area_id")
    if not area_id:
        return JsonResponse({"pf": []})
    qs = PfBuilding.objects.filter(area_id=area_id).exclude(
        latitude__isnull=True, longitude__isnull=True
    )
    data = {
        "pf": [
            {"id": b.id, "lat": b.latitude, "lng": b.longitude, "name": str(b)}
            for b in qs
        ]
    }
    return JsonResponse(data)


def main_buildings_json(request):
    area_id = request.GET.get("area_id")
    master_id = request.GET.get("master_project_id")
    qs = MainBuilding.objects.none()
    if master_id:
        qs = MainBuilding.objects.filter(building__project__master_project_id=master_id)
    elif area_id:
        qs = MainBuilding.objects.filter(area_id=area_id)
    qs = qs.exclude(latitude__isnull=True, longitude__isnull=True)
    data = {
        "main": [
            {
                "id": b.id,
                "lat": b.latitude,
                "lng": b.longitude,
                "name": str(b),
                "master_project": b.project.master_project.english_name
                if b.project.master_project
                else "",
            }
            for b in qs
        ]
    }
    return JsonResponse(data)


@require_POST
def link_buildings(request):
    pf_id = request.POST.get("pf_id")
    main_id = request.POST.get("main_id")
    if not pf_id or not main_id:
        return HttpResponseBadRequest("pf_id and main_id required")

    pf = get_object_or_404(PfBuilding, id=pf_id)
    main = get_object_or_404(MainBuilding, id=main_id)

    pf.dld_building = main
    pf.save(update_fields=["dld_building"])

    return JsonResponse({"status": "ok"})


# main/views.py
import json
from django.shortcuts import render
from realty.main.models import Building
from realty.pfimport.models import Area


def buildings_map(request):
    """
    Карта со всеми Building (точки) + полигоны pfimport.Area.
    """
    # --- точки --------------------------------------------------------------
    bqs = Building.objects.select_related("project", "area_by_pf").filter(
        latitude__isnull=False, longitude__isnull=False
    )

    building_features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [b.longitude, b.latitude],
            },
            "properties": {
                "name": b.english_name or b.number or f"Building #{b.pk}",
                "project": b.project.english_name or b.project.project_number,
                "area": b.area_by_pf.name if b.area_by_pf else "—",
            },
        }
        for b in bqs
    ]

    # --- полигоны районов ----------------------------------------------------
    # берём все, у кого сохранена geometry_json
    areas_qs = Area.objects.exclude(geometry_json=None)

    area_features = [
        {
            "type": "Feature",
            "geometry": a.geometry_json,
            "properties": {"name": a.name},
        }
        for a in areas_qs
    ]

    context = {
        "buildings_geojson": json.dumps(
            {"type": "FeatureCollection", "features": building_features}
        ),
        "areas_geojson": json.dumps(
            {"type": "FeatureCollection", "features": area_features}
        ),
    }
    return render(request, "pfimport/map3.html", context)


# ─── ДОБАВЬТЕ в конец файла ──────────────────────────────────────────────────
import json
from django.http import JsonResponse
from django.db.models import Q


def _apply_building_filters(qs, params):
    """
    Принимает QuerySet Building и GET‑параметры;
    возвращает QS, отфильтрованный по ВСЕМ полям модели.
    • text‑поля → icontains
    • exact‑поля / FK id → exact
    • числовые диапазоны: min_/max_<field>
    """
    char_fields = {
        "english_name",
        "arabic_name",
        "number",
        "property_type",
    }
    exact_fields = {
        "project_id",
        "area_id",
        "area_by_pf_id",
        "floor_count",
        "total_units",
        "building_count",
    }

    # --- icontains для текстовых -------------------------------------------
    for f in char_fields:
        v = params.get(f)
        if v:
            qs = qs.filter(**{f"{f}__icontains": v})

    # --- exact для остальных -----------------------------------------------
    for f in exact_fields:
        v = params.get(f)
        if v:
            qs = qs.filter(**{f: v})

    # --- диапазоны (min_/max_) ---------------------------------------------
    range_map = {
        "floor_count": ["min_floor", "max_floor"],
        "total_units": ["min_units", "max_units"],
        "building_count": ["min_buildings", "max_buildings"],
    }
    for field, (min_key, max_key) in range_map.items():
        if min_key in params:
            qs = qs.filter(**{f"{field}__gte": params[min_key]})
        if max_key in params:
            qs = qs.filter(**{f"{field}__lte": params[max_key]})

    return qs


def buildings_geojson(request):
    """
    API‑эндпоинт: GeoJSON всех (или отфильтрованных) Building.
    Пример: /api/buildings.geojson?property_type=Residential&min_floor=10
    """
    qs = Building.objects.filter(latitude__isnull=False, longitude__isnull=False)
    qs = _apply_building_filters(qs, request.GET)

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [b.longitude, b.latitude],
            },
            "properties": {
                "name": b.english_name or b.number or f"B {b.pk}",
                "project": b.project.english_name if b.project else "",
                "area": b.area_by_pf.name if b.area_by_pf else "",
                # — можете добавить больше свойств —
                "property_type": b.property_type,
                "floor_count": b.floor_count,
                "total_units": b.total_units,
            },
        }
        for b in qs
    ]
    return JsonResponse(
        {"type": "FeatureCollection", "features": features},
        json_dumps_params={"ensure_ascii": False},
    )
