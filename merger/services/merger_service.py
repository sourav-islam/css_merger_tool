"""Service that orchestrates the CSS merger engine and stores job metadata."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from django.core.files.base import ContentFile

from merger.css_merger_engine.comparator import Comparator
from merger.css_merger_engine.merger import Merger
from merger.css_merger_engine.parser import CSSParser
from merger.css_merger_engine.reporter import Reporter
from merger.css_merger_engine.writer import CSSWriter
from merger.models import CSSFile, Conflict as JobConflict, MergeInput, MergeJob

logger = logging.getLogger(__name__)


class MergeService:
    def __init__(self, user):
        self.user = user

    def run_merge(self, input_files: List[Path], strategy: str = "prefer_style2"):
        logger.info("Starting merge for user %s with %d files", self.user, len(input_files))

        if not input_files:
            return {"status": "failed", "message": "No CSS files supplied."}

        clean_strategy = strategy or "prefer_style2"
        parser = CSSParser()
        comparator = Comparator()
        merger = Merger(strategy=clean_strategy)
        reporter = Reporter(clean_strategy)
        writer = CSSWriter()

        parsed = [parser.parse_file(path) for path in input_files if path and Path(path).exists()]
        if not parsed:
            return {"status": "failed", "message": "No readable CSS files were found."}

        base = parsed[0]
        for sheet in parsed[1:]:
            _, conflicts = comparator.compare(base, sheet)
            if conflicts:
                for conflict in conflicts:
                    if conflict.resolution is None:
                        conflict.resolution = "b"
            base = merger.merge(base, sheet, conflicts if "conflicts" in locals() else [])

        if len(parsed) > 1:
            _, conflicts = comparator.compare(parsed[0], parsed[1])
            merged = merger.merge(parsed[0], parsed[1], conflicts)
        else:
            merged = parsed[0]
            conflicts = []

        merged_css = writer.render(merged)
        report_text = reporter.build_summary_report(parsed[0], parsed[1] if len(parsed) > 1 else parsed[0], merged, conflicts)
        if len(parsed) > 1:
            conflicts_text = reporter.build_conflicts_report(conflicts)
        else:
            conflicts_text = "No conflicts detected.\n"

        job = MergeJob.objects.create(
            user=self.user,
            status="completed",
            strategy=clean_strategy,
            total_files=len(input_files),
            duplicate_count=self._count_duplicates(parsed),
            conflict_count=len(conflicts),
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        for index, path in enumerate(input_files):
            file_path = Path(path)
            css_bytes = file_path.read_bytes() if file_path.exists() else b""
            css_file = CSSFile.objects.create(
                user=self.user,
                file=ContentFile(css_bytes, name=file_path.name),
                original_filename=file_path.name,
            )
            MergeInput.objects.create(merge_job=job, css_file=css_file, position=index)

        output_name = f"merged_{self.user.pk}_{job.pk}.css"
        job.output_file.save(output_name, ContentFile(merged_css.encode("utf-8")))
        job.save()

        for conflict in conflicts:
            JobConflict.objects.create(
                merge_job=job,
                selector=conflict.selector,
                property_name=conflict.property,
                value_a=conflict.declaration_a.value,
                value_b=conflict.declaration_b.value,
                resolution=conflict.resolution,
            )

        logger.info(
            "Merge complete for user %s: %d files, %d conflicts, %d duplicates",
            self.user,
            len(input_files),
            len(conflicts),
            job.duplicate_count,
        )

        return {
            "status": "completed",
            "message": "CSS merge completed successfully.",
            "job_id": job.pk,
            "output_path": str(job.output_file.path if job.output_file else ""),
            "conflict_count": len(conflicts),
            "duplicate_count": job.duplicate_count,
            "report": report_text,
            "conflicts_text": conflicts_text,
        }

    def _count_duplicates(self, parsed_sheets):
        seen = set()
        duplicate_total = 0

        for sheet in parsed_sheets:
            for rule in sheet.all_rules_flat():
                if rule.is_container():
                    continue
                for decl in rule.declarations:
                    key = (
                        rule.normalized_selector() if hasattr(rule, "normalized_selector") else rule.selector,
                        decl.normalized_key(),
                        decl.value.strip().lower(),
                    )
                    if key in seen:
                        duplicate_total += 1
                    else:
                        seen.add(key)

        return duplicate_total
