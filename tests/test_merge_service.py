from pathlib import Path

import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from merger.models import MergeJob
from merger.services.merger_service import MergeService


@pytest.mark.django_db
def test_run_merge_creates_database_stats_and_output(tmp_path):
    css_a = tmp_path / "base.css"
    css_b = tmp_path / "theme.css"
    css_a.write_text("body { color: red; background: white; }\n.btn { color: blue; }\n", encoding="utf-8")
    css_b.write_text("body { color: blue; }\n.btn { color: blue; }\n", encoding="utf-8")

    user = get_user_model().objects.create_user(username="tester", email="tester@example.com", password="secret123")
    service = MergeService(user)

    result = service.run_merge([css_a, css_b], strategy="prefer_style2")

    assert result["status"] == "completed"
    assert result["conflict_count"] == 1
    assert result["duplicate_count"] >= 1
    assert result["output_path"]
    assert Path(result["output_path"]).exists()
    assert MergeJob.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_dashboard_uses_real_merge_statistics(client):
    user = get_user_model().objects.create_user(username="dash", email="dash@example.com", password="secret123")
    MergeJob.objects.create(
        user=user,
        status="completed",
        strategy="prefer_style2",
        duplicate_count=4,
        conflict_count=2,
        total_files=2,
    )
    MergeJob.objects.create(
        user=user,
        status="completed",
        strategy="prefer_style1",
        duplicate_count=1,
        conflict_count=0,
        total_files=1,
    )

    client.force_login(user)
    response = client.get(reverse("merger:dashboard"))

    assert response.status_code == 200
    assert response.context["stats"]["total_files"] == 3
    assert response.context["stats"]["duplicates_removed"] == 5
    assert response.context["stats"]["conflicts_resolved"] == 2
    assert response.context["stats"]["completed_jobs"] == 2


@pytest.mark.django_db
def test_merge_view_post_with_files(client, tmp_path):
    """Test that the merge view POST handler processes files and creates a job."""
    css_a = tmp_path / "style1.css"
    css_b = tmp_path / "style2.css"
    css_a.write_text("body { color: red; }\n")
    css_b.write_text("body { color: blue; }\n")

    user = get_user_model().objects.create_user(username="merger", email="merger@example.com", password="secret123")
    client.force_login(user)

    with open(css_a, "rb") as f1, open(css_b, "rb") as f2:
        response = client.post(
            reverse("merger:merge"),
            {
                "css_files": [f1, f2],
                "strategy": "prefer_style2",
            },
        )

    assert response.status_code == 302
    assert MergeJob.objects.filter(user=user).count() == 1

    job = MergeJob.objects.get(user=user)
    assert job.status == "completed"
    assert job.strategy == "prefer_style2"
    assert job.total_files == 2
