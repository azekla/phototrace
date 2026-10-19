from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="analysis-index"),
    path("analyses/", views.create_analysis, name="analysis-create"),
    path("analyses/<uuid:analysis_id>/", views.result, name="analysis-result"),
    path("analyses/<uuid:analysis_id>/status/", views.status, name="analysis-status"),
    path("analyses/<uuid:analysis_id>/preview/", views.preview, name="analysis-preview"),
    path("analyses/<uuid:analysis_id>/private-metadata/", views.private_metadata, name="analysis-private-metadata"),
    path("analyses/<uuid:analysis_id>/report.json", views.report_json, name="analysis-report-json"),
    path("analyses/<uuid:analysis_id>/report.pdf", views.report_pdf, name="analysis-report-pdf"),
    path("analyses/<uuid:analysis_id>/delete/", views.delete_analysis, name="analysis-delete"),
    path("history/", views.history, name="analysis-history"),
    path("methodology/", views.methodology, name="analysis-methodology"),
    path("about/", views.about, name="analysis-about"),
    path("health/", views.health, name="analysis-health"),
]
