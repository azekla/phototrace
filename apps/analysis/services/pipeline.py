"""Run one queued analysis while preserving partial results."""

import io
import time

from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageOps

from apps.analysis.models import Analysis
from apps.analysis.services.metadata import extract_metadata
from apps.analysis.services.storage import original_path, preview_path
from ml.detector import MODEL_ID, verdict_for_score


def _make_preview(raw):
    with Image.open(io.BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            rgba = image.convert("RGBA")
            white = Image.new("RGBA", rgba.size, "white")
            white.alpha_composite(rgba)
            image = white.convert("RGB")
        else:
            image = image.convert("RGB")
        output = io.BytesIO()
        image.save(output, "JPEG", quality=85, optimize=True)
        return output.getvalue()


def process_analysis(analysis_id, detector=None, detector_error=None):
    started = time.perf_counter()
    try:
        analysis = Analysis.objects.get(id=analysis_id, state=Analysis.State.RUNNING)
    except Analysis.DoesNotExist:
        return
    try:
        raw = original_path(analysis.stored_name).read_bytes()
    except OSError:
        Analysis.objects.filter(id=analysis_id, state=Analysis.State.RUNNING).update(
            state=Analysis.State.FAILED,
            model_status="unavailable",
            metadata_status="unavailable",
            notes=["Исходный файл недоступен."],
            finished_at=timezone.now(),
        )
        return

    metadata = {}
    notes = []
    try:
        metadata = extract_metadata(raw)
        metadata_status = "ready"
    except Exception:
        metadata_status = "error"
        notes.append("Не удалось прочитать метаданные.")

    try:
        preview = _make_preview(raw)
    except Exception:
        preview = None
        notes.append("Не удалось создать превью изображения.")

    score = None
    verdict = "unavailable"
    model_status = "unavailable"
    if detector is None:
        notes.append(detector_error or "Визуальная модель недоступна.")
    else:
        try:
            score = detector.predict(raw)
            verdict = verdict_for_score(score)
            model_status = "ready"
        except Exception:
            notes.append("Визуальный анализ не завершился из-за ошибки модели.")

    if model_status == "ready" and metadata_status == "ready":
        state = Analysis.State.COMPLETED
    elif model_status == "ready" or metadata_status == "ready":
        state = Analysis.State.PARTIAL
    else:
        state = Analysis.State.FAILED

    with transaction.atomic():
        if not Analysis.objects.filter(id=analysis_id, state=Analysis.State.RUNNING).exists():
            return
        if preview:
            preview_path(analysis_id).write_bytes(preview)
        Analysis.objects.filter(id=analysis_id, state=Analysis.State.RUNNING).update(
            state=state,
            score=score,
            verdict=verdict,
            model_status=model_status,
            metadata_status=metadata_status,
            metadata=metadata,
            notes=notes,
            model_id=MODEL_ID if detector is not None else "",
            model_sha256=detector.sha256 if detector is not None else "",
            processing_ms=round((time.perf_counter() - started) * 1000),
            finished_at=timezone.now(),
        )
