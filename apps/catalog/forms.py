from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Author,
    Book,
    BookCopy,
    BookLocation,
    Category,
    Publisher,
    Shelf,
    normalize_isbn,
)


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css_class = "form-select"
            else:
                css_class = "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()


class AuthorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Author
        fields = ["name", "biography", "nationality", "date_of_birth", "photo", "is_active"]
        widgets = {
            "biography": forms.Textarea(attrs={"rows": 4}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].widget.attrs["accept"] = ".jpg,.jpeg,.png,.webp"
        self.apply_bootstrap()


class PublisherForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ["name", "address", "contact_email", "phone", "website", "is_active"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        queryset = Publisher.objects.filter(name__iexact=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError("A publisher with this name already exists.")
        return name


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "code", "parent", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parent_queryset = Category.objects.order_by("name")
        if self.instance.pk:
            excluded_ids = {self.instance.pk}
            pending = [self.instance.pk]
            while pending:
                children = list(
                    Category.objects.filter(parent_id__in=pending).values_list("pk", flat=True)
                )
                new_ids = set(children) - excluded_ids
                excluded_ids.update(new_ids)
                pending = list(new_ids)
            parent_queryset = parent_queryset.exclude(pk__in=excluded_ids)
        self.fields["parent"].queryset = parent_queryset
        self.apply_bootstrap()

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        queryset = Category.objects.filter(code__iexact=code)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError("A category with this code already exists.")
        return code


class ShelfForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Shelf
        fields = ["shelf_code", "name", "floor", "section", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_shelf_code(self):
        code = self.cleaned_data["shelf_code"].strip().upper()
        queryset = Shelf.objects.filter(shelf_code__iexact=code)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError("A shelf with this code already exists.")
        return code


class BookLocationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BookLocation
        fields = ["shelf", "aisle", "row", "column", "label", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shelves = Shelf.objects.filter(is_active=True)
        if self.instance.pk and self.instance.shelf_id:
            shelves = Shelf.objects.filter(pk=self.instance.shelf_id) | shelves
        self.fields["shelf"].queryset = shelves.distinct().order_by("shelf_code")
        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        shelf = cleaned_data.get("shelf")
        label = cleaned_data.get("label", "").strip()
        if shelf and label:
            queryset = BookLocation.objects.filter(shelf=shelf, label__iexact=label)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error("label", "This label already exists on the selected shelf.")
        cleaned_data["label"] = label
        return cleaned_data


class BookForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "subtitle",
            "isbn",
            "book_code",
            "authors",
            "publisher",
            "category",
            "publication_year",
            "edition",
            "language",
            "pages",
            "description",
            "cover_image",
        ]
        widgets = {
            "authors": forms.SelectMultiple(attrs={"size": 7}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["book_code"].help_text = "Leave blank to generate a permanent code."
        self.fields["isbn"].help_text = "ISBN-10 or ISBN-13; spaces and hyphens are normalized."
        self.fields["cover_image"].widget.attrs["accept"] = ".jpg,.jpeg,.png,.webp"
        self.fields["authors"].queryset = Author.objects.order_by("name")
        self.fields["publisher"].queryset = Publisher.objects.order_by("name")
        self.fields["category"].queryset = Category.objects.select_related("parent").order_by("name")
        if self.instance.pk and self.instance.copies.exists():
            self.fields["book_code"].disabled = True
        self.apply_bootstrap()

    def clean_isbn(self):
        isbn = normalize_isbn(self.cleaned_data.get("isbn"))
        if isbn:
            queryset = Book.objects.filter(isbn=isbn)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("A book with this ISBN already exists.")
        return isbn

    def clean_book_code(self):
        code = self.cleaned_data.get("book_code", "").strip().upper()
        if code:
            queryset = Book.objects.filter(book_code__iexact=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("A book with this code already exists.")
        return code


class BookCopyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BookCopy
        fields = [
            "book",
            "barcode",
            "shelf",
            "location",
            "condition",
            "acquired_date",
            "price",
            "notes",
        ]
        widgets = {
            "acquired_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, book=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["barcode"].help_text = "Leave blank to use the generated copy code."
        self.fields["book"].queryset = Book.objects.order_by("title")
        self.fields["shelf"].queryset = Shelf.objects.filter(is_active=True).order_by("shelf_code")

        shelf_id = None
        if self.is_bound:
            shelf_id = self.data.get(self.add_prefix("shelf"))
        elif self.instance.pk:
            shelf_id = self.instance.shelf_id
        if shelf_id and str(shelf_id).isdigit():
            self.fields["location"].queryset = BookLocation.objects.filter(
                shelf_id=shelf_id,
                is_active=True,
            ).order_by("label")
        else:
            self.fields["location"].queryset = BookLocation.objects.filter(
                is_active=True
            ).select_related("shelf").order_by("shelf__shelf_code", "label")

        if self.instance.pk:
            self.fields["book"].queryset = Book.objects.filter(pk=self.instance.book_id)
            self.fields["book"].disabled = True
        elif book:
            self.fields["book"].queryset = Book.objects.filter(pk=book.pk)
            self.fields["book"].initial = book
            self.fields["book"].disabled = True

        self.fields["condition"].choices = [
            choice
            for choice in BookCopy.CONDITION_CHOICES
            if choice[0] != BookCopy.DAMAGED_CONDITION
        ]
        self.apply_bootstrap()

    def clean_barcode(self):
        barcode = (self.cleaned_data.get("barcode") or "").strip().upper()
        if barcode:
            queryset = BookCopy.objects.filter(barcode__iexact=barcode)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("A copy with this barcode already exists.")
        return barcode or None

    def clean(self):
        cleaned_data = super().clean()
        shelf = cleaned_data.get("shelf")
        location = cleaned_data.get("location")
        if location and shelf and location.shelf_id != shelf.pk:
            self.add_error("location", "Book location must belong to the selected shelf.")
        return cleaned_data


class AdvancedBookSearchForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(required=False, label="Keyword")
    title = forms.CharField(required=False)
    isbn = forms.CharField(required=False)
    barcode = forms.CharField(required=False)
    book_code = forms.CharField(required=False)
    author = forms.ModelChoiceField(queryset=Author.objects.none(), required=False)
    publisher = forms.ModelChoiceField(queryset=Publisher.objects.none(), required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)
    shelf = forms.ModelChoiceField(queryset=Shelf.objects.none(), required=False)
    availability = forms.ChoiceField(
        choices=[("", "Any availability")] + BookCopy.STATUS_CHOICES,
        required=False,
    )
    publication_year = forms.IntegerField(min_value=1000, max_value=9999, required=False)
    language = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["author"].queryset = Author.objects.filter(is_active=True).order_by("name")
        self.fields["publisher"].queryset = Publisher.objects.filter(is_active=True).order_by("name")
        self.fields["category"].queryset = Category.objects.filter(is_active=True).order_by("name")
        self.fields["shelf"].queryset = Shelf.objects.filter(is_active=True).order_by("shelf_code")
        self.apply_bootstrap()
