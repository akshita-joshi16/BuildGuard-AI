
from io import BytesIO
from datetime import datetime

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


def generate_pdf_report(
    detections,
    source_name="Uploaded file",
    source_type="Image",
    annotated_image=None,
    summary=None,
    timestamp=None,
):
    """Generate a downloadable BuildGuard AI PDF safety report."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=23,
        textColor=colors.HexColor("#173B2E"),
        spaceAfter=6,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#246044"),
        spaceBefore=14,
        spaceAfter=8,
    )

    normal_style = styles["BodyText"]

    story = []

    report_time = timestamp or datetime.now().strftime(
        "%d %B %Y, %I:%M %p"
    )

    # Header
    story.append(Paragraph("BUILDGUARD AI", title_style))
    story.append(
        Paragraph(
            "Construction Site Safety Monitoring Report",
            styles["Heading3"],
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#D5EF65"),
        )
    )
    story.append(Spacer(1, 12))

    # Report information
    story.append(Paragraph("Report Information", heading_style))

    info_data = [
        ["File Name", str(source_name)],
        ["Analysis Type", str(source_type)],
        ["Report Generated", report_time],
    ]

    info_table = Table(info_data, colWidths=[42 * mm, 125 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EDF3ED")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#173B2E")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDE5DD")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # Summary
    story.append(Paragraph("Detection Summary", heading_style))

    total_detections = len(detections or [])

    story.append(
        Paragraph(
            f"<b>Total detected objects:</b> {total_detections}",
            normal_style,
        )
    )

    if summary is None:
        counts = {}
        for item in detections or []:
            name = str(item.get("class_name", "Unknown"))
            counts[name] = counts.get(name, 0) + 1
    else:
        counts = summary

    if counts:
        summary_data = [["Detected Category", "Count"]]
        for name, count in counts.items():
            summary_data.append([str(name), str(count)])

        summary_table = Table(
            summary_data,
            colWidths=[110 * mm, 57 * mm],
            repeatRows=1,
        )
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B2E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F5F7F3")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDE5DD")),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(summary_table)

    # Detection details
    story.append(Paragraph("Detection Details", heading_style))

    if detections:
        detail_data = [[
            "Category",
            "Confidence",
            "Timestamp",
        ]]

        for item in detections:
            category = str(item.get("class_name", "Unknown"))
            confidence = item.get("confidence", 0)
            timestamp_value = item.get(
                "timestamp_label",
                item.get("frame_timestamp", "-"),
            )

            try:
                confidence_text = f"{float(confidence) * 100:.1f}%"
            except (ValueError, TypeError):
                confidence_text = str(confidence)

            detail_data.append([
                category,
                confidence_text,
                str(timestamp_value),
            ])

        detail_table = Table(
            detail_data,
            colWidths=[70 * mm, 45 * mm, 52 * mm],
            repeatRows=1,
        )
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#246044")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDE5DD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#F5F7F3"),
            ]),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(detail_table)
    else:
        story.append(
            Paragraph("No objects were detected.", normal_style)
        )

    # Annotated image
    if annotated_image is not None:
        story.append(
            Paragraph("Annotated Detection Image", heading_style)
        )

        try:
            from PIL import Image as PILImage

            image_buffer = BytesIO()
            PILImage.fromarray(annotated_image).save(
                image_buffer,
                format="PNG",
            )
            image_buffer.seek(0)

            report_image = Image(
                image_buffer,
                width=150 * mm,
                height=100 * mm,
                kind="proportional",
            )
            story.append(report_image)
        except Exception:
            story.append(
                Paragraph(
                    "Annotated image could not be added.",
                    normal_style,
                )
            )

    # Disclaimer
    story.append(Spacer(1, 18))
    story.append(Paragraph("Disclaimer", heading_style))
    story.append(
        Paragraph(
            "This report contains AI-generated detection results. "
            "Predictions may contain errors and should not replace "
            "professional construction-site safety inspections.",
            normal_style,
        )
    )

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()
