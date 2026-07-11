from django import forms

from .models import Announcement


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.Select) or isinstance(field.widget, forms.SelectMultiple):
                css_class = "form-select"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class AnnouncementForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "content", "target_roles", "status", "publish_date", "expire_date", "send_email"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
            "target_roles": forms.SelectMultiple(attrs={"size": 6}),
            "publish_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expire_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        publish_date = cleaned_data.get("publish_date")
        expire_date = cleaned_data.get("expire_date")
        if publish_date and expire_date and expire_date < publish_date:
            raise forms.ValidationError("Expire date must be after the publish date.")
        return cleaned_data
