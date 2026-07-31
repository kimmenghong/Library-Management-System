from django import forms

from .models import DigitalBook, DigitalBookCategory


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.Select) or isinstance(field.widget, forms.SelectMultiple):
                css_class = "form-select"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class DigitalBookCategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DigitalBookCategory
        fields = ["name", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class DigitalBookForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DigitalBook
        fields = ["title", "book", "category", "file", "description", "allowed_roles", "is_public", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "allowed_roles": forms.SelectMultiple(attrs={"size": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        is_public = cleaned_data.get("is_public")
        allowed_roles = cleaned_data.get("allowed_roles")
        if not is_public and allowed_roles is not None and not allowed_roles.exists():
            raise forms.ValidationError("Select at least one role for restricted digital books, or mark the file as public.")
        return cleaned_data
