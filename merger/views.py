from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from pathlib import Path
import tempfile
import logging

from merger.models import MergeJob
from merger.services.merger_service import MergeService

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    display_name = ""
    try:
        profile = request.user.profile
        display_name = profile.display_name or ""
    except Exception:
        pass
    welcome_name = display_name or request.user.username or "User"

    jobs = MergeJob.objects.filter(user=request.user).order_by("-created_at")
    stats = {
        "total_files": sum(job.total_files for job in jobs),
        "conflicts_resolved": sum(job.conflict_count for job in jobs),
        "duplicates_removed": sum(job.duplicate_count for job in jobs),
        "completed_jobs": jobs.filter(status="completed").count(),
    }

    recent_merges = []
    for job in jobs[:5]:
        recent_merges.append(
            {
                "id": job.pk,
                "status": job.status,
                "files_text": job.files_text,
                "strategy_label": job.strategy_label,
            }
        )

    context = {
        "welcome_name": welcome_name,
        "stats": stats,
        "recent_merges": recent_merges,
    }
    return render(request, "merger/dashboard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def merge_view(request):
    if request.method == "POST":
        return handle_merge_post(request)
    return render(request, "merger/merge.html")


def handle_merge_post(request):
    """Process CSS file uploads and run merge."""
    css_files = request.FILES.getlist("css_files")
    strategy = request.POST.get("strategy", "prefer_style2")

    if not css_files:
        return JsonResponse({"error": "No CSS files uploaded"}, status=400)

    if len(css_files) > 10:
        return JsonResponse({"error": "Maximum 10 files allowed"}, status=400)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_paths = []

            for uploaded_file in css_files:
                if not uploaded_file.name.endswith(".css"):
                    return JsonResponse(
                        {"error": f"Invalid file: {uploaded_file.name}. Only .css files allowed."}, status=400
                    )

                file_path = tmp_path / uploaded_file.name
                file_path.write_bytes(uploaded_file.read())
                file_paths.append(file_path)

            service = MergeService(request.user)
            result = service.run_merge(file_paths, strategy=strategy)

            if result["status"] != "completed":
                return JsonResponse({"error": result.get("message", "Merge failed")}, status=500)

            return redirect("merger:result", job_id=result["job_id"])

    except Exception as e:
        logger.exception("Merge failed")
        return JsonResponse({"error": f"Merge failed: {str(e)}"}, status=500)


@login_required
def result(request, job_id):
    """Display merge results and conflicts."""
    try:
        job = MergeJob.objects.get(pk=job_id, user=request.user)
    except MergeJob.DoesNotExist:
        return HttpResponseForbidden("Job not found or not authorized")

    merged_css = ""
    if job.output_file:
        try:
            merged_css = job.output_file.read().decode("utf-8")
        except Exception as e:
            logger.warning(f"Could not read output file: {e}")
            merged_css = "(Unable to read merged CSS)"

    conflicts = job.conflicts.all()

    context = {
        "job": job,
        "merged_css": merged_css,
        "conflicts": list(conflicts),
        "conflict_count": len(conflicts),
    }
    return render(request, "merger/result.html", context)


@login_required
def history(request):
    history_jobs = MergeJob.objects.filter(user=request.user).order_by("-created_at")
    context = {"history": list(history_jobs)}
    return render(request, "merger/history.html", context)
