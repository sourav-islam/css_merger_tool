from __future__ import annotations

from typing import List

from merger.css_merger_engine.models import Conflict, Stylesheet


class Reporter:
    def __init__(self, strategy: str):
        self.strategy = strategy

    def build_conflicts_report(self, conflicts: List[Conflict]) -> str:
        if not conflicts:
            return "No conflicts detected.\n"

        lines = [f"CSS MERGE CONFLICTS ({len(conflicts)} total)", "=" * 60, ""]
        for i, conflict in enumerate(conflicts, start=1):
            lines.append(f"[{i}] {conflict.describe()}")
            resolution = conflict.resolution or "unresolved"
            if resolution == "a":
                winner_file = conflict.declaration_a.source_file
            elif resolution == "b":
                winner_file = conflict.declaration_b.source_file
            else:
                winner_file = "N/A"
            lines.append(f"    Resolution: kept value from {winner_file}")
            lines.append("")

        return "\n".join(lines)

    def build_summary_report(
        self,
        sheet_a: Stylesheet,
        sheet_b: Stylesheet,
        merged: Stylesheet,
        conflicts: List[Conflict],
    ) -> str:
        stats_a = self._stylesheet_stats(sheet_a)
        stats_b = self._stylesheet_stats(sheet_b)
        stats_merged = self._stylesheet_stats(merged)

        resolved_a = sum(1 for c in conflicts if c.resolution == "a")
        resolved_b = sum(1 for c in conflicts if c.resolution == "b")

        lines = [
            "CSS MERGE REPORT",
            "=" * 60,
            "",
            f"Strategy used: {self.strategy}",
            "",
            "-- Source Files --",
            f"style1.css: {stats_a['rules']} rules, {stats_a['declarations']} declarations, {stats_a['at_rules']} at-rules",
            f"style2.css: {stats_b['rules']} rules, {stats_b['declarations']} declarations, {stats_b['at_rules']} at-rules",
            "",
            "-- Merged Output --",
            f"merged.css: {stats_merged['rules']} rules, {stats_merged['declarations']} declarations, {stats_merged['at_rules']} at-rules",
            "",
            "-- Conflicts --",
            f"Total conflicts detected: {len(conflicts)}",
            f"Resolved in favor of style1.css: {resolved_a}",
            f"Resolved in favor of style2.css: {resolved_b}",
            "",
            "-- Deduplication --",
            f"Rules before merge (combined): {stats_a['rules'] + stats_b['rules']}",
            f"Rules after merge: {stats_merged['rules']}",
            f"Declarations before merge (combined): {stats_a['declarations'] + stats_b['declarations']}",
            f"Declarations after merge: {stats_merged['declarations']}",
        ]
        return "\n".join(lines) + "\n"

    def _stylesheet_stats(self, sheet: Stylesheet) -> dict:
        flat = sheet.all_rules_flat()
        at_rules = [r for r in flat if r.is_at_rule]
        leaf_rules = [r for r in flat if not r.is_container()]
        declarations = sum(len(r.declarations) for r in leaf_rules)
        return {"rules": len(leaf_rules), "at_rules": len(at_rules), "declarations": declarations}