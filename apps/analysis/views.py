from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Analysis
from .services.report import json_bytes, pdf_bytes
from .services.storage import delete_files, original_path, preview_path
from .services.upload import validate_upload


def _session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _own_analysis(request, analysis_id):
    return get_object_or_404(Analysis, id=analysis_id, owner_session=_session_key(request))


@require_GET
def index(request):
    return render(request, "analysis/index.html", {"recent": Analysis.objects.filter(owner_session=_session_key(request))[:3]})


@require_POST
def create_analysis(request):
    session_key = _session_key(request)
    if Analysis.objects.filter(owner_session=session_key, state__in=["queued", "running"]).count() >= 2:
        return render(request, "analysis/index.html", {"error": "Сначала дождитесь завершения текущих проверок."}, status=429)
    if Analysis.objects.filter(state__in=["queued", "running"]).count() >= 10:
        return render(request, "analysis/index.html", {"error": "Очередь занята. Попробуйте позже."}, status=503)
    try:
        info = validate_upload(request.FILES.get("image"))
    except ValidationError as exc:
        return render(request, "analysis/index.html", {"error": exc.messages[0]}, status=400)
    raw = info.pop("raw")
    with transaction.atomic():
        analysis = Analysis.objects.create(
            owner_session=session_key,
            expires_at=timezone.now() + timedelta(days=7),
            **info,
        )
        try:
            original_path(analysis.stored_name).write_bytes(raw)
        except OSError:
            analysis.delete()
            return render(request, "analysis/index.html", {"error": "Не удалось сохранить файл."}, status=500)
    return redirect("analysis-result", analysis_id=analysis.id)


@require_GET
def result(request, analysis_id):
    analysis = _own_analysis(request, analysis_id)
    return render(request, "analysis/result.html", {
        "analysis": analysis,
        "public_metadata": analysis.metadata.get("public", {}),
        "metadata_notes": analysis.metadata.get("notes", []),
        "has_private": bool(analysis.metadata.get("private")),
    })


@require_GET
def status(request, analysis_id):
    analysis = _own_analysis(request, analysis_id)
    return JsonResponse({"state": analysis.state, "state_text": analysis.get_state_display(), "done": analysis.state not in {"queued", "running"}})


@require_GET
def preview(request, analysis_id):
    analysis = _own_analysis(request, analysis_id)
    path = preview_path(analysis.id)
    if not path.exists():
        raise Http404
    response = FileResponse(path.open("rb"), content_type="image/jpeg")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def private_metadata(request, analysis_id):
    analysis = _own_analysis(request, analysis_id)
    response = JsonResponse({"fields": analysis.metadata.get("private", {})})
    response["Cache-Control"] = "private, no-store"
    return response


@require_GET
def history(request):
    items = Analysis.objects.filter(owner_session=_session_key(request))
    return render(request, "analysis/history.html", {"page": Paginator(items, 20).get_page(request.GET.get("page"))})


@require_GET
def report_json(request, analysis_id):
    analysis = _own_analysis(request, analysis_id)
    if analysis.state in {"queued", "running"}:
        raise Http404
    response = HttpResponse(json_bytes(analysis), content_type="application/json; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="phototrace-{analysis.id}.json"'
    response["Cache-Control"] = "private, no-store"
    return response


@require_GET
def report_pdf(request, analysis_id):
    analysis = _own_analysis(request, analysis_id)
    if analysis.state in {"queued", "running"}:
        raise Http404
    response = HttpResponse(pdf_bytes(analysis), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="phototrace-{analysis.id}.pdf"'
    response["Cache-Control"] = "private, no-store"
    return response


@require_POST
def delete_analysis(request, analysis_id):
    with transaction.atomic():
        analysis = _own_analysis(request, analysis_id)
        delete_files(analysis)
        analysis.delete()
    return redirect("analysis-history")


@require_GET
def methodology(request):
    return render(request, "analysis/methodology.html")


@require_GET
def about(request):
    return render(request, "analysis/about.html")


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})
