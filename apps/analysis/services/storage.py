"""Keep originals outside Django's static root and serve only derived previews."""

from pathlib import Path

from django.conf import settings


def original_path(stored_name: str) -> Path:
    if Path(stored_name).name != stored_name:
        raise ValueError("Invalid stored name")
    return settings.PRIVATE_DIR / stored_name


def preview_path(analysis_id) -> Path:
    return settings.PRIVATE_DIR / f"preview-{analysis_id}.jpg"


def delete_files(analysis):
    original_path(analysis.stored_name).unlink(missing_ok=True)
    preview_path(analysis.id).unlink(missing_ok=True)
