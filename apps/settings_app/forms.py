from django import forms

from .models import BackupRecord, BackupSchedule, LibraryProfile, SystemSetting


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class LibraryProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LibraryProfile
        fields = ["name", "address", "phone", "email", "website", "logo", "theme"]
        widgets = {"address": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class SystemSettingForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SystemSetting
        fields = ["key", "value", "description"]
        widgets = {"value": forms.Textarea(attrs={"rows": 3}), "description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class BackupScheduleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BackupSchedule
        fields = ["frequency", "backup_time", "is_enabled", "backup_directory"]
        widgets = {"backup_time": forms.TimeInput(attrs={"type": "time"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class RestoreBackupForm(BootstrapFormMixin, forms.Form):
    backup = forms.ModelChoiceField(queryset=BackupRecord.objects.filter(status=BackupRecord.CREATED))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
