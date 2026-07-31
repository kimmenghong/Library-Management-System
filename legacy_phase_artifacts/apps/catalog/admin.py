from django.contrib import admin

from .models import Author, Book, BookCopy, BookLocation, Category, Publisher, Shelf


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "nationality", "is_active", "created_at")
    list_filter = ("is_active", "nationality")
    search_fields = ("name", "biography", "nationality")
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "contact_email", "phone", "address")
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "parent", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "code", "description")
    autocomplete_fields = ("parent",)
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ("shelf_code", "name", "floor", "section", "is_active")
    list_filter = ("floor", "section", "is_active")
    search_fields = ("shelf_code", "name", "section", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(BookLocation)
class BookLocationAdmin(admin.ModelAdmin):
    list_display = ("label", "shelf", "aisle", "row", "column", "is_active")
    list_filter = ("shelf", "is_active")
    search_fields = ("label", "shelf__shelf_code", "aisle", "row", "column")
    autocomplete_fields = ("shelf",)
    readonly_fields = ("created_at", "updated_at")


class BookCopyInline(admin.TabularInline):
    model = BookCopy
    extra = 0
    fields = ("copy_code", "barcode", "shelf", "location", "status", "condition", "acquired_date")
    readonly_fields = ("copy_code", "status")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "book_code", "isbn", "category", "publisher", "status", "total_copies")
    list_filter = ("status", "category", "publisher", "language")
    search_fields = ("title", "subtitle", "isbn", "book_code", "authors__name")
    filter_horizontal = ("authors",)
    readonly_fields = ("status", "created_at", "updated_at")
    list_select_related = ("category", "publisher")
    inlines = [BookCopyInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ("copy_code", "book", "barcode", "status", "condition", "shelf", "location")
    list_filter = ("status", "condition", "shelf", "location")
    search_fields = ("copy_code", "barcode", "book__title", "book__isbn", "book__book_code")
    autocomplete_fields = ("book", "shelf", "location")
    readonly_fields = ("copy_code", "status", "qr_code", "created_at", "updated_at")
    list_select_related = ("book", "shelf", "location")
