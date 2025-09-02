# building_reports/views.py

from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from realty.pfimport.models import Building as PFBuilding
from .models import (
    PFSnapshotBuilding,
    BuildingReportSnapshot,
    AreaReportSnapshot,
)

# маппинг normalized → raw number_of_rooms
ROOM_MAPPING = {
    "studio": ["Studio"],
    "1br": ["1 B/R"],
    "2br": ["2 B/R"],
    "3br": ["3 B/R"],
    "4br": ["4 B/R"],
}


def report_view(request):
    # только PF-дома, у которых есть оба отчёта
    pf_buildings = (
        PFBuilding.objects.filter(
            dld_building__isnull=False,
        )
        .distinct()
        .order_by("name")
    )

    pf_id = request.GET.get("pf_building")
    bedrooms = request.GET.get("bedrooms")

    ctx = {
        "pf_buildings": pf_buildings,
        "selected_pf": None,
        "bedroom_choices": None,
        "selected_bedrooms": None,
        "pf_snapshot": None,
        "building_snapshot": None,
        "area_snapshot": None,
        "total_units": None,
        "rooms_structure": None,
    }

    if pf_id:
        pf = get_object_or_404(pf_buildings, pk=pf_id)
        ctx["selected_pf"] = pf

        # варианты bedrooms из PFSnapshotBuilding
        rooms = (
            PFSnapshotBuilding.objects.filter(building=pf)
            .values_list("bedrooms", flat=True)
            .distinct()
        )
        ctx["bedroom_choices"] = rooms

        if bedrooms:
            ctx["selected_bedrooms"] = bedrooms

            # 1) PF-снэпшот
            ctx["pf_snapshot"] = PFSnapshotBuilding.objects.filter(
                building=pf, bedrooms=bedrooms
            ).first()

            # строим Q-фильтр для BuildingReportSnapshot и AreaReportSnapshot
            raw_names = ROOM_MAPPING.get(bedrooms.lower(), [bedrooms])
            q_rooms = Q()
            for nm in raw_names:
                q_rooms |= Q(number_of_rooms__iexact=nm)

            # 2) BuildingReportSnapshot по main.Building
            main_b = pf.dld_building
            if main_b:
                ctx["building_snapshot"] = (
                    BuildingReportSnapshot.objects.filter(building=main_b)
                    .filter(q_rooms)
                    .order_by("-period_start")
                    .first()
                )
                ctx["total_units"] = pf.dld_building.total_units
                ctx["rooms_structure"] = pf.dld_building.arabic_name

            # 3) AreaReportSnapshot по зоне
            if main_b and main_b.area:
                ctx["area_snapshot"] = (
                    AreaReportSnapshot.objects.filter(area=main_b.area)
                    .filter(q_rooms)
                    .order_by("-period_start")
                    .first()
                )

    return render(request, "building_reports/report.html", ctx)
