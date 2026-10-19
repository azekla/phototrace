from django.core.management.base import BaseCommand, CommandError

from ml.detector import Detector


class Command(BaseCommand):
    help = "Проверить файл модели и запуск ONNX Runtime"

    def handle(self, *args, **options):
        try:
            detector = Detector()
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Модель готова; SHA-256: {detector.sha256}"))
