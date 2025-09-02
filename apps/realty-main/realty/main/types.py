# types.py
from typing import List
from typing import Optional

import strawberry
import strawberry_django
from django.contrib.auth import get_user_model
from realty.main import models
from strawberry import auto


@strawberry_django.type(get_user_model())
class User:
    username: auto
    email: auto


@strawberry_django.input(get_user_model())
class UserInput:
    username: auto
    password: auto


@strawberry.type
class AreaSuggestion:
    id: int
    nameEn: Optional[str]
    nameAr: Optional[str]


@strawberry.type
class BuildingSuggestion:
    id: int
    nameEn: Optional[str]
    nameAr: Optional[str]
    buildingNumber: Optional[str]


@strawberry.type
class ProjectSuggestion:
    id: int
    englishName: Optional[str]
    arabicName: Optional[str]
    nameEn: Optional[str]
    nameAr: Optional[str]
    projectNumber: Optional[str]


@strawberry.type
class AutocompleteResult:
    areas: List[AreaSuggestion]
    buildings: List[BuildingSuggestion]
    projects: List[ProjectSuggestion]


@strawberry.type
class FilterOptions:
    property_components: List[str]
    something_important_v1: List[str]
    periods: List[str]


@strawberry.type
class AggregationType:
    value: float
    dynamic: float
    versus: float
    comparison: float
    range: str


@strawberry.type
class AggregationResultType:
    total_buildings: int
    total_deals: int
    total_properties: Optional[int]
    growth_dynamic_percent: float

    average_price: AggregationType
    median_price: AggregationType
    average_price_per_sqm: AggregationType = strawberry.field(name="averagePricePerSQM")
    price_range: AggregationType
    deals: AggregationType
    deals_volume: AggregationType
    liquidity: AggregationType
    roi: AggregationType


@strawberry_django.type(models.MergedTransaction)
class MergedTransaction:
    """
    Данный класс теперь динамически возвращает поля из MergedRentalTransaction,
    если transaction_type == 'rental', и из MergedTransaction, если transaction_type == 'sales'.
    """

    @strawberry.field(name="id")
    def get_id(self) -> strawberry.ID:
        """
        В режиме 'rental': возвращаем contract_id (string).
        В остальных случаях: возвращаем pk записи.
        """
        if self.transaction_type == "rental":
            # contract_id есть только в MergedRentalTransaction
            return getattr(self, "contract_id", str(self.pk)) or str(self.pk)
        return str(self.pk)

    @strawberry.field(name="roomsEn")
    def get_rooms_en(self) -> Optional[str]:
        """
        И в продажах, и в аренде поле number_of_rooms называется одинаково.
        """
        return self.number_of_rooms

    @strawberry.field(name="actualWorth")
    def get_actual_worth(self) -> Optional[float]:
        """
        Для аренды: annual_amount
        Для продаж: transaction_price
        """
        if self.transaction_type == "rental":
            return getattr(self, "annual_amount", None)
        if self.transaction_price is not None:
            return float(self.transaction_price)
        return None

    @strawberry.field
    def meter_sale_price(self) -> Optional[float]:
        """
        И в продажах, и в аренде поле называется одинаково.
        """
        if self.meter_sale_price is not None:
            return float(self.meter_sale_price)
        return None

    @strawberry.field
    def deal_year(self) -> Optional[int]:
        """
        Для аренды: только year из date_of_transaction.
        Для продаж: берём поле deal_year из MergedTransaction.
        """
        if self.transaction_type == "rental":
            date_of_transaction = getattr(self, "date_of_transaction", None)
            return date_of_transaction.year if date_of_transaction else None
        return self.deal_year

    @strawberry.field
    def date_of_transaction(self) -> Optional[str]:
        """
        Для аренды: contract_start_date + '_-_' + contract_end_date
        Для продаж: обычное date_of_transaction
        """
        if self.transaction_type == "rental":
            start = str(getattr(self, "contract_start_date", "")) or ""
            end = str(getattr(self, "contract_end_date", "")) or ""
            return f"{start}_-_{end}"
        dt = getattr(self, "date_of_transaction", None)
        return str(dt) if dt else None

    @strawberry.field
    def building_name(self) -> Optional[str]:
        """
        И в продажах, и в аренде название поля совпадает (building_name).
        """
        return self.building_name

    @strawberry.field
    def location_name(self) -> Optional[str]:
        """
        Для аренды: area.name_en
        Для продаж: поле location_name в MergedTransaction.
        """
        if self.transaction_type == "rental":
            area_obj = getattr(self, "area", None)
            return area_obj.name_en if area_obj else None
        return self.location_name

    @strawberry.field
    def sqm(self) -> Optional[float]:
        """
        Совпадает в обеих моделях.
        """
        return self.sqm

    @strawberry.field
    def roi(self) -> Optional[float]:
        """
        Для аренды: null
        Для продаж: берём из MergedTransaction.
        """
        if self.transaction_type == "rental":
            return None
        return self.roi

    @strawberry.field
    def area_name_en(self) -> Optional[str]:
        """
        Изначально в MergedTransaction: area.name_en
        В аренде: тоже area.name_en, но подстраховываемся через getattr.
        """
        if self.transaction_type == "rental":
            area_obj = getattr(self, "area", None)
            return area_obj.name_en if area_obj else None
        return self.area.name_en if self.area else None

    @strawberry.field
    def developer_name_en(self) -> Optional[str]:
        """
        Для аренды: project.developer.english_name (если есть).
        Для продаж: building.project.developer.english_name
        """
        if self.transaction_type == "rental":
            project_obj = getattr(self, "project", None)
            if project_obj and project_obj.developer:
                return project_obj.developer.english_name
            return None

        if self.building and self.building.project and self.building.project.developer:
            return self.building.project.developer.english_name
        return None

    @strawberry.field(name="typename")
    def get_typename(self) -> str:
        """
        Возвращает "__typename", чтобы на фронте отличать MergedRentTransaction от MergedTransaction.
        """
        if self.transaction_type == "rental":
            return "MergedRentTransaction"
        return "MergedTransaction"


@strawberry_django.order(models.MergedTransaction)
class MergedTransactionOrder:
    date_of_transaction: auto
    roi: auto
    sqm: auto
