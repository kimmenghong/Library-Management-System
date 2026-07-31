from django import forms

from .models import FAQ, Feedback, SupportTicket


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class FAQForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ["question", "answer", "category", "display_order", "is_active"]
        widgets = {"answer": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class SupportTicketForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["subject", "message", "priority"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class SupportTicketAdminForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["status", "priority", "assigned_to", "response"]
        widgets = {"response": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class FeedbackForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["name", "email", "rating", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
