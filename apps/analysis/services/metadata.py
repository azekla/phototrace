"""Extract a bounded, display-safe subset of container metadata."""

import io

from defusedxml import ElementTree
from PIL import ExifTags, Image


PRIVATE_KEYS = {"GPSInfo", "BodySerialNumber", "CameraSerialNumber", "LensSerialNumber", "Artist", "Copyright"}
EXIF_LIMIT = 100
TEXT_LIMIT = 3000


def _string(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    elif isinstance(value, (list, tuple)):
        value = ", ".join(_string(x) for x in value[:12])
    else:
        value = str(value)
    return value[:TEXT_LIMIT]


def extract_metadata(raw: bytes) -> dict:
    public = {}
    private = {}
    notes = []
    with Image.open(io.BytesIO(raw)) as image:
        exif = image.getexif()
        if exif:
            for tag_id, value in list(exif.items())[:EXIF_LIMIT]:
                key = ExifTags.TAGS.get(tag_id, str(tag_id))
                if key in {"MakerNote", "UserComment", "PrintIM", "Padding", "ExifOffset"}:
                    continue
                target = private if key in PRIVATE_KEYS or "Serial" in key else public
                if key == "GPSInfo":
                    try:
                        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
                        target[key] = ", ".join(f"{ExifTags.GPSTAGS.get(k,k)}: {_string(v)}" for k, v in list(gps.items())[:20])[:TEXT_LIMIT]
                    except (KeyError, ValueError, TypeError):
                        target[key] = "Присутствует, но не удалось прочитать"
                else:
                    target[key] = _string(value)
            try:
                detailed = exif.get_ifd(ExifTags.IFD.Exif)
            except (KeyError, ValueError, TypeError):
                detailed = {}
            for tag_id, value in list(detailed.items())[:EXIF_LIMIT]:
                key = ExifTags.TAGS.get(tag_id, str(tag_id))
                if key in {"MakerNote", "UserComment", "PrintIM", "Padding"}:
                    continue
                target = private if key in PRIVATE_KEYS or "Serial" in key else public
                target.setdefault(key, _string(value))

        if image.format == "PNG":
            for key, value in list(image.info.items())[:EXIF_LIMIT]:
                if key in {"exif", "icc_profile", "transparency", "gamma", "dpi"}:
                    continue
                if isinstance(value, (str, bytes)):
                    public[f"PNG:{key}"] = _string(value)

        xmp = image.info.get("xmp") or image.info.get("XML:com.adobe.xmp")
        if isinstance(xmp, str):
            xmp = xmp.encode("utf-8", "replace")
        if xmp:
            if len(xmp) > 1024 * 1024:
                notes.append("XMP слишком большой и не был прочитан.")
            else:
                try:
                    root = ElementTree.fromstring(xmp)
                    count = 0
                    for node in root.iter():
                        if count >= EXIF_LIMIT:
                            break
                        if node.text and node.text.strip():
                            key = node.tag.rsplit("}", 1)[-1]
                            target = private if any(part in key.lower() for part in ("gps", "serial", "creator", "author")) else public
                            target[f"XMP:{key}"] = _string(node.text.strip())
                            count += 1
                except (ElementTree.ParseError, ValueError):
                    notes.append("XMP присутствует, но его не удалось прочитать.")

    if not public and not private:
        notes.append("В файле не найдены поддерживаемые метаданные.")
    notes.append("Метаданные можно изменить или удалить; сами по себе они не доказывают происхождение изображения.")
    return {"public": public, "private": private, "notes": notes, "version": "1"}
