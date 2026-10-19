from django.contrib import admin

from .models import Analysis


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "state", "verdict", "image_format", "byte_size")
    list_filter = ("state", "verdict", "image_format")
    search_fields = ("id", "sha256", "original_name")
    readonly_fields = [field.name for field in Analysis._meta.fields]

    def has_add_permission(self, request):
        return False
