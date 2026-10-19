from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analysis.models import Analysis
from apps.analysis.services.storage import delete_files


class Command(BaseCommand):
    help = "Удалить просроченные проверки и файлы"

    def handle(self, *args, **options):
        count = 0
        for analysis in Analysis.objects.filter(expires_at__lt=timezone.now()).iterator():
            delete_files(analysis)
            analysis.delete()
            count += 1
        self.stdout.write(f"Удалено проверок: {count}")
