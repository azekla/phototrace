"""Validate untrusted images before they enter the analysis queue."""

import hashlib
import io
import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
Image.MAX_TEXT_CHUNK = 1024 * 1024
Image.MAX_TEXT_MEMORY = 2 * 1024 * 1024

ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def validate_upload(upload):
    if not upload:
        raise ValidationError("Выберите изображение.")
    if upload.size > settings.MAX_IMAGE_BYTES:
        raise ValidationError("Размер файла превышает 15 МБ.")
    if upload.size == 0:
        raise ValidationError("Файл пустой.")
    raw = upload.read(settings.MAX_IMAGE_BYTES + 1)
    if len(raw) > settings.MAX_IMAGE_BYTES:
        raise ValidationError("Размер файла превышает 15 МБ.")
    try:
        with Image.open(io.BytesIO(raw)) as image:
            fmt = image.format
            width, height = image.size
            frames = getattr(image, "n_frames", 1)
            if fmt not in ALLOWED_FORMATS:
                raise ValidationError("Поддерживаются только JPEG, PNG и WebP.")
            if frames != 1:
                raise ValidationError("Анимированные изображения не поддерживаются.")
            if width * height > settings.MAX_IMAGE_PIXELS:
                raise ValidationError("Изображение содержит слишком много пикселей (максимум 25 Мп).")
            image.load()
    except ValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValidationError("Не удалось прочитать изображение. Возможно, файл повреждён.") from exc

    name = str(upload.name or "image")[-255:]
    name = re.sub(r"[\x00-\x1f\x7f\\/]", "_", name).strip(" .") or "image"
    stored_name = f"{uuid.uuid4().hex}{ALLOWED_FORMATS[fmt]}"
    return {
        "raw": raw,
        "original_name": name,
        "stored_name": stored_name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_size": len(raw),
        "image_format": fmt,
        "width": width,
        "height": height,
    }
