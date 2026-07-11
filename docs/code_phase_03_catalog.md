# Code Phase 3: Catalog and Physical Inventory

## Scope

This phase completes the `catalog` Django app for bibliographic records, authors, publishers, categories, shelves, locations, physical copies, ISBNs, barcodes, QR codes, status synchronization, advanced search, and relationship-safe deletion.

## App Structure

```text
apps/catalog/
├── management/commands/seed_sample_data.py
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_alter_booklocation_unique_together_and_more.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── services.py
├── signals.py
├── tests.py
├── urls.py
└── views.py

templates/catalog/
├── author_form.html
├── author_list.html
├── book_detail.html
├── book_form.html
├── book_list.html
├── bookcopy_form.html
├── bookcopy_list.html
├── catalog_tabs.html
├── category_form.html
├── category_list.html
├── confirm_delete.html
├── location_form.html
├── location_list.html
├── publisher_form.html
├── publisher_list.html
├── shelf_form.html
└── shelf_list.html
```

## Models

- `Author`: author identity, biography, nationality, birth date, and photo
- `Publisher`: publisher contact information
- `Category`: hierarchical classification with cycle prevention
- `Shelf`: physical shelf and section metadata
- `BookLocation`: shelf-specific aisle, row, column, and label
- `Book`: bibliographic title, ISBN, authors, publisher, category, language, edition, and aggregate status
- `BookCopy`: permanent copy code, barcode, shelf/location, condition, acquisition data, and operational status

## Business Rules

- ISBN-10 and ISBN-13 checksums are validated and formatting is normalized.
- Book, copy, barcode, category, and shelf identifiers are normalized and protected by case-insensitive database constraints.
- Generated book and copy codes are collision resistant.
- Book codes become immutable after physical copies are registered.
- Registered copies cannot move to another title.
- A selected location must belong to the selected shelf; selecting only a location automatically supplies its shelf.
- Category trees reject self-parenting and ancestor cycles.
- Catalog forms cannot directly change borrowed, lost, damaged, or repair statuses.
- Book status is synchronized automatically whenever a copy is saved or deleted.
- Referenced records cannot be deleted from the custom UI; staff are directed to deactivate classifications instead.
- Image uploads use validated image fields, extensions, and project upload-size limits.
- QR SVGs are generated live from normalized copy barcodes using ReportLab.
- REST serializers apply the same model validation and expose operational status as read-only.
- Imports normalize ISBNs and perform case-insensitive author and publisher matching.

## Main URLs

```text
/catalog/                         Advanced book search and title inventory
/catalog/books/<id>/              Book details and physical copies
/catalog/books/create/            Add a bibliographic record
/catalog/copies/                  Physical inventory
/catalog/copies/create/           Register a copy
/catalog/copies/<id>/qr/          Scannable QR SVG
/catalog/authors/                 Author management
/catalog/publishers/              Publisher management
/catalog/categories/              Category hierarchy
/catalog/shelves/                 Shelf management
/catalog/locations/               Location management
```

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.catalog
python manage.py test
```

The catalog suite contains 20 focused tests. The complete project suite contains 57 passing tests after this phase.
