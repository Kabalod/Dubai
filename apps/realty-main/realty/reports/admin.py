# realty/reports/admin.py

from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages

from .models import BuildingReport, BEDROOM_CHOICES
from realty.pfimport.models import Building
from .utils import get_room_int_and_units

from realty.pfimport.models import Area
from .models import AreaReport, DldBuildingReport

from .models import CityReport, CityReportPF
from realty.main.models import Building as DldBuilding

import logging
import statistics  # нужен для median() в try/except


log = logging.getLogger(__name__)


@admin.register(BuildingReport)
class BuildingReportAdmin(admin.ModelAdmin):
    list_display = (
        "building",
        "bedrooms",
        "calculated_at",
        "avg_sale_price",
        "avg_rent_price",
        "roi",
        "sale_per_unit_ratio",
    )
    list_filter = ("bedrooms",)
    change_list_template = "admin/reports/buildingreport/change_list.html"

    # ───────────────────────────── actions ────────────────────────────
    actions = ["recalculate_selected"]

    @admin.action(description="Пересчитать выбранные отчёты")
    def recalculate_selected(self, request, queryset):
        ok = err = 0
        for rep in queryset:
            try:
                if BuildingReport.calculate(rep.building, rep.bedrooms):
                    ok += 1
            except Exception as exc:  # noqa: BLE001
                err += 1
                log.warning("Skip %s/%s – %s", rep.building, rep.bedrooms, exc)
        self.message_user(
            request,
            f"✅ {ok} пересчитано, ❌ {err} пропущено (см. логи).",
            level=messages.SUCCESS,
        )

    # ───────────────────── кнопка «Пересчитать все» ───────────────────
    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "recalculate-all/",
                self.admin_site.admin_view(self.recalculate_all),
                name="reports_buildingreport_recalculate_all",
            ),
        ]
        return extra + urls

    def recalculate_all(self, request):
        ok = err = 0
        for b in Building.objects.filter(dld_building__isnull=False):
            for key, _ in BEDROOM_CHOICES:
                try:
                    _, units = get_room_int_and_units(b, key)
                    if not units:
                        continue
                    if BuildingReport.calculate(b, key):
                        ok += 1
                except Exception as exc:  # noqa: BLE001
                    err += 1
                    log.warning("Report for %s / %s skipped: %s", b, key, exc)

        self.message_user(
            request,
            f"Готово: {ok} отчётов пересчитано, {err} пропущено (см. логи).",
            level=messages.SUCCESS,
        )
        return redirect("..")


@admin.register(AreaReport)
class AreaReportAdmin(admin.ModelAdmin):
    list_display = (
        "area",
        "bedrooms",
        "calculated_at",
        "avg_sale_price",
        "avg_rent_price",
    )
    list_filter = ("bedrooms",)
    change_list_template = "admin/reports/areareport/change_list.html"
    search_fields = [
        "name",
        "building__area__name",
        "bedrooms",
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "recalculate-all/",
                self.admin_site.admin_view(self.recalculate_all),
                name="areareport_recalculate_all",
            ),
        ]
        return custom + urls

    def recalculate_all(self, request):
        count = 0
        for area in Area.objects.all():
            for key, _ in BEDROOM_CHOICES:
                if AreaReport.calculate(area, key):
                    count += 1
        messages.success(request, f"Пересчитано {count} отчётов для районов.")
        return redirect("..")


# realty/reports/admin.py
# импортируйте messages и BEDROOM_CHOICES у вас уже есть


@admin.register(CityReportPF)
class CityReportPFAdmin(admin.ModelAdmin):
    list_display = (
        "bedrooms",
        "calculated_at",
        "avg_price",
        "median_price",
        "min_price",
        "max_price",
    )
    change_list_template = "admin/reports/cityreport/change_list2.html"  # копия шаблона

    actions = ["recalculate_selected"]

    # ── action для выбранных строк ------------------------------------------------
    @admin.action(description="Пересчитать выбранные отчёты")
    def recalculate_selected(self, request, queryset):
        """Пересчитать только отмеченные отчёты PF."""
        count = 0
        for report in queryset:
            if CityReportPF.calculate(report.bedrooms):
                count += 1
        self.message_user(
            request,
            f"Пересчитано {count} выбранных отчётов PF.",
            level=messages.SUCCESS,
        )

    # ── кнопка «Пересчитать всё» над списком --------------------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "recalculate-all/",
                self.admin_site.admin_view(self.recalculate_all),
                name="cityreportpf_recalculate_all",
            ),
        ]
        return custom + urls

    def recalculate_all(self, request):
        """Полный пересчёт по всем комнатностям."""
        count = 0
        for key, _ in BEDROOM_CHOICES:
            if CityReportPF.calculate(key):
                count += 1
        messages.success(request, f"Пересчитано {count} городских PF-отчётов.")
        return redirect("..")


@admin.register(CityReport)
class CityReportAdmin(admin.ModelAdmin):
    list_display = (
        "bedrooms",
        "calculated_at",
        "avg_price",
        "median_price",
        "min_price",
        "max_price",
    )
    change_list_template = "admin/reports/cityreport/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "recalculate-all/",
                self.admin_site.admin_view(self.recalculate_all),
                name="cityreport_recalculate_all",
            ),
        ]
        return custom + urls

    def recalculate_all(self, request):
        count = 0
        for key, _ in BEDROOM_CHOICES:
            if CityReport.calculate(key):
                count += 1
        messages.success(request, f"Пересчитано {count} городских отчётов.")
        return redirect("..")


import time


from django.http import StreamingHttpResponse


from .models import DldBuildingReport


