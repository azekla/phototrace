import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import OperationalError
from django.utils import timezone

from apps.analysis.models import Analysis
from apps.analysis.services.pipeline import process_analysis
from ml.detector import Detector


class Command(BaseCommand):
    help = "Обрабатывать задачи анализа в отдельном процессе"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Обработать не более одной задачи и завершить работу")

    def handle(self, *args, **options):
        try:
            detector = Detector()
            error = None
            self.stdout.write(self.style.SUCCESS("Модель загружена."))
        except Exception as exc:
            detector = None
            error = "Визуальная модель недоступна; метаданные будут извлечены."
            self.stderr.write(f"Model load failed: {type(exc).__name__}: {exc}")

        # A crashed task is not silently retried with a possibly duplicated result.
        stale = timezone.now() - timedelta(minutes=10)
        Analysis.objects.filter(state=Analysis.State.RUNNING, started_at__lt=stale).update(
            state=Analysis.State.FAILED,
            model_status="unavailable",
            notes=["Обработка была прервана. Запустите новую проверку."],
            finished_at=timezone.now(),
        )
        while True:
            try:
                candidate = Analysis.objects.filter(state=Analysis.State.QUEUED).order_by("created_at").values_list("id", flat=True).first()
                if candidate:
                    claimed = Analysis.objects.filter(id=candidate, state=Analysis.State.QUEUED).update(
                        state=Analysis.State.RUNNING, started_at=timezone.now()
                    )
                    if claimed:
                        process_analysis(candidate, detector, error)
                        self.stdout.write(f"Processed {candidate}")
                        if options["once"]:
                            return
                        continue
            except OperationalError:
                # Short SQLite write contention is possible while the web process writes.
                time.sleep(1)
            if options["once"]:
                return
            time.sleep(1)
