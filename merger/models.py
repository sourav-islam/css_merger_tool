from __future__ import annotations

from django.conf import settings
from django.db import models


class CSSFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="css_files")
    file = models.FileField(upload_to="css_uploads/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"CSSFile({self.original_filename})"


class MergeJob(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("review", "Review"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="merge_jobs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    strategy = models.CharField(max_length=50, default="prefer_style2")
    total_files = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    conflict_count = models.PositiveIntegerField(default=0)
    output_file = models.FileField(upload_to="merged_css/%Y/%m/%d/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def strategy_label(self):
        return self.strategy.replace("_", " ").title()

    @property
    def files_text(self):
        return ", ".join(item.css_file.original_filename for item in self.inputs.all()[:5]) or f"{self.total_files} file(s)"

    def __str__(self):
        return f"MergeJob({self.pk})"


class MergeInput(models.Model):
    merge_job = models.ForeignKey(MergeJob, on_delete=models.CASCADE, related_name="inputs")
    css_file = models.ForeignKey(CSSFile, on_delete=models.CASCADE, related_name="merge_inputs")
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"MergeInput({self.css_file.original_filename})"


class Conflict(models.Model):
    merge_job = models.ForeignKey(MergeJob, on_delete=models.CASCADE, related_name="conflicts")
    selector = models.CharField(max_length=255)
    property_name = models.CharField(max_length=255)
    value_a = models.TextField()
    value_b = models.TextField()
    resolution = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Conflict({self.selector}: {self.property_name})"
