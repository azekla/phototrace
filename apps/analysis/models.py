import uuid

from django.db import models


class Analysis(models.Model):
    class State(models.TextChoices):
        QUEUED = "queued", "В очереди"
        RUNNING = "running", "Обрабатывается"
        COMPLETED = "completed", "Готово"
        PARTIAL = "partial", "Частичный результат"
        FAILED = "failed", "Ошибка"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_session = models.CharField(max_length=64, db_index=True)
    original_name = models.CharField(max_length=255)
    stored_name = models.CharField(max_length=80, unique=True)
    sha256 = models.CharField(max_length=64)
    byte_size = models.PositiveIntegerField()
    image_format = models.CharField(max_length=12)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    state = models.CharField(max_length=20, choices=State.choices, default=State.QUEUED, db_index=True)
    score = models.FloatField(null=True, blank=True)
    verdict = models.CharField(max_length=32, blank=True)
    model_status = models.CharField(max_length=20, default="pending")
    metadata_status = models.CharField(max_length=20, default="pending")
    metadata = models.JSONField(default=dict)
    notes = models.JSONField(default=list)
    model_id = models.CharField(max_length=100, blank=True)
    model_sha256 = models.CharField(max_length=64, blank=True)
    processing_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    @property
    def verdict_text(self):
        return {
            "likely_real": "Вероятно реальное изображение",
            "likely_generated": "Вероятно изображение, созданное ИИ",
            "uncertain": "Недостаточно уверенности для вывода",
            "unavailable": "Визуальный анализ недоступен",
        }.get(self.verdict, "Ожидается анализ")

    @property
    def score_percent(self):
        return round(self.score * 100, 1) if self.score is not None else None
