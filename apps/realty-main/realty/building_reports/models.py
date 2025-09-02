from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models import Avg, Min, Max, Count

from realty.main.models import (
    Building,
    Area,
    MergedTransaction,
    MergedRentalTransaction,
)

# pfimport/models.py
from decimal import Decimal
from realty.main.models import Building as DldBuilding
from realty.pfimport.models import PFBase, PFListSale, PFListRent, PFJsonUpload


class PFSnapshotBuilding(models.Model):
    """
    Снимок метрик по объявлениям PF (sale/rent) для каждого pfimport.Building
    и каждой нормализованной 'комнатности'.
    """

    building = models.ForeignKey(
        "pfimport.Building", on_delete=models.CASCADE, related_name="pf_snapshots"
    )
    bedrooms = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Нормализованная комнатность: studio, 1br, 2br, 3br или 4br",
    )

    # — цены —
    avg_sale_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    avg_rent_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    median_sale_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    median_rent_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    min_sale_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    max_sale_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    min_rent_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    max_rent_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )

    # — экспозиция (дней) —
    avg_exposure_sale = models.FloatField(default=0)
    avg_exposure_rent = models.FloatField(default=0)

    # — количество объявлений —
    sale_count = models.PositiveIntegerField(default=0)
    rent_count = models.PositiveIntegerField(default=0)

    # — относительные метрики —
    ads_per_unit_sale = models.FloatField(
        default=0, help_text="sale_count / total_units"
    )
    ads_per_unit_rent = models.FloatField(
        default=0, help_text="rent_count / total_units"
    )
    roi = models.FloatField(default=0, help_text="avg_rent_price / avg_sale_price")
    liquidity_sale = models.FloatField(
        default=0, help_text="sale_count / total_units / 12"
    )
    liquidity_rent = models.FloatField(
        default=0, help_text="rent_count / total_units / 12"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("building", "bedrooms"),)
        ordering = ("building", "bedrooms")

    @classmethod
    def run_snapshot_for_all(cls):
        # Импортируем модель Building из приложения pfimport, а не из building_reports
        from realty.pfimport.models import (
            PFListSale,
            PFListRent,
            PFJsonUpload,
            Building as PFBuilding,
        )

        uploader = PFJsonUpload()
        today = timezone.now().date()

        # Теперь PFBuilding действительно имеет поле dld_building
        for b in PFBuilding.objects.select_related("area", "dld_building").all():
            # … ваш код дальше без изменений …

            # забираем все объявления sale и rent для этого здания
            sale_qs = list(PFListSale.objects.filter(building=b, price__isnull=False))
            rent_qs = list(PFListRent.objects.filter(building=b, price__isnull=False))

            # группируем объявления по нормализованной «комнатности»
            groups: dict[str, dict] = {}
            for obj in sale_qs + rent_qs:
                key = uploader._normalize_bedroom_key(obj.bedrooms)
                if key not in groups:
                    groups[key] = {"sales": [], "rents": []}

            for obj in sale_qs:
                key = uploader._normalize_bedroom_key(obj.bedrooms)
                groups[key]["sales"].append(obj)
            for obj in rent_qs:
                key = uploader._normalize_bedroom_key(obj.bedrooms)
                groups[key]["rents"].append(obj)

            # общее число квартир берем из связанного realty.main.models.Building
            units = getattr(b.dld_building, "total_units", 0) or 0

            # функция для медианы
            def median(lst: list[float]) -> float:
                if not lst:
                    return 0
                s = sorted(lst)
                n = len(s)
                return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2

            # для каждой «комнатности» считаем метрики
            for bed, bucket in groups.items():
                sale_prices = [float(o.price) for o in bucket["sales"]]
                rent_prices = [float(o.price) for o in bucket["rents"]]

                # дни экспозиции
                sale_days = [
                    (today - o.added_on.date()).days
                    for o in bucket["sales"]
                    if o.added_on
                ]
                rent_days = [
                    (today - o.added_on.date()).days
                    for o in bucket["rents"]
                    if o.added_on
                ]

                sale_count = len(sale_prices)
                rent_count = len(rent_prices)

                avg_sale = sum(sale_prices) / sale_count if sale_count else 0
                avg_rent = sum(rent_prices) / rent_count if rent_count else 0

                defaults = {
                    "avg_sale_price": Decimal(f"{avg_sale:.2f}"),
                    "avg_rent_price": Decimal(f"{avg_rent:.2f}"),
                    "median_sale_price": Decimal(f"{median(sale_prices):.2f}"),
                    "median_rent_price": Decimal(f"{median(rent_prices):.2f}"),
                    "min_sale_price": Decimal(
                        f"{min(sale_prices) if sale_prices else 0:.2f}"
                    ),
                    "max_sale_price": Decimal(
                        f"{max(sale_prices) if sale_prices else 0:.2f}"
                    ),
                    "min_rent_price": Decimal(
                        f"{min(rent_prices) if rent_prices else 0:.2f}"
                    ),
                    "max_rent_price": Decimal(
                        f"{max(rent_prices) if rent_prices else 0:.2f}"
                    ),
                    "avg_exposure_sale": sum(sale_days) / sale_count
                    if sale_count
                    else 0,
                    "avg_exposure_rent": sum(rent_days) / rent_count
                    if rent_count
                    else 0,
                    "sale_count": sale_count,
                    "rent_count": rent_count,
                    "ads_per_unit_sale": sale_count / units if units else 0,
                    "ads_per_unit_rent": rent_count / units if units else 0,
                    "roi": (avg_rent / avg_sale) if avg_sale else 0,
                    "liquidity_sale": sale_count / (units or 1) / 12,
                    "liquidity_rent": rent_count / (units or 1) / 12,
                }

                cls.objects.update_or_create(
                    building=b, bedrooms=bed, defaults=defaults
                )


