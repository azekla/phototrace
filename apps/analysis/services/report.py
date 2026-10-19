"""Public-only exports of a saved analysis."""

import io
import json
from pathlib import Path

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape


def report_data(analysis):
    return {
        "id": str(analysis.id),
        "checked_at": timezone.localtime(analysis.created_at).isoformat(),
        "filename": analysis.original_name,
        "sha256": analysis.sha256,
        "format": analysis.image_format,
        "size": {"width": analysis.width, "height": analysis.height, "bytes": analysis.byte_size},
        "state": analysis.state,
        "verdict": analysis.verdict,
        "verdict_text": analysis.verdict_text,
        "model_score": analysis.score,
        "score_notice": "Оценка модели не является доказательством происхождения или калиброванной вероятностью.",
        "model_status": analysis.model_status,
        "model_id": analysis.model_id,
        "model_sha256": analysis.model_sha256,
        "thresholds": {"real_max": 0.35, "generated_min": 0.65, "status": "предварительные; независимая калибровка ещё не выполнена"},
        "metadata_status": analysis.metadata_status,
        "metadata": analysis.metadata.get("public", {}),
        "metadata_notes": analysis.metadata.get("notes", []),
        "private_fields_excluded": bool(analysis.metadata.get("private")),
        "notes": analysis.notes,
        "processing_ms": analysis.processing_ms,
    }


def json_bytes(analysis):
    return json.dumps(report_data(analysis), ensure_ascii=False, indent=2).encode("utf-8")


def _register_font():
    for path in [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]:
        if path.exists():
            pdfmetrics.registerFont(TTFont("PhotoTrace", str(path)))
            return "PhotoTrace"
    raise RuntimeError("Кириллический шрифт для PDF не найден")


def pdf_bytes(analysis):
    data = report_data(analysis)
    font = _register_font()
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        if hasattr(style, "fontName"):
            style.fontName = font
            style.leading = max(style.leading, style.fontSize * 1.4)
    body = styles["BodyText"]
    story = [Paragraph("PhotoTrace — отчёт об анализе изображения", styles["Title"]), Spacer(1, 18)]
    fields = [
        ("Дата", data["checked_at"]), ("Файл", data["filename"]),
        ("Формат и размеры", f"{data['format']}, {data['size']['width']} × {data['size']['height']}"),
        ("SHA-256", data["sha256"]), ("Вывод", data["verdict_text"]),
        ("Оценка модели", "—" if data["model_score"] is None else f"{data['model_score']:.4f}"),
        ("Модель", data["model_id"] or "недоступна"),
    ]
    for label, value in fields:
        story.append(Paragraph(f"<b>{escape(label)}:</b> {escape(str(value))}", body))
        story.append(Spacer(1, 5))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Метаданные", styles["Heading2"]))
    if data["metadata"]:
        rows = [[Paragraph("Поле", body), Paragraph("Значение", body)]]
        for key, value in data["metadata"].items():
            rows.append([Paragraph(escape(str(key)), body), Paragraph(escape(str(value)), body)])
        table = Table(rows, colWidths=[145, 355], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5edf7")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#d6deea")),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Поддерживаемые метаданные не найдены.", body))
    story.append(Spacer(1, 12))
    for note in data["metadata_notes"] + data["notes"]:
        story.append(Paragraph(escape(str(note)), body))
        story.append(Spacer(1, 5))
    story.append(Paragraph(escape(data["score_notice"]), body))
    story.append(Paragraph("Пороговые значения предварительные. Чувствительные поля исключены из отчёта.", body))
    doc.build(story)
    return output.getvalue()
