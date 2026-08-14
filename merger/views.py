from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, "merger/dashboard.html")


@login_required
def merge_view(request):
    # placeholder for upload form and merge initiation
    return render(request, "merger/merge.html")


@login_required
def history(request):
    return render(request, "merger/history.html")
