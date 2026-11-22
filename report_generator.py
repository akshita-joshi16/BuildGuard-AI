
"""Professional PDF safety report generation for BuildGuard AI."""

from io import BytesIO
from datetime import datetime
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
)


# ----------------------------------------------------------
# REPORT THEME
# ----------------------------------------------------------

FOREST_GREEN = colors.HexColor("#173B2E")
DARK_GREEN = colors.HexColor("#142D27")
ACCENT_GREEN = colors.HexColor("#246044")
SAFETY_LIME = colors.HexColor("#B8E36B")
IVORY = colors.HexColor("#F5F1E7")
LIGHT_GREEN = colors.HexColor("#EDF3ED")
BORDER_COLOR = colors.HexColor("#DDE5DD")
TEXT_COLOR = colors.HexColor("#263B32")
MUTED_TEXT = colors.HexColor("#68786F")


def _safe_text(value):
    """Escape text before inserting it into ReportLab Paragraphs."""
    return escape(str(value if value is not None else "-"))


def _format_confidence(value):
    """Format a model confidence value as a percentage."""
    try:
        number = float(value)
        if 0 <= number <= 1:
            number *= 100
        return f"{number:.1f}%"
    except (ValueError, TypeError):
        return "-"


def _format_timestamp(item):
    """Get a readable timestamp from a detection record."""
    value = item.get(
        "timestamp_label",
        item.get("frame_timestamp"),
    )

    if value is None:
        return "-"

    try:
        seconds = float(value)
        if seconds < 0:
            return str(value)

        minutes, remaining_seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

        return f"{minutes:02d}:{remaining_seconds:02d}"
    except (ValueError, TypeError):
        return str(value)


