from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from merger.css_merger_engine import utils
from merger.css_merger_engine.models import ComparisonEntry, Conflict, Declaration, Rule, Stylesheet
from merger.css_merger_engine.normalizer import Normalizer


class Comparator:
    def __init__(self, normalizer: Optional[Normalizer] = None):
        self.normalizer = normalizer or Normalizer()
        self.logger = utils.setup_logger(self.__class__.__name__)

    def compare(
        self, sheet_a: Stylesheet, sheet_b: Stylesheet
    ) -> Tuple[List[ComparisonEntry], List[Conflict]]:
        index_a = self.normalizer.build_index(sheet_a)
        index_b = self.normalizer.build_index(sheet_b)

        all_keys = list(dict.fromkeys(list(index_a.keys()) + list(index_b.keys())))

        entries: List[ComparisonEntry] = []
        all_conflicts: List[Conflict] = []

        for context, selector in all_keys:
            rules_a = index_a.get((context, selector), [])
            rules_b = index_b.get((context, selector), [])

            decls_a = self._merge_same_file_declarations(rules_a)
            decls_b = self._merge_same_file_declarations(rules_b)

            entry = ComparisonEntry(context=context, selector=selector)

            properties = set(decls_a.keys()) | set(decls_b.keys())
            for prop in properties:
                da = decls_a.get(prop)
                db = decls_b.get(prop)

                if da and db:
                    va = self.normalizer.normalize_value(da.value)
                    vb = self.normalizer.normalize_value(db.value)
                    if va == vb and da.important == db.important:
                        entry.matching.append(db)
                    else:
                        conflict = Conflict(
                            selector=selector,
                            property=prop,
                            declaration_a=da,
                            declaration_b=db,
                            context=context,
                        )
                        entry.conflicts.append(conflict)
                        all_conflicts.append(conflict)
                elif da:
                    entry.only_in_a.append(da)
                elif db:
                    entry.only_in_b.append(db)

            entries.append(entry)

        self.logger.info(
            "Compared %d unique selector contexts, found %d conflicts",
            len(entries),
            len(all_conflicts),
        )
        return entries, all_conflicts

    def _merge_same_file_declarations(self, rules: List[Rule]) -> Dict[str, Declaration]:
        merged: Dict[str, Declaration] = {}
        for rule in rules:
            for decl in rule.declarations:
                merged[decl.normalized_key()] = decl
        return merged