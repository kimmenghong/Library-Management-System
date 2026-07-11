from datetime import timedelta
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone

from apps.catalog.models import Book, BookCopy, Category
from apps.circulation.models import BorrowRecord
from apps.circulation.services import mark_overdue_records
from apps.fines.models import Fine
from apps.members.models import Member
from apps.status_tracking.models import DamagedBook, LostBook, RepairRecord


REPORT_TITLES = {
    "most-borrowed": "Most Borrowed Books",
    "active-borrowers": "Active Borrowers",
    "members-with-fines": "Members with Fines",
    "status": "Lost, Damaged, and Repair Report",
}


def dashboard_metrics():
    mark_overdue_records()
    return {
        "total_books": Book.objects.count(),
        "total_members": Member.objects.count(),
        "available_books": BookCopy.objects.filter(status=BookCopy.AVAILABLE).count(),
        "borrowed_books": BookCopy.objects.filter(status=BookCopy.BORROWED).count(),
        "overdue_books": BorrowRecord.objects.filter(status=BorrowRecord.OVERDUE).count(),
        "lost_books": BookCopy.objects.filter(status=BookCopy.LOST).count(),
        "damaged_books": BookCopy.objects.filter(status=BookCopy.DAMAGED).count(),
        "under_repair": BookCopy.objects.filter(status=BookCopy.UNDER_REPAIR).count(),
        "unpaid_fines": Fine.objects.exclude(status__in=[Fine.PAID, Fine.WAIVED]).count(),
    }


