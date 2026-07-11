from __future__ import annotations

from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "docs" / "final_report_11_table_library_management_system.docx"

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def xml_escape(value: object) -> str:
    return escape(str(value), {'"': "&quot;"})


def run(
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    color: str | None = None,
    size: int | None = None,
) -> str:
    props: list[str] = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{size * 2}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    pieces: list[str] = []
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if index:
            pieces.append("<w:br/>")
        pieces.append(f'<w:t xml:space="preserve">{xml_escape(line)}</w:t>')
    return f"<w:r>{rpr}{''.join(pieces)}</w:r>"


def paragraph(
    text: str = "",
    *,
    style: str | None = None,
    align: str | None = None,
    bold: bool = False,
    italic: bool = False,
    color: str | None = None,
    size: int | None = None,
    before: int | None = None,
    after: int | None = None,
    page_break_before: bool = False,
    keep_next: bool = False,
    num_id: int | None = None,
    ilvl: int = 0,
) -> str:
    props: list[str] = []
    if style:
        props.append(f'<w:pStyle w:val="{style}"/>')
    if page_break_before:
        props.append("<w:pageBreakBefore/>")
    if keep_next:
        props.append("<w:keepNext/>")
    if num_id is not None:
        props.append(
            "<w:numPr>"
            f'<w:ilvl w:val="{ilvl}"/>'
            f'<w:numId w:val="{num_id}"/>'
            "</w:numPr>"
        )
    spacing_values: list[str] = []
    if before is not None:
        spacing_values.append(f'w:before="{before}"')
    if after is not None:
        spacing_values.append(f'w:after="{after}"')
    if spacing_values:
        props.append(f"<w:spacing {' '.join(spacing_values)}/>")
    if align:
        props.append(f'<w:jc w:val="{align}"/>')
    ppr = f"<w:pPr>{''.join(props)}</w:pPr>" if props else ""
    return f"<w:p>{ppr}{run(text, bold=bold, italic=italic, color=color, size=size)}</w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def heading(text: str, level: int = 1) -> str:
    return paragraph(text, style=f"Heading{level}", keep_next=True)


def numbered(text: str) -> str:
    return paragraph(text, num_id=1, after=80)


def cell(content: str | list[str], width: int, *, header: bool = False, align: str | None = None) -> str:
    fill = '<w:shd w:fill="F2F4F7"/>' if header else ""
    paragraphs = content if isinstance(content, list) else [content]
    inner = []
    for item in paragraphs:
        inner.append(
            paragraph(
                item,
                style="TableHeader" if header else "TableText",
                bold=header,
                align=align,
                after=0,
            )
        )
    return (
        "<w:tc>"
        "<w:tcPr>"
        f'<w:tcW w:w="{width}" w:type="dxa"/>'
        "<w:vAlign w:val=\"center\"/>"
        f"{fill}"
        "</w:tcPr>"
        f"{''.join(inner)}"
        "</w:tc>"
    )


def table(headers: list[str], rows: list[list[str | list[str]]], widths: list[int]) -> str:
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    header_row = "<w:tr>" + "".join(
        cell(value, widths[index], header=True) for index, value in enumerate(headers)
    ) + "</w:tr>"
    body_rows = []
    for row in rows:
        body_rows.append(
            "<w:tr>"
            + "".join(cell(value, widths[index]) for index, value in enumerate(row))
            + "</w:tr>"
        )
    return (
        "<w:tbl>"
        "<w:tblPr>"
        '<w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblInd w:w="120" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        "<w:tblBorders>"
        '<w:top w:val="single" w:sz="4" w:color="D9DEE7"/>'
        '<w:left w:val="single" w:sz="4" w:color="D9DEE7"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="D9DEE7"/>'
        '<w:right w:val="single" w:sz="4" w:color="D9DEE7"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="D9DEE7"/>'
        '<w:insideV w:val="single" w:sz="4" w:color="D9DEE7"/>'
        "</w:tblBorders>"
        "<w:tblCellMar>"
        '<w:top w:w="80" w:type="dxa"/>'
        '<w:left w:w="120" w:type="dxa"/>'
        '<w:bottom w:w="80" w:type="dxa"/>'
        '<w:right w:w="120" w:type="dxa"/>'
        "</w:tblCellMar>"
        "</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        f"{header_row}{''.join(body_rows)}"
        "</w:tbl>"
    )


