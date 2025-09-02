from django import forms
from realty.main.models import Building


class BuildingReportForm(forms.Form):
    building = forms.ModelChoiceField(
        queryset=Building.objects.order_by("english_name"),
        label="Building",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
