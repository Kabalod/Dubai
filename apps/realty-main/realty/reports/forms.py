from django import forms
from .models import DldBuildingReport, BEDROOM_CHOICES


class DldBuildingReportFilterForm(forms.Form):
    english_name = forms.CharField(
        label="Building name contains",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Enter building name"}),
    )
    bedrooms = forms.ChoiceField(
        label="Bedrooms", required=False, choices=[("", "Any")] + BEDROOM_CHOICES
    )