def info_table(rows: list[tuple[str, str]]) -> str:
    return table(
        ["Item", "Details"],
        [[label, value] for label, value in rows],
        [2300, 7060],
    )


def document_body() -> str:
    today = date(2026, 7, 9).strftime("%B %d, %Y")
    parts: list[str] = []

    parts.extend(
        [
            paragraph("Final Project Report", align="center", color="2E74B5", bold=True, size=16, before=1600, after=120),
            paragraph("Library Management System", align="center", bold=True, size=28, after=160),
            paragraph("Corrected 11-Table Django Implementation", align="center", italic=True, size=14, color="555555", after=420),
            info_table(
                [
                    ("Project Type", "University Final Project"),
                    ("Technology Stack", "Python Django, SQLite, HTML, CSS, Bootstrap 5"),
                    ("Database Scope", "Lecturer Data Dictionary with 11 required application tables"),
                    ("Submission Date", today),
                    ("Submitted By", "Student Name: ________________________________"),
                    ("Student ID", "________________________________"),
                    ("Lecturer", "________________________________"),
                    ("Department", "________________________________"),
                ]
            ),
            paragraph(
                "This report presents the corrected Library Management System based on the required 11-table Data Dictionary. "
                "The system focuses on the essential academic library workflow: managing users, roles, books, members, borrowing, fines, notifications, and reports.",
                align="center",
                italic=True,
                color="555555",
                before=360,
                after=0,
            ),
            page_break(),
        ]
    )

    parts.append(heading("Acknowledgement", 1))
    parts.append(
        paragraph(
            "First, I would like to express my sincere gratitude to my lecturer for providing guidance, feedback, and the required Data Dictionary for this project. "
            "The lecturer's instructions helped me improve the database design and correct the system structure so that it follows the required academic standard."
        )
    )
    parts.append(
        paragraph(
            "I would also like to thank my classmates, friends, and family for their encouragement during the development and documentation of this Library Management System. "
            "Their support helped me complete the project more confidently."
        )
    )
    parts.append(
        paragraph(
            "Finally, I am thankful for the opportunity to apply Django, database design, authentication, validation, testing, and documentation skills in a practical final project."
        )
    )

    parts.append(heading("Abstract", 1))
    parts.append(
        paragraph(
            "The Library Management System is a web-based application developed using Python Django. "
            "It is designed to help a university library manage important daily operations such as user management, book catalog management, member registration, book borrowing, book returning, fine calculation, notification history, and report generation."
        )
    )
    parts.append(
        paragraph(
            "The corrected version of the project follows the lecturer's Data Dictionary exactly by using 11 required application tables: roles, users, categories, authors, publishers, books, members, borrow_records, fines, notifications, and reports. "
            "The system uses proper primary keys, foreign keys, validation rules, and workflow logic to keep records accurate and consistent."
        )
    )
    parts.append(
        paragraph(
            "The project includes a custom user model, role-based access support, book stock control, direct book borrowing records, automatic stock updates, late return fine calculation, member notifications, report history, sample data, and automated tests. "
            "The final result is a simple but professional library system suitable for university final project submission."
        )
    )

    parts.append(heading("Project Objectives", 1))
    for item in [
        "To develop a professional Django-based Library Management System for university library operations.",
        "To store and manage book, author, publisher, category, user, role, and member information accurately.",
        "To manage the borrowing and returning process using a clear transaction record.",
        "To connect each borrow record directly to a member, a book, the issuing user, and the receiving user.",
        "To calculate fines automatically when books are returned after the due date.",
        "To store notification history for library members.",
        "To generate report records for library administration.",
        "To follow the lecturer's 11-table Data Dictionary exactly.",
        "To test the system using Django automated tests.",
        "To reduce manual record keeping and improve data consistency.",
    ]:
        parts.append(numbered(item))

    parts.append(heading("Scope Of The System", 1))
    parts.append(
        paragraph(
            "The system scope is limited to the lecturer's corrected 11-table Data Dictionary. "
            "It does not use prohibited extra application tables such as BookCopy, reservations, digital books, repair records, or audit tables in the active corrected schema."
        )
    )
    parts.append(heading("Included Scope", 2))
    for item in [
        "User login and logout.",
        "Role and user management.",
        "Category, author, publisher, and book management.",
        "Library member management.",
        "Book borrowing and returning.",
        "Book availability update during issue and return.",
        "Late return fine calculation and payment tracking.",
        "Member notification history.",
        "Report generation history.",
        "Sample data and automated testing.",
    ]:
        parts.append(numbered(item))

    parts.append(heading("Excluded Scope", 2))
    for item in [
        "The corrected submission does not use BookCopy for borrow records.",
        "The corrected submission does not use extra domain tables outside the 11 required tables.",
        "Advanced production features such as barcode printing, email sending, PDF export, and backup scheduling are listed as future improvements.",
    ]:
        parts.append(numbered(item))

    parts.append(heading("System Modules", 1))
    parts.append(
        table(
            ["Module", "Purpose"],
            [
                ["Authentication Module", "Allows users to log in and log out using Django authentication with the custom users table."],
                ["Role And User Management", "Manages roles and user accounts, including active status, staff status, and user profile details."],
                ["Book Master Data", "Manages categories, authors, publishers, and books."],
                ["Member Management", "Stores library member information and connects each member to a user account."],
                ["Borrowing Module", "Records book issue transactions and links members, books, and issuing users."],
                ["Returning Module", "Records return date and receiving user, updates stock, and validates return details."],
                ["Fine Management", "Calculates and stores fines for late returns and tracks paid amount."],
                ["Notification Module", "Stores due date, overdue, fine, and general notifications for members."],
                ["Report Module", "Generates report records and stores the user who generated each report."],
                ["Dashboard Module", "Displays key statistics such as total books, members, borrowed books, overdue records, fines, and reports."],
                ["Testing And Sample Data", "Provides seed data and automated tests for all required tables and workflows."],
            ],
            [2500, 6860],
        )
    )

    parts.append(heading("Data Dictionary With 11 Tables", 1))
    parts.append(
        paragraph(
            "The following table summarizes the corrected Data Dictionary. "
            "All application table names are controlled using Django model Meta db_table, and all primary keys match the lecturer's required names."
        )
    )
    parts.append(
        table(
            ["Table", "Primary Key", "Important Fields", "Relationships"],
            [
                ["roles", "role_id", "role_name, description", "One role has many users."],
                ["users", "user_id", "role_id, username, email, full_name, phone, address, is_active, is_staff, is_superuser, created_at, updated_at", "role_id references roles.role_id."],
                ["categories", "category_id", "category_name, description", "One category has many books."],
                ["authors", "author_id", "author_name, biography", "One author has many books."],
                ["publishers", "publisher_id", "publisher_name, address, contact_number, email", "One publisher has many books."],
                ["books", "book_id", "category_id, author_id, publisher_id, isbn, title, edition, publication_year, quantity, available_quantity, shelf_location, status, created_at, updated_at", "category_id, author_id, and publisher_id reference their master tables."],
                ["members", "member_id", "user_id, member_code, member_type, department, phone, address, registration_date, status", "user_id references users.user_id."],
                ["borrow_records", "borrow_id", "member_id, book_id, issued_by, received_by, borrow_date, due_date, return_date, status", "member_id references members.member_id. book_id references books.book_id. issued_by and received_by reference users.user_id."],
                ["fines", "fine_id", "borrow_id, member_id, amount, paid_amount, status, created_at, paid_date", "borrow_id references borrow_records.borrow_id. member_id references members.member_id."],
                ["notifications", "notification_id", "member_id, title, message, notification_type, is_read, created_at", "member_id references members.member_id."],
                ["reports", "report_id", "report_type, generated_by, generated_at, file_path", "generated_by references users.user_id."],
            ],
            [1450, 1300, 4250, 2360],
        )
    )

    parts.append(heading("Data Dictionary Verification", 2))
    for item in [
        "BorrowRecord uses book_id foreign key to books, not BookCopy.",
        "BorrowRecord includes issued_by and received_by foreign keys to users.",
        "Notification uses member_id foreign key to members, not users.",
        "Report is included and uses generated_by foreign key to users.",
        "All required primary key names match the lecturer's Data Dictionary.",
        "All required table names match exactly using db_table.",
    ]:
        parts.append(numbered(item))

    parts.append(heading("ERD Explanation", 1))
    parts.append(
        paragraph(
            "The Entity Relationship Diagram is centered on the borrowing transaction. "
            "A user belongs to one role. A member is connected to one user account. A book belongs to one category, one author, and one publisher. "
            "When a book is borrowed, a borrow_records row connects the member, the selected book, and the user who issued the book."
        )
    )
    parts.append(
        paragraph(
            "When the book is returned, the same borrow_records row stores the return date and the user who received the book. "
            "If the return is late, the system creates a fine connected to both the borrow record and the member. "
            "Notifications are connected to members so that each member has a clear notification history. "
            "Reports are connected to the user who generated them, which supports accountability."
        )
    )
    parts.append(
        table(
            ["Relationship", "Cardinality", "Explanation"],
            [
                ["roles to users", "One-to-many", "One role can be assigned to many users."],
                ["users to members", "One-to-one", "Each member profile is linked to one user account."],
                ["categories to books", "One-to-many", "One category can contain many books."],
                ["authors to books", "One-to-many", "One author can be related to many books."],
                ["publishers to books", "One-to-many", "One publisher can publish many books."],
                ["members to borrow_records", "One-to-many", "One member can have many borrowing records."],
                ["books to borrow_records", "One-to-many", "One book title can appear in many borrowing records over time."],
                ["users to borrow_records", "One-to-many", "Users can issue and receive many borrow transactions."],
                ["borrow_records to fines", "One-to-many", "One borrowing record can have fine records when applicable."],
                ["members to notifications", "One-to-many", "One member can receive many notifications."],
                ["users to reports", "One-to-many", "One user can generate many reports."],
            ],
            [2600, 1800, 4960],
        )
    )

    parts.append(heading("System Workflow", 1))
    parts.append(heading("Login Workflow", 2))
    for item in [
        "The user opens the login page.",
        "The user enters username and password.",
        "Django authenticates the account using the custom users table.",
        "If the login is successful, the user is redirected to the dashboard.",
        "If the login fails, the system displays an error message.",
    ]:
        parts.append(numbered(item))

    parts.append(heading("Borrow Book Workflow", 2))
    for item in [
        "The librarian selects a member and an available book.",
        "The system validates that the book has available quantity.",
        "The system creates a borrow_records row with member_id, book_id, issued_by, borrow_date, and due_date.",
        "The system decreases the book's available_quantity.",
        "If no copies are available, the book status becomes borrowed.",
    ]:
        parts.append(numbered(item))

    parts.append(heading("Return Book Workflow", 2))
    for item in [
        "The librarian opens the borrow record and enters the return date.",
        "The system records received_by as the logged-in librarian.",
        "The system updates return_date and changes the borrow record status to returned.",
        "The system increases the book's available_quantity.",
        "If the return date is later than the due date, the system calculates a fine.",
        "The system creates a notification for the member when a fine is generated.",
    ]:
        parts.append(numbered(item))

    parts.append(heading("Fine Calculation Workflow", 2))
    parts.append(
        paragraph(
            "The fine is calculated by counting the number of late days after the due date. "
            "In the implemented system, the fine rate is 1.00 per late day. "
            "For example, if a book is returned 5 days late, the fine amount is 5.00."
        )
    )

    parts.append(heading("Screenshots Explanation Section", 1))
    parts.append(
        paragraph(
            "The following screenshots should be inserted into the final printed report or presentation. "
            "Each screenshot demonstrates an important part of the completed system."
        )
    )
    parts.append(
        table(
            ["Screenshot", "Explanation"],
            [
                ["Login Page", "Shows the user authentication screen where users enter username and password."],
                ["Dashboard", "Shows system statistics such as books, members, borrowed records, fines, and reports."],
                ["Roles And Users", "Shows how library staff can manage roles and user accounts."],
                ["Book List", "Shows book catalog data with title, ISBN, author, publisher, category, quantity, availability, and status."],
                ["Member List", "Shows registered library members and their member type."],
                ["Borrow Book Form", "Shows the process of selecting a member, selecting a book, and setting borrow and due dates."],
                ["Borrow Records", "Shows issued books, due dates, return dates, issued_by users, and received_by users."],
                ["Return Book Form", "Shows how the librarian records a returned book."],
                ["Fine List", "Shows fines created from late returns and payment status."],
                ["Notification List", "Shows member notification history."],
                ["Report List", "Shows generated reports and the user who generated each report."],
                ["Test Result", "Shows the terminal result after running python3 manage.py test."],
            ],
            [2500, 6860],
        )
    )

    parts.append(heading("Testing Result", 1))
    parts.append(
        paragraph(
            "The system was tested using Django's automated test framework. "
            "The tests verify the corrected Data Dictionary schema, table names, primary keys, foreign keys, borrowing workflow, returning workflow, fine calculation, notification creation, report generation, and repeatable sample data insertion."
        )
    )
    parts.append(
        table(
            ["Test Item", "Result"],
            [
                ["Django system check", "Passed: System check identified no issues."],
                ["Migration check", "Passed: No changes detected."],
                ["Automated test command", "python3 manage.py test"],
                ["Test suite result", "Passed: Ran 12 tests successfully."],
                ["Borrow book test", "Passed: book availability decreases after issue."],
                ["Return book test", "Passed: return date, received_by, status, and stock update correctly."],
                ["Fine calculation test", "Passed: late return creates correct fine amount."],
                ["Notification test", "Passed: notifications connect to members."],
                ["Report generation test", "Passed: reports connect to generated_by user."],
                ["Seed data test", "Passed: valid rows are created for all 11 required tables."],
            ],
            [3000, 6360],
        )
    )

    parts.append(heading("Problems And Solutions", 1))
    parts.append(
        table(
            ["Problem", "Solution"],
            [
                ["The earlier project design contained too many application tables.", "The system was corrected to use only the lecturer's 11 required Data Dictionary tables in the active apps.library implementation."],
                ["Borrow records previously used BookCopy.", "BorrowRecord was changed to use book_id foreign key directly to books."],
                ["Borrow records needed staff accountability.", "issued_by and received_by foreign keys were added to connect borrow actions to users."],
                ["Notifications were connected to users instead of members.", "Notification was corrected to use member_id foreign key to members."],
                ["The Report table was missing from the corrected schema.", "A reports table was created with report_id primary key and generated_by foreign key to users."],
                ["Data consistency needed validation.", "Model clean methods and database constraints were added for quantities, dates, and fine amounts."],
                ["The system needed reliable demo data.", "A repeatable seed_data management command was created."],
                ["The project needed proof of correctness.", "Automated tests were added for all 11 tables and major workflows."],
            ],
            [3600, 5760],
        )
    )

    parts.append(heading("Conclusion", 1))
    parts.append(
        paragraph(
            "The corrected Library Management System successfully implements the required 11-table Data Dictionary for a university final project. "
            "The system provides the main functions needed by a library, including user and role management, book management, member management, borrowing, returning, fine calculation, notifications, and reports."
        )
    )
    parts.append(
        paragraph(
            "The project demonstrates practical Django development skills, including custom models, foreign key relationships, forms, views, templates, admin configuration, validation, management commands, and automated testing. "
            "Most importantly, the final database design follows the lecturer's required schema exactly for the application tables."
        )
    )
    parts.append(
        paragraph(
            "Overall, the system reduces manual library work, improves record accuracy, and provides a clear foundation for future improvements."
        )
    )

    parts.append(heading("Future Improvements", 1))
    for item in [
        "Add barcode and QR code generation for book labels.",
        "Add email reminders for due dates and overdue books.",
        "Add PDF and Excel export for reports.",
        "Add advanced charts for dashboard analytics.",
        "Add member self-service pages for borrowing history and notifications.",
        "Add PostgreSQL deployment configuration for production use.",
        "Add backup and restore tools.",
        "Add audit trail logging for important actions.",
        "Add advanced search by ISBN, title, author, publisher, category, status, and shelf location.",
        "Add responsive UI improvements for mobile users.",
    ]:
        parts.append(numbered(item))

    sect_pr = (
        "<w:sectPr>"
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
        "</w:sectPr>"
    )
    parts.append(sect_pr)
    return "".join(parts)


