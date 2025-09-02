# utils.py
from datetime import datetime
from enum import Enum
from typing import List
from typing import Optional
from typing import Union

import strawberry
from dateutil.relativedelta import relativedelta
from realty.main.models import Area
from realty.main.models import Building
from realty.main.models import MergedRentalTransaction
from realty.main.models import MergedTransaction
from realty.main.models import Project


valid_periods = {
    "YTD": relativedelta(month=1, day=1),
    "1 week": relativedelta(weeks=1),
    "1 month": relativedelta(months=1),
    "3 months": relativedelta(months=3),
    "6 months": relativedelta(months=6),
    "1 year": relativedelta(years=1),
    "2 years": relativedelta(years=2),
}


@strawberry.enum
class Period(Enum):
    WEEK = strawberry.enum_value("1 week")
    MONTH = strawberry.enum_value("1 month")
    MONTH3 = strawberry.enum_value("3 months")
    MONTH6 = strawberry.enum_value("6 months")
    YEAR = strawberry.enum_value("1 year")
    YEAR2 = strawberry.enum_value("2 years")


def _get_period_range(period: str):
    now = datetime.now().date()
    if period == "YTD":
        start = datetime(now.year, 1, 1).date()
        return start, now

    if period not in valid_periods:
        raise ValueError(f"Unsupported period '{period}'.")
    delta = valid_periods[period]
    end = now
    start = end - delta
    return start, end


# Обёртка, имитирующая поведение QuerySet (для offset pagination)
class FakeQuerySet:
    def __init__(self, data: List, model=None):
        self._data = data
        self.model = model

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

    def count(self):
        return len(self._data)

    def all(self):
        return self

    def order_by(self, *args, **kwargs):
        # Если требуется сортировка – реализовать можно, пока что no-op
        return self

    @property
    def query(self):
        # Для поддержки offset pagination возвращаем фиктивный объект с атрибутом `annotations` и `ordered`
        class FakeQuery:
            annotations = {}
            ordered = True

        return FakeQuery()

    @property
    def ordered(self):
        return self


def _build_transactions_queryset(
    transaction_type: str,
    search_substring: Optional[str],
    property_components: Optional[List[str]],
    periods: Optional[str],
) -> Union[List[MergedTransaction], FakeQuerySet]:
    """
    Если transaction_type == "rental", берём объекты MergedRentalTransaction,
    фильтруем их и для каждого создаём «фейковый» объект MergedTransaction,
    в который записываем исходный объект в атрибут _rental_data.
    Возвращаем FakeQuerySet для offset pagination.

    Иначе (sales) – возвращаем обычный QuerySet MergedTransaction.
    """
    if transaction_type == "rental":
        qs_r = MergedRentalTransaction.objects.all()
        if search_substring and search_substring.strip():
            area = Area.objects.filter(name_en__icontains=search_substring).first()
            if area:
                qs_r = qs_r.filter(building__area=area)
            else:
                building = Building.objects.filter(
                    english_name__icontains=search_substring
                ).first()
                if building:
                    qs_r = qs_r.filter(building=building)
                else:
                    project = Project.objects.filter(
                        english_name__icontains=search_substring
                    ).first()
                    if project:
                        qs_r = qs_r.filter(building__project=project)
                    else:
                        return FakeQuerySet([], model=MergedTransaction)
        if property_components and len(property_components) > 0:
            qs_r = qs_r.filter(number_of_rooms__in=property_components)
        if periods:
            start_date, end_date = _get_period_range(periods)
            qs_r = qs_r.filter(date_of_transaction__range=(start_date, end_date))
        fake_list = []
        for rent_obj in qs_r:
            fake_obj = MergedTransaction(
                transaction_type="rental",
                building=rent_obj.building,
                date_of_transaction=rent_obj.date_of_transaction,
                building_name=rent_obj.building_name,
                location_name=rent_obj.location_name,
                number_of_rooms=rent_obj.number_of_rooms,
                sqm=rent_obj.sqm,
                period=rent_obj.period,
                meter_sale_price=rent_obj.meter_sale_price,
            )
            fake_obj._rental_data = rent_obj
            fake_list.append(fake_obj)
        return FakeQuerySet(fake_list, model=MergedTransaction)
    else:
        qs = MergedTransaction.objects.filter(transaction_type="sales")
        if search_substring and search_substring.strip():
            area = Area.objects.filter(name_en__icontains=search_substring).first()
            if area:
                qs = qs.filter(building__area=area)
            else:
                building = Building.objects.filter(
                    english_name__icontains=search_substring
                ).first()
                if building:
                    qs = qs.filter(building=building)
                else:
                    project = Project.objects.filter(
                        english_name__icontains=search_substring
                    ).first()
                    if project:
                        qs = qs.filter(building__project=project)
                    else:
                        return qs.none()
        if property_components and len(property_components) > 0:
            qs = qs.filter(number_of_rooms__in=property_components)
        if periods:
            start_date, end_date = _get_period_range(periods)
            qs = qs.filter(date_of_transaction__range=(start_date, end_date))
        return qs
