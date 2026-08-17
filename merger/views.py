from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    display_name = ""
    try:
        profile = request.user.profile
        display_name = profile.display_name or ""
    except Exception:
        pass
    welcome_name = display_name or request.user.username or "User"

    stats = {
        "total_files": 0,
        "conflicts_resolved": 0,
        "duplicates_removed": 0,
        "completed_jobs": 0,
    }

    recent_merges = []

    context = {
        "welcome_name": welcome_name,
        "stats": stats,
        "recent_merges": recent_merges,
    }
    return render(request, "merger/dashboard.html", context)


@login_required
def merge_view(request):
    return render(request, "merger/merge.html")


@login_required
def history(request):
    return render(request, "merger/history.html")