def _get_confidence_statistics(detections):
    """Calculate confidence statistics from valid prediction values."""
    values = []

    for item in detections:
        try:
            value = float(item.get("confidence", 0))
            if 0 <= value <= 1:
                values.append(value * 100)
            elif 1 < value <= 100:
                values.append(value)
        except (ValueError, TypeError):
            continue

    if not values:
        return None

    return {
        "average": sum(values) / len(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def _build_footer(canvas, doc):
    """Draw a consistent footer and page number on each page."""
    canvas.saveState()

    page_width, _ = A4

    canvas.setStrokeColor(BORDER_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(
        18 * mm,
        15 * mm,
        page_width - 18 * mm,
        15 * mm,
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED_TEXT)

    canvas.drawString(
        18 * mm,
        10 * mm,
        "BUILDGUARD AI | Construction Safety Monitoring",
    )

    canvas.drawRightString(
        page_width - 18 * mm,
        10 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ----------------------------------------------------------
# MAIN PDF GENERATOR
# ----------------------------------------------------------

def generate_pdf_report(
    detections,
    source_name="Uploaded file",
    source_type="Image",
    annotated_image=None,
    summary=None,
    timestamp=None,
):
    """
    Generate a professional downloadable BuildGuard AI PDF report.

    Args:
        detections: List of detection dictionaries.
        source_name: Uploaded image or video filename.
        source_type: Image or Video.
        annotated_image: Optional annotated RGB image as a NumPy array
                         or PIL image.
        summary: Optional dictionary containing category counts.
        timestamp: Optional report generation timestamp.

    Returns:
        PDF document as bytes.
    """

    detections = list(detections or [])
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title="BuildGuard AI Safety Report",
        author="BuildGuard AI",
        subject="Construction Site Safety Monitoring",
    )

    # ------------------------------------------------------
    # TEXT STYLES
    # ------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "BuildGuardTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=30,
        textColor=FOREST_GREEN,
        alignment=0,
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "BuildGuardSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=MUTED_TEXT,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "BuildGuardHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=ACCENT_GREEN,
        spaceBefore=13,
        spaceAfter=7,
        keepWithNext=True,
    )

    normal_style = ParagraphStyle(
        "BuildGuardBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR,
    )

    small_style = ParagraphStyle(
        "BuildGuardSmall",
        parent=normal_style,
        fontSize=8,
        leading=11,
    )

    cell_style = ParagraphStyle(
        "BuildGuardCell",
        parent=normal_style,
        fontSize=8,
        leading=10,
    )

    story = []

    report_time = timestamp or datetime.now().strftime(
        "%d %B %Y, %I:%M %p"
    )

    # ------------------------------------------------------
    # HEADER
    # ------------------------------------------------------

    story.append(Paragraph("BUILDGUARD AI", title_style))

    story.append(
        Paragraph(
            "CONSTRUCTION SITE SAFETY MONITORING REPORT",
            subtitle_style,
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=2,
            color=SAFETY_LIME,
        )
    )

    story.append(Spacer(1, 12))

    # ------------------------------------------------------
    # REPORT INFORMATION
    # ------------------------------------------------------

    story.append(
        Paragraph("01 | Report Information", heading_style)
    )

    info_data = [
        [
            Paragraph("<b>File Name</b>", cell_style),
            Paragraph(_safe_text(source_name), cell_style),
        ],
        [
            Paragraph("<b>Analysis Type</b>", cell_style),
            Paragraph(_safe_text(source_type), cell_style),
        ],
        [
            Paragraph("<b>Generated On</b>", cell_style),
            Paragraph(_safe_text(report_time), cell_style),
        ],
    ]

    info_table = Table(
        info_data,
        colWidths=[42 * mm, 125 * mm],
    )

    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREEN),
        ("BACKGROUND", (1, 0), (1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(info_table)

    # ------------------------------------------------------
    # EXECUTIVE SUMMARY
    # ------------------------------------------------------

    story.append(
        Paragraph("02 | Executive Summary", heading_style)
    )

    total_detections = len(detections)
    confidence_stats = _get_confidence_statistics(detections)

    average_confidence = (
        f"{confidence_stats['average']:.1f}%"
        if confidence_stats else "N/A"
    )

    summary_cards = [
        [
            Paragraph(
                f"<b>{total_detections}</b><br/>"
                "Detected Objects",
                cell_style,
            ),
            Paragraph(
                f"<b>{average_confidence}</b><br/>"
                "Average Confidence",
                cell_style,
            ),
        ]
    ]

    cards_table = Table(
        summary_cards,
        colWidths=[83.5 * mm, 83.5 * mm],
    )

    cards_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, -1), FOREST_GREEN),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 13),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
    ]))

    story.append(cards_table)

    # ------------------------------------------------------
    # CATEGORY BREAKDOWN
    # ------------------------------------------------------

    story.append(
        Paragraph("03 | PPE Detection Breakdown", heading_style)
    )

    if summary is None:
        counts = {}

        for item in detections:
            name = str(item.get("class_name", "Unknown"))
            counts[name] = counts.get(name, 0) + 1
    else:
        counts = summary

    if counts:
        summary_data = [[
            Paragraph("<b>Detected Category</b>", cell_style),
            Paragraph("<b>Prediction Count</b>", cell_style),
        ]]

        for name, count in counts.items():
            summary_data.append([
                Paragraph(_safe_text(name), cell_style),
                Paragraph(_safe_text(count), cell_style),
            ])

        summary_table = Table(
            summary_data,
            colWidths=[110 * mm, 57 * mm],
            repeatRows=1,
        )

        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), FOREST_GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                IVORY,
            ]),
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))

        story.append(summary_table)
    else:
        story.append(
            Paragraph(
                "No detection categories are available for this analysis.",
                normal_style,
            )
        )

    # ------------------------------------------------------
    # CONFIDENCE STATISTICS
    # ------------------------------------------------------

    if confidence_stats:
        story.append(
            Paragraph("04 | Model Confidence Statistics", heading_style)
        )

        confidence_data = [
            ["Average", "Minimum", "Maximum"],
            [
                f"{confidence_stats['average']:.1f}%",
                f"{confidence_stats['minimum']:.1f}%",
                f"{confidence_stats['maximum']:.1f}%",
            ],
        ]

        confidence_table = Table(
            confidence_data,
            colWidths=[55.7 * mm, 55.7 * mm, 55.7 * mm],
        )

        confidence_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT_GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GREEN),
            ("TEXTCOLOR", (0, 1), (-1, 1), FOREST_GREEN),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 9),
        ]))

        story.append(confidence_table)

    # ------------------------------------------------------
    # DETECTION DETAILS
    # ------------------------------------------------------

    story.append(
        Paragraph("05 | Individual Detection Details", heading_style)
    )

    if detections:
        detail_data = [[
            Paragraph("<b>Category</b>", cell_style),
            Paragraph("<b>Confidence</b>", cell_style),
            Paragraph("<b>Timestamp</b>", cell_style),
        ]]

        for item in detections:
            category = item.get("class_name", "Unknown")
            confidence = item.get("confidence", 0)
            timestamp_value = _format_timestamp(item)

            detail_data.append([
                Paragraph(_safe_text(category), cell_style),
                Paragraph(_format_confidence(confidence), cell_style),
                Paragraph(_safe_text(timestamp_value), cell_style),
            ])

        detail_table = Table(
            detail_data,
            colWidths=[70 * mm, 45 * mm, 52 * mm],
            repeatRows=1,
        )

        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), FOREST_GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                IVORY,
            ]),
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))

        story.append(detail_table)
    else:
        story.append(
            Paragraph(
                "No objects were detected in this analysis.",
                normal_style,
            )
        )

    # ------------------------------------------------------
    # ANNOTATED IMAGE
    # ------------------------------------------------------

    if annotated_image is not None:
        story.append(
            Paragraph("06 | Annotated Detection Image", heading_style)
        )

        try:
            from PIL import Image as PILImage

            image_buffer = BytesIO()

            if isinstance(annotated_image, PILImage.Image):
                pil_image = annotated_image.convert("RGB")
            else:
                pil_image = PILImage.fromarray(annotated_image).convert("RGB")

            pil_image.save(image_buffer, format="PNG")
            image_buffer.seek(0)

            report_image = Image(
                image_buffer,
                width=150 * mm,
                height=100 * mm,
                kind="proportional",
            )

            report_image.hAlign = "CENTER"
            story.append(report_image)

        except Exception:
            story.append(
                Paragraph(
                    "The annotated image could not be included in this report.",
                    small_style,
                )
            )

    # ------------------------------------------------------
    # DISCLAIMER
    # ------------------------------------------------------

    story.append(
        Paragraph("Important Safety Disclaimer", heading_style)
    )

    story.append(
        Paragraph(
            "This report contains AI-generated object detection results. "
            "The detected objects and confidence scores are model predictions "
            "and may contain errors, omissions or false detections. "
            "They do not independently establish a safety violation or "
            "guarantee PPE compliance. All findings must be reviewed by "
            "a qualified human safety professional. This system does not "
            "replace professional construction-site inspections or "
            "applicable safety procedures.",
            normal_style,
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=SAFETY_LIME,
        )
    )

    story.append(Spacer(1, 5))

    story.append(
        Paragraph(
            "Generated by BuildGuard AI | "
            "AI-Powered Construction Site Safety Monitoring",
            small_style,
        )
    )

    # ------------------------------------------------------
    # BUILD PDF
    # ------------------------------------------------------

    doc.build(
        story,
        onFirstPage=_build_footer,
        onLaterPages=_build_footer,
    )

    buffer.seek(0)
    return buffer.getvalue()