def content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def document_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>"""


def styles_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{NS_W}">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="320" w:after="160"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="2E74B5"/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="2E74B5"/><w:sz w:val="26"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="160" w:after="80"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="1F4D78"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="TableText">
    <w:name w:val="Table Text"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="0" w:line="264" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="20"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="TableHeader">
    <w:name w:val="Table Header"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="0" w:line="264" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:sz w:val="20"/></w:rPr>
  </w:style>
</w:styles>"""


def numbering_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{NS_W}">
  <w:abstractNum w:abstractNumId="1">
    <w:multiLevelType w:val="singleLevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="decimal"/>
      <w:lvlText w:val="%1."/>
      <w:lvlJc w:val="left"/>
      <w:pPr>
        <w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs>
        <w:ind w:left="720" w:hanging="360"/>
        <w:spacing w:after="160" w:line="280" w:lineRule="auto"/>
      </w:pPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
</w:numbering>"""


def document_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{NS_W}" xmlns:r="{NS_R}">
  <w:body>{document_body()}</w:body>
</w:document>"""


def core_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:dcmitype="http://purl.org/dc/dcmitype/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Library Management System Final Report</dc:title>
  <dc:subject>Corrected 11-table Django implementation</dc:subject>
  <dc:creator>Library Management System Project</dc:creator>
  <cp:keywords>Django; Library Management System; Data Dictionary</cp:keywords>
  <dc:description>University final project report for the corrected 11-table Library Management System.</dc:description>
</cp:coreProperties>"""


def app_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
  xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <Company>University Final Project</Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>1.0</AppVersion>
</Properties>"""


def build_docx() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT_PATH, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml())
        archive.writestr("_rels/.rels", rels_xml())
        archive.writestr("word/document.xml", document_xml())
        archive.writestr("word/_rels/document.xml.rels", document_rels_xml())
        archive.writestr("word/styles.xml", styles_xml())
        archive.writestr("word/numbering.xml", numbering_xml())
        archive.writestr("docProps/core.xml", core_xml())
        archive.writestr("docProps/app.xml", app_xml())


if __name__ == "__main__":
    build_docx()
    print(OUTPUT_PATH)
