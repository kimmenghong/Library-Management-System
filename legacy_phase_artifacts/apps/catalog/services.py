from reportlab.graphics import renderSVG
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing


def generate_qr_svg(payload, size=180):
    """Generate a scannable SVG using the project's existing ReportLab dependency."""
    widget = QrCodeWidget(payload)
    x1, y1, x2, y2 = widget.getBounds()
    width = x2 - x1
    height = y2 - y1
    scale = min(size / width, size / height)
    drawing = Drawing(
        size,
        size,
        transform=[scale, 0, 0, scale, -x1 * scale, -y1 * scale],
    )
    drawing.add(widget)
    return renderSVG.drawToString(drawing)
