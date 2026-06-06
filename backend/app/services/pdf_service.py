"""
PDF generation service using ReportLab.

Generates professional invoice PDFs with:
  - Company header with branding
  - Invoice number, date, and due details
  - Bill To section (vendor details)
  - Line items table with proper formatting
  - Subtotal, tax, and grand total
  - Payment terms and notes
  - Company footer with GSTIN
"""

import io
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_invoice_pdf(
    invoice_number: str,
    invoice_date: datetime,
    vendor_name: str,
    vendor_email: str,
    vendor_address: str | None,
    vendor_gst: str | None,
    line_items: list[dict],
    subtotal: Decimal,
    tax_rate: Decimal,
    tax_amount: Decimal,
    total_amount: Decimal,
    notes: str | None = None,
    po_number: str | None = None,
) -> bytes:
    """
    Generate a professional invoice PDF.

    Args:
        invoice_number: Invoice number (INV-YYYY-XXXX)
        invoice_date: Invoice creation date
        vendor_name: Vendor company name
        vendor_email: Vendor email
        vendor_address: Vendor address
        vendor_gst: Vendor GST number
        line_items: List of dicts with product_name, quantity, unit, unit_price, total_price
        subtotal: Subtotal amount
        tax_rate: Tax percentage
        tax_amount: Tax amount
        total_amount: Grand total
        notes: Payment terms or notes
        po_number: Related PO number

    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # Custom styles
    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "InvoiceSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#6b7280"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=12,
        spaceAfter=6,
    )
    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        leading=14,
    )
    bold_style = ParagraphStyle(
        "BoldText",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#111827"),
        fontName="Helvetica-Bold",
    )

    # ── Company Header ────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph(settings.COMPANY_NAME, title_style),
            Paragraph(f"<b>INVOICE</b><br/>{invoice_number}", ParagraphStyle(
                "InvNum", parent=styles["Normal"], fontSize=14, alignment=2,
                textColor=colors.HexColor("#1e40af"),
            )),
        ],
        [
            Paragraph(
                f"{settings.COMPANY_ADDRESS}<br/>"
                f"Phone: {settings.COMPANY_PHONE}<br/>"
                f"Email: {settings.COMPANY_EMAIL}<br/>"
                f"GSTIN: {settings.COMPANY_GSTIN}",
                subtitle_style,
            ),
            Paragraph(
                f"<b>Date:</b> {invoice_date.strftime('%d %B %Y')}<br/>"
                f"<b>PO Ref:</b> {po_number or 'N/A'}",
                ParagraphStyle("InvDetails", parent=styles["Normal"], fontSize=10, alignment=2),
            ),
        ],
    ]
    header_table = Table(header_data, colWidths=[340, 180])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8 * mm))

    # ── Horizontal line ───────────────────────────────────────────────────────
    line_table = Table([[""]],  colWidths=[520])
    line_table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Bill To Section ───────────────────────────────────────────────────────
    elements.append(Paragraph("BILL TO", heading_style))
    bill_to_text = f"<b>{vendor_name}</b><br/>"
    if vendor_address:
        bill_to_text += f"{vendor_address}<br/>"
    bill_to_text += f"Email: {vendor_email}<br/>"
    if vendor_gst:
        bill_to_text += f"GSTIN: {vendor_gst}"
    elements.append(Paragraph(bill_to_text, normal_style))
    elements.append(Spacer(1, 8 * mm))

    # ── Line Items Table ──────────────────────────────────────────────────────
    elements.append(Paragraph("ITEMS", heading_style))

    # Table header
    table_data = [["#", "Product / Service", "Qty", "Unit", "Unit Price", "Total"]]

    for idx, item in enumerate(line_items, 1):
        table_data.append([
            str(idx),
            str(item["product_name"]),
            str(item["quantity"]),
            str(item["unit"]),
            f"Rs. {item['unit_price']:,.2f}",
            f"Rs. {item['total_price']:,.2f}",
        ])

    item_table = Table(
        table_data,
        colWidths=[25, 200, 45, 45, 90, 100],
        repeatRows=1,
    )
    item_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Body
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        # Alternating rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        # Grid
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Totals Section ────────────────────────────────────────────────────────
    totals_data = [
        ["", "", "Subtotal:", f"Rs. {subtotal:,.2f}"],
        ["", "", f"GST ({tax_rate}%):", f"Rs. {tax_amount:,.2f}"],
        ["", "", "GRAND TOTAL:", f"Rs. {total_amount:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[200, 100, 110, 100])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (2, -1), (-1, -1), 12),
        ("TEXTCOLOR", (2, -1), (-1, -1), colors.HexColor("#1e40af")),
        ("LINEABOVE", (2, -1), (-1, -1), 1, colors.HexColor("#1e40af")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 10 * mm))

    # ── Notes / Payment Terms ─────────────────────────────────────────────────
    if notes:
        elements.append(Paragraph("NOTES / PAYMENT TERMS", heading_style))
        elements.append(Paragraph(notes, normal_style))
        elements.append(Spacer(1, 8 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_line = Table([[""]],  colWidths=[520])
    footer_line.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(footer_line)
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(
        f"This is a computer-generated invoice from {settings.COMPANY_NAME}. "
        f"For queries, contact {settings.COMPANY_EMAIL}.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#9ca3af")),
    ))

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info("PDF generated: invoice=%s size=%d bytes", invoice_number, len(pdf_bytes))
    return pdf_bytes


def save_invoice_pdf(invoice_number: str, pdf_bytes: bytes) -> str:
    """
    Save generated PDF to disk.

    Returns the file path relative to project root.
    """
    directory = os.path.join(settings.PDF_STORAGE_PATH, "invoices")
    os.makedirs(directory, exist_ok=True)

    filename = f"{invoice_number}.pdf"
    filepath = os.path.join(directory, filename)

    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

    logger.info("PDF saved: %s (%d bytes)", filepath, len(pdf_bytes))
    return filepath
