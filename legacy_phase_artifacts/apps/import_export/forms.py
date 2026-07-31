from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError

from .models import ExportJob, ImportJob


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class BookImportForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ImportJob
        fields = ["source_file"]

    def clean_source_file(self):
        file = self.cleaned_data["source_file"]
        if Path(file.name).suffix.lower() not in {".csv", ".xlsx"}:
            raise ValidationError("Upload a CSV or Excel (.xlsx) file.")
        return file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class ExportForm(BootstrapFormMixin, forms.Form):
    target = forms.ChoiceField(choices=ExportJob.TARGET_CHOICES)
    file_format = forms.ChoiceField(choices=[("csv", "CSV"), ("xlsx", "Excel")])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