@admin.register(DldBuildingReport)
class DldBuildingReportAdmin(admin.ModelAdmin):
    change_list_template = "admin/reports/dldbuildingreport/change_list.html"
    list_display = (
        "dld_building",
        "bedrooms",
        "calculated_at",
        "avg_sale_price_ly",
        "avg_rent_price_ly",
        "roi_ly",
        "avg_sale_price_py",
        "avg_rent_price_py",
        "roi_py",
    )
    list_filter = ("bedrooms",)
    search_fields = [
        "dld_building__english_name",
        "bedrooms",
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "recalculate-all/",
                self.admin_site.admin_view(self.recalculate_all),
                name="dldbuildingreport_recalculate_all",
            ),
        ]
        return custom + urls

    def recalculate_all(self, request):
        """
        Показывает «матрицу» + процент выполнения в левом-верхнем углу.
        """

        # === NEW ===  сколько всего шагов (здание × комнатность)
        total_steps = Building.objects.filter(dld_building__isnull=False).count() * len(
            BEDROOM_CHOICES
        )

        def stream():
            yield f"""
              <!DOCTYPE html><html><head>
                <meta charset="utf-8">
                <title>Matrix DLD</title>
                <style>
                  html,body{{margin:0;padding:0;overflow:hidden;background:#000}}
                  canvas{{position:absolute;top:0;left:0}}
                  /* === NEW === фиксированный индикатор в углу */
                  #progress{{
                      position:fixed;top:8px;left:8px;
                      color:#0F0;font:700 16px/1 monospace;z-index:9999;
                  }}
                </style>
              </head><body>
                <div id="progress">0&nbsp;%</div>            <!-- === NEW === -->
                <canvas id="matrix"></canvas>
                <canvas id="custom"></canvas>

                <script>
                  /* --- стандартная матрица, как было --- */
                  const cMat=document.getElementById('matrix'),
                        cCust=document.getElementById('custom'),
                        ctxMat=cMat.getContext('2d'),
                        ctxCust=cCust.getContext('2d');
                  cMat.width=cCust.width=innerWidth;
                  cMat.height=cCust.height=innerHeight;

                  const fontSize=16,
                        columns=Math.floor(cMat.width/fontSize),
                        drops=Array(columns).fill(0),
                        custom=[];
                  function drawMatrix(){{
                    ctxMat.fillStyle='rgba(0,0,0,.05)';
                    ctxMat.fillRect(0,0,cMat.width,cMat.height);
                    ctxMat.fillStyle='#0F0';
                    ctxMat.font=fontSize+'px monospace';
                    for(let i=0;i<columns;i++){{
                      const ch=String.fromCharCode(0x30A0+Math.random()*96);
                      ctxMat.fillText(ch,i*fontSize,drops[i]*fontSize);
                      if(drops[i]*fontSize>cMat.height&&Math.random()>.975)drops[i]=0;
                      drops[i]++;
                    }}
                  }}
                  function drawCustom(){{
                    ctxCust.clearRect(0,0,cCust.width,cCust.height);
                    ctxCust.fillStyle='#F0F';
                    ctxCust.font=fontSize+'px monospace';
                    custom.forEach((d,idx)=>{{
                      ctxCust.fillText(d.text,d.x*fontSize,d.y*fontSize);
                      d.y+=d.speed;
                      if(d.y*fontSize>cCust.height)custom.splice(idx,1);
                    }});
                  }}
                  setInterval(()=>{{drawMatrix();drawCustom();}},18);

                  function pushText(txt,speed=.5){{
                    const used=custom.map(d=>d.x),
                          free=[...Array(columns).keys()].filter(i=>!used.includes(i)),
                          x=free.length?free[Math.random()*free.length|0]:Math.random()*columns|0;
                    custom.push({{text:txt,x,y:0,speed}});
                  }}

                  /* === NEW === прогресс */
                  const TOTAL_STEPS = {total_steps};
                  let doneSteps = 0;
                  function incProgress(){{
                    doneSteps++;
                    const pct = Math.round(doneSteps / TOTAL_STEPS * 100);
                    document.getElementById('progress').innerHTML = pct + '&nbsp;%';
                  }}
                </script>
            """

            # --- сам пересчёт с инкрементом процента -------------------
            for b in Building.objects.filter(dld_building__isnull=False):
                for key, label in BEDROOM_CHOICES:
                    status = f"{b.name} – {label}"
                    yield f"<script>pushText({status!r},0.5);incProgress();</script>"
                    DldBuildingReport.calculate(b.dld_building, key)
                    # time.sleep(1)        # при желании оставьте / уберите

            yield """
                <script>
                  pushText('✅ Готово!',0.5);
                  incProgress();          /* гарантируем 100 % */
                </script></body></html>
            """

        # === CHANGED === тип остался Streaming, но теперь с %.
        return StreamingHttpResponse(stream(), content_type="text/html")


from realty.main.models import Area as DldArea
from .models import AreaReportDLD


@admin.register(AreaReportDLD)
class AreaReportAdminDLD(admin.ModelAdmin):
    list_display = (
        "area",
        "bedrooms",
        "calculated_at",
        "avg_sale_price_ly",
        "avg_rent_price_ly",
    )
    list_filter = ("bedrooms",)
    change_list_template = "admin/reports/areareportdld/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "recalculate-all/",
                self.admin_site.admin_view(self.recalculate_all),
                name="areareport_recalculate_all_dld",
            ),
        ]
        return custom + urls

    def recalculate_all(self, request):
        AreaReportDLD.fill_all()
        messages.success(
            request, "Пересчитаны все отчёты по районам по всем комнатностям."
        )
        return redirect("..")
