import hashlib
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ml.detector import EXPECTED_SHA256


URL = (
    "https://huggingface.co/angelhd25/ull-ai-image-detector/resolve/"
    "88ae192e4001bcbbf6f02de75e033171e227b5b2/commfor384_web_v13_fp32.onnx"
)


class Command(BaseCommand):
    help = "Скачать закреплённые веса и проверить SHA-256"

    def handle(self, *args, **options):
        target = settings.MODEL_PATH
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() == EXPECTED_SHA256:
                self.stdout.write(self.style.SUCCESS("Модель уже загружена и проверена."))
                return
            raise CommandError("Файл модели существует, но его SHA-256 неверен.")
        part = target.with_suffix(".part")
        digest = hashlib.sha256()
        try:
            with urlopen(Request(URL, headers={"User-Agent": "PhotoTrace/0.1"}), timeout=120) as response, part.open("wb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
                    digest.update(block)
            if digest.hexdigest() != EXPECTED_SHA256:
                raise CommandError("Контрольная сумма загруженной модели неверна.")
            part.replace(target)
        except Exception:
            part.unlink(missing_ok=True)
            raise
        self.stdout.write(self.style.SUCCESS(f"Модель проверена: {target}"))