class BuildingReportSnapshot(models.Model):
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="report_snapshots"
    )
    number_of_rooms = models.CharField(max_length=50, db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    prev_period_start = models.DateField()
    prev_period_end = models.DateField()

    avg_price_sales = models.DecimalField(max_digits=15, decimal_places=2)
    median_price_sales = models.DecimalField(max_digits=15, decimal_places=2)
    min_price_sales = models.DecimalField(max_digits=15, decimal_places=2)
    max_price_sales = models.DecimalField(max_digits=15, decimal_places=2)
    transactions_count_sales = models.PositiveIntegerField()
    total_units = models.PositiveIntegerField()
    rooms_count_sales = models.PositiveIntegerField()
    liquidity_sales = models.FloatField()

    avg_price_sales_prev = models.DecimalField(max_digits=15, decimal_places=2)
    median_price_sales_prev = models.DecimalField(max_digits=15, decimal_places=2)
    min_price_sales_prev = models.DecimalField(max_digits=15, decimal_places=2)
    max_price_sales_prev = models.DecimalField(max_digits=15, decimal_places=2)
    transactions_count_sales_prev = models.PositiveIntegerField()
    rooms_count_sales_prev = models.PositiveIntegerField()
    liquidity_sales_prev = models.FloatField()

    avg_price_rental = models.DecimalField(max_digits=15, decimal_places=2)
    median_price_rental = models.DecimalField(max_digits=15, decimal_places=2)
    min_price_rental = models.DecimalField(max_digits=15, decimal_places=2)
    max_price_rental = models.DecimalField(max_digits=15, decimal_places=2)
    transactions_count_rental = models.PositiveIntegerField()
    rooms_count_rental = models.PositiveIntegerField()
    liquidity_rental = models.FloatField()

    avg_price_rental_prev = models.DecimalField(max_digits=15, decimal_places=2)
    median_price_rental_prev = models.DecimalField(max_digits=15, decimal_places=2)
    min_price_rental_prev = models.DecimalField(max_digits=15, decimal_places=2)
    max_price_rental_prev = models.DecimalField(max_digits=15, decimal_places=2)
    transactions_count_rental_prev = models.PositiveIntegerField()
    rooms_count_rental_prev = models.PositiveIntegerField()
    liquidity_rental_prev = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            "building",
            "number_of_rooms",
            "period_start",
            "period_end",
        )
        ordering = ("-period_start", "building", "number_of_rooms")

    @classmethod
    def run_snapshot_for_all(cls):
        today = timezone.localdate()
        period_end = today
        period_start = today - relativedelta(years=1)
        prev_period_end = period_start
        prev_period_start = period_start - relativedelta(years=1)

        for b in Building.objects.all():
            rooms_sales = set(
                MergedTransaction.objects.filter(
                    building=b, date_of_transaction__range=(period_start, period_end)
                ).values_list("number_of_rooms", flat=True)
            )
            rooms_rent = set(
                MergedRentalTransaction.objects.filter(
                    building=b, date_of_transaction__range=(period_start, period_end)
                ).values_list("number_of_rooms", flat=True)
            )

            for rooms in rooms_sales.union(rooms_rent):

                def calc(qs):
                    prices = list(qs.values_list("transaction_price", flat=True))
                    avg = (
                        qs.aggregate(Avg("transaction_price"))["transaction_price__avg"]
                        or 0
                    )
                    med = sorted(prices)[len(prices) // 2] if prices else 0
                    mn = min(prices) if prices else 0
                    mx = max(prices) if prices else 0
                    cnt = qs.count()

                    first_obj = qs.first()
                    same = first_obj.same_rooms_count_in_building if first_obj else 0

                    liq = cnt / (same or 1) / 12
                    return avg, med, mn, mx, cnt, same, liq

                qs_s = MergedTransaction.objects.filter(
                    building=b,
                    number_of_rooms=rooms,
                    date_of_transaction__range=(period_start, period_end),
                )
                qs_sp = MergedTransaction.objects.filter(
                    building=b,
                    number_of_rooms=rooms,
                    date_of_transaction__range=(prev_period_start, prev_period_end),
                )
                qs_r = MergedRentalTransaction.objects.filter(
                    building=b,
                    number_of_rooms=rooms,
                    date_of_transaction__range=(period_start, period_end),
                )
                qs_rp = MergedRentalTransaction.objects.filter(
                    building=b,
                    number_of_rooms=rooms,
                    date_of_transaction__range=(prev_period_start, prev_period_end),
                )

                s, ms, ns, xs, cs, ss, ls = calc(qs_s)
                sp, msp, nsp, xsp, csp, ssp, lsp = calc(qs_sp)
                r, mr, nr, xr, cr, sr, lr = calc(qs_r)
                rp, mrp, nrp, xrp, crp, srp, lrp = calc(qs_rp)

                data = dict(
                    period_start=period_start,
                    period_end=period_end,
                    prev_period_start=prev_period_start,
                    prev_period_end=prev_period_end,
                    avg_price_sales=s,
                    median_price_sales=ms,
                    min_price_sales=ns,
                    max_price_sales=xs,
                    transactions_count_sales=cs,
                    total_units=b.total_units or 0,
                    rooms_count_sales=ss,
                    liquidity_sales=ls,
                    avg_price_sales_prev=sp,
                    median_price_sales_prev=msp,
                    min_price_sales_prev=nsp,
                    max_price_sales_prev=xsp,
                    transactions_count_sales_prev=csp,
                    rooms_count_sales_prev=ssp,
                    liquidity_sales_prev=lsp,
                    avg_price_rental=r,
                    median_price_rental=mr,
                    min_price_rental=nr,
                    max_price_rental=xr,
                    transactions_count_rental=cr,
                    rooms_count_rental=sr,
                    liquidity_rental=lr,
                    avg_price_rental_prev=rp,
                    median_price_rental_prev=mrp,
                    min_price_rental_prev=nrp,
                    max_price_rental_prev=xrp,
                    transactions_count_rental_prev=crp,
                    rooms_count_rental_prev=srp,
                    liquidity_rental_prev=lrp,
                )

                cls.objects.update_or_create(
                    building=b,
                    number_of_rooms=rooms,
                    period_start=period_start,
                    period_end=period_end,
                    defaults=data,
                )


class AreaReportSnapshot(models.Model):
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, related_name="report_snapshots"
    )
    number_of_rooms = models.CharField(max_length=50, db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    prev_period_start = models.DateField()
    prev_period_end = models.DateField()

    # —\ продажа ——
    avg_price_sales = models.DecimalField(max_digits=15, decimal_places=2)
    median_price_sales = models.DecimalField(max_digits=15, decimal_places=2)
    min_price_sales = models.DecimalField(max_digits=15, decimal_places=2)
    max_price_sales = models.DecimalField(max_digits=15, decimal_places=2)
    transactions_count_sales = models.PositiveIntegerField()
    rooms_count_sales = models.PositiveIntegerField()
    liquidity_sales = models.FloatField()
    # — продажи_prev ——
    avg_price_sales_prev = models.DecimalField(max_digits=15, decimal_places=2)
    median_price_sales_prev = models.DecimalField(max_digits=15, decimal_places=2)
    min_price_sales_prev = models.DecimalField(max_digits=15, decimal_places=2)
    max_price_sales_prev = models.DecimalField(max_digits=15, decimal_places=2)
    transactions_count_sales_prev = models.PositiveIntegerField()
    rooms_count_sales_prev = models.PositiveIntegerField()
    liquidity_sales_prev = models.FloatField()
    # — аренда ——
    avg_price_rental = models.DecimalField(max_digits=15, decimal_places=2)
    median_price_rental = models.DecimalField(max_digits=15, decimal_places=2)
    min_price_rental = models.DecimalField(max_digits=15, decimal_places=2)
    max_price_rental = models.DecimalField(max_digits=15, decimal_places=2)
    transactions_count_rental = models.PositiveIntegerField()
    rooms_count_rental = models.PositiveIntegerField()
    liquidity_rental = models.FloatField()
    # — аренда_prev ——
    avg_price_rental_prev = models.DecimalField(max_digits=15, decimal_places=2)
    median_price_rental_prev = models.DecimalField(max_digits=15, decimal_places=2)
    min_price_rental_prev = models.DecimalField(max_digits=15, decimal_places=2)
    max_price_rental_prev = models.DecimalField(max_digits=15, decimal_places=2)
    transactions_count_rental_prev = models.PositiveIntegerField()
    rooms_count_rental_prev = models.PositiveIntegerField()
    liquidity_rental_prev = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            "area",
            "number_of_rooms",
            "period_start",
            "period_end",
        )
        ordering = ("-period_start", "area", "number_of_rooms")

    @classmethod
    def run_snapshot_for_all(cls):
        today = timezone.localdate()
        p_end = today
        p_start = today - relativedelta(years=1)
        pp_end = p_start
        pp_start = p_start - relativedelta(years=1)

        for area in Area.objects.all():
            rooms_sales = set(
                MergedTransaction.objects.filter(
                    area=area, date_of_transaction__range=(p_start, p_end)
                ).values_list("number_of_rooms", flat=True)
            )
            rooms_rent = set(
                MergedRentalTransaction.objects.filter(
                    area=area, date_of_transaction__range=(p_start, p_end)
                ).values_list("number_of_rooms", flat=True)
            )

            for rooms in rooms_sales.union(rooms_rent):

                def calc(qs):
                    prices = list(qs.values_list("transaction_price", flat=True))
                    avg = (
                        qs.aggregate(Avg("transaction_price"))["transaction_price__avg"]
                        or 0
                    )
                    med = sorted(prices)[len(prices) // 2] if prices else 0
                    mn = min(prices) if prices else 0
                    mx = max(prices) if prices else 0
                    cnt = qs.count()
                    # вместо прямого запроса в БД — берём свойство у первого объекта
                    first_obj = qs.first()
                    same = first_obj.same_rooms_count_in_building if first_obj else 0
                    liq = cnt / (same or 1) / 12
                    return avg, med, mn, mx, cnt, same, liq

                ss = MergedTransaction.objects.filter(
                    area=area,
                    number_of_rooms=rooms,
                    date_of_transaction__range=(p_start, p_end),
                )
                sp = MergedTransaction.objects.filter(
                    area=area,
                    number_of_rooms=rooms,
                    date_of_transaction__range=(pp_start, pp_end),
                )
                rs = MergedRentalTransaction.objects.filter(
                    area=area,
                    number_of_rooms=rooms,
                    date_of_transaction__range=(p_start, p_end),
                )
                rp = MergedRentalTransaction.objects.filter(
                    area=area,
                    number_of_rooms=rooms,
                    date_of_transaction__range=(pp_start, pp_end),
                )

                s, ms, ns, xs, cs, scs, ls = calc(ss)
                sp0, ms0, ns0, xs0, cs0, scsp, ls0 = calc(sp)
                r, Mr, nr, xr, cr, scr, lr = calc(rs)
                rp0, mrp0, nrp0, xrp0, crp0, scrp, lrp0 = calc(rp)

                data = dict(
                    period_start=p_start,
                    period_end=p_end,
                    prev_period_start=pp_start,
                    prev_period_end=pp_end,
                    avg_price_sales=s,
                    median_price_sales=ms,
                    min_price_sales=ns,
                    max_price_sales=xs,
                    transactions_count_sales=cs,
                    rooms_count_sales=scs,
                    liquidity_sales=ls,
                    avg_price_sales_prev=sp0,
                    median_price_sales_prev=ms0,
                    min_price_sales_prev=ns0,
                    max_price_sales_prev=xs0,
                    transactions_count_sales_prev=cs0,
                    rooms_count_sales_prev=scsp,
                    liquidity_sales_prev=ls0,
                    avg_price_rental=r,
                    median_price_rental=Mr,
                    min_price_rental=nr,
                    max_price_rental=xr,
                    transactions_count_rental=cr,
                    rooms_count_rental=scr,
                    liquidity_rental=lr,
                    avg_price_rental_prev=rp0,
                    median_price_rental_prev=mrp0,
                    min_price_rental_prev=nrp0,
                    max_price_rental_prev=xrp0,
                    transactions_count_rental_prev=crp0,
                    rooms_count_rental_prev=scrp,
                    liquidity_rental_prev=lrp0,
                )

                cls.objects.update_or_create(
                    area=area,
                    number_of_rooms=rooms,
                    period_start=p_start,
                    period_end=p_end,
                    defaults=data,
                )
