from django import forms

from .models import BookReview


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class BookReviewForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BookReview
        fields = ["book", "member", "rating", "review_text"]
        widgets = {"review_text": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class ReviewModerationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BookReview
        fields = ["status", "moderation_notes"]
        widgets = {"moderation_notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