def chart_payload():
    today = timezone.localdate()
    start_date = today - timedelta(days=180)
    monthly = (
        BorrowRecord.objects.filter(borrow_date__gte=start_date)
        .annotate(month=TruncMonth("borrow_date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    status_counts = BookCopy.objects.values("status").annotate(total=Count("id")).order_by("status")
    category_counts = (
        Category.objects.annotate(total=Count("books"))
        .filter(total__gt=0)
        .order_by("-total")[:8]
    )
    return {
        "monthly_borrow_labels": [item["month"].strftime("%b %Y") for item in monthly],
        "monthly_borrow_values": [item["total"] for item in monthly],
        "copy_status_labels": [item["status"].replace("_", " ").title() for item in status_counts],
        "copy_status_values": [item["total"] for item in status_counts],
        "category_labels": [item.name for item in category_counts],
        "category_values": [item.total for item in category_counts],
    }


def most_borrowed_books(limit=20):
    return list(
        Book.objects.annotate(
            borrow_count=Count("copies__borrow_records"),
            active_borrows=Count(
                "copies__borrow_records",
                filter=Q(copies__borrow_records__status__in=[BorrowRecord.BORROWED, BorrowRecord.OVERDUE]),
            ),
        )
        .filter(borrow_count__gt=0)
        .order_by("-borrow_count", "title")[:limit]
    )


def active_borrowers(limit=20):
    return list(
        Member.objects.select_related("user")
        .annotate(
            active_borrow_count=Count(
                "borrow_records",
                filter=Q(borrow_records__status__in=[BorrowRecord.BORROWED, BorrowRecord.OVERDUE]),
            ),
            total_borrow_count=Count("borrow_records"),
        )
        .filter(active_borrow_count__gt=0)
        .order_by("-active_borrow_count", "member_code")[:limit]
    )


def members_with_fines(limit=50):
    members = list(
        Member.objects.select_related("user")
        .annotate(
            fine_count=Count("fines", filter=~Q(fines__status__in=[Fine.PAID, Fine.WAIVED])),
            total_fines=Sum("fines__amount", filter=~Q(fines__status__in=[Fine.PAID, Fine.WAIVED])),
            total_paid=Sum("fines__paid_amount", filter=~Q(fines__status__in=[Fine.PAID, Fine.WAIVED])),
        )
        .filter(fine_count__gt=0)
        .order_by("-total_fines", "member_code")[:limit]
    )
    for member in members:
        member.fine_balance = (member.total_fines or 0) - (member.total_paid or 0)
    return members


def status_report():
    return {
        "lost_books": list(LostBook.objects.select_related("book_copy__book", "member__user").order_by("status", "-reported_date")),
        "damaged_books": list(DamagedBook.objects.select_related("book_copy__book", "member__user").order_by("status", "-reported_date")),
        "repairs": list(RepairRecord.objects.select_related("book_copy__book", "damage_record").order_by("status", "-sent_date")),
    }


def report_rows(report_type):
    if report_type == "most-borrowed":
        headers = ["Book Code", "Title", "ISBN", "Total Borrows", "Active Borrows"]
        rows = [
            [book.book_code, book.title, book.isbn or "-", book.borrow_count, book.active_borrows]
            for book in most_borrowed_books(limit=100)
        ]
    elif report_type == "active-borrowers":
        headers = ["Member Code", "Name", "Type", "Active Borrows", "Total Borrows"]
        rows = [
            [member.member_code, member.display_name, member.get_member_type_display(), member.active_borrow_count, member.total_borrow_count]
            for member in active_borrowers(limit=100)
        ]
    elif report_type == "members-with-fines":
        headers = ["Member Code", "Name", "Fine Count", "Total Fines", "Paid", "Balance"]
        rows = []
        for member in members_with_fines(limit=200):
            total_fines = member.total_fines or 0
            total_paid = member.total_paid or 0
            rows.append([member.member_code, member.display_name, member.fine_count, total_fines, total_paid, member.fine_balance])
    elif report_type == "status":
        headers = ["Type", "Book Copy", "Title", "Member", "Status", "Date", "Cost"]
        data = status_report()
        rows = []
        for item in data["lost_books"]:
            rows.append(["Lost", item.book_copy.copy_code, item.book_copy.book.title, item.member.display_name if item.member else "-", item.get_status_display(), item.reported_date, item.replacement_cost])
        for item in data["damaged_books"]:
            rows.append(["Damaged", item.book_copy.copy_code, item.book_copy.book.title, item.member.display_name if item.member else "-", item.get_status_display(), item.reported_date, item.estimated_repair_cost])
        for item in data["repairs"]:
            rows.append(["Repair", item.book_copy.copy_code, item.book_copy.book.title, "-", item.get_status_display(), item.sent_date, item.repair_cost])
    else:
        raise ValueError("Unknown report type.")
    return headers, rows


def export_excel(report_type):
    headers, rows = report_rows(report_type)
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ModuleNotFoundError:
        return export_basic_xlsx(report_type, headers, rows)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = REPORT_TITLES[report_type][:31]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append(row)
    for column_cells in sheet.columns:
        length = max(len(str(cell.value or "")) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(length + 4, 40)
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{report_type}.xlsx"'
    return response


def export_pdf(report_type):
    headers, rows = report_rows(report_type)
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ModuleNotFoundError:
        return export_basic_pdf(report_type, headers, rows)

    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=landscape(letter), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elements = [Paragraph(REPORT_TITLES[report_type], styles["Title"]), Spacer(1, 12)]
    table_data = [headers] + [[str(value) for value in row] for row in rows]
    if len(table_data) == 1:
        table_data.append(["No records found."] + [""] * (len(headers) - 1))
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    elements.append(table)
    document.build(elements)
    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{report_type}.pdf"'
    return response


def export_basic_xlsx(report_type, headers, rows):
    def xml_escape(value):
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def cell_name(row_index, column_index):
        name = ""
        while column_index:
            column_index, remainder = divmod(column_index - 1, 26)
            name = chr(65 + remainder) + name
        return f"{name}{row_index}"

    sheet_rows = [headers] + rows
    row_xml = []
    for row_index, row in enumerate(sheet_rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            cells.append(
                f'<c r="{cell_name(row_index, column_index)}" t="inlineStr">'
                f"<is><t>{xml_escape(value)}</t></is></c>"
            )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Report" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData>{''.join(row_xml)}</sheetData>
</worksheet>""",
        )
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{report_type}.xlsx"'
    return response


def export_basic_pdf(report_type, headers, rows):
    def pdf_escape(value):
        return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    title = REPORT_TITLES[report_type]
    text_rows = [" | ".join(headers)] + [" | ".join(str(value) for value in row) for row in rows]
    if not rows:
        text_rows.append("No records found.")
    pages = []
    lines_per_page = 32
    for start in range(0, len(text_rows), lines_per_page):
        page_lines = text_rows[start : start + lines_per_page]
        commands = ["BT /F1 16 Tf 40 570 Td (%s) Tj ET" % pdf_escape(title)]
        y = 540
        for line in page_lines:
            commands.append("BT /F1 8 Tf 40 %d Td (%s) Tj ET" % (y, pdf_escape(line[:170])))
            y -= 15
        pages.append("\\n".join(commands))

    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        None,
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_object_numbers = []
    for content in pages:
        page_number = len(objects) + 1
        content_number = len(objects) + 2
        page_object_numbers.append(page_number)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 792 612] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_number} 0 R >>")
        encoded = content.encode("utf-8")
        objects.append(f"<< /Length {len(encoded)} >>\\nstream\\n{content}\\nendstream")
    kids = " ".join(f"{number} 0 R" for number in page_object_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_numbers)} >>"

    output = BytesIO()
    output.write(b"%PDF-1.4\\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{index} 0 obj\\n{obj}\\nendobj\\n".encode("utf-8"))
    xref_start = output.tell()
    output.write(f"xref\\n0 {len(objects) + 1}\\n".encode("utf-8"))
    output.write(b"0000000000 65535 f \\n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \\n".encode("utf-8"))
    output.write(
        f"trailer\\n<< /Size {len(objects) + 1} /Root 1 0 R >>\\nstartxref\\n{xref_start}\\n%%EOF".encode("utf-8")
    )
    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{report_type}.pdf"'
    return response
