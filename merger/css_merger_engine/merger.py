from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from merger.css_merger_engine import constants, utils
from merger.css_merger_engine.models import Conflict, Declaration, Rule, Stylesheet
from merger.css_merger_engine.normalizer import Normalizer


class Merger:
    def __init__(self, strategy: str = constants.DEFAULT_STRATEGY, normalizer: Optional[Normalizer] = None):
        if strategy not in constants.VALID_STRATEGIES:
            raise ValueError(f"Invalid strategy: {strategy}")
        self.strategy = strategy
        self.normalizer = normalizer or Normalizer()
        self.logger = utils.setup_logger(self.__class__.__name__)

    def merge(self, sheet_a: Stylesheet, sheet_b: Stylesheet, conflicts: List[Conflict]) -> Stylesheet:
        conflict_lookup = {(c.context, c.selector, c.property): c for c in conflicts}
        merged_rules = self._merge_rule_lists(sheet_a.rules, sheet_b.rules, context=None, conflict_lookup=conflict_lookup)
        self.logger.info("Merge complete: %d top-level rules, strategy=%s", len(merged_rules), self.strategy)
        return Stylesheet(rules=merged_rules, source_file="merged.css")

    def _merge_rule_lists(
        self,
        rules_a: List[Rule],
        rules_b: List[Rule],
        context: Optional[str],
        conflict_lookup: Dict[Tuple[Optional[str], str, str], Conflict],
    ) -> List[Rule]:
        output: List[Rule] = []
        consumed_b = set()

        b_by_selector: Dict[str, List[int]] = {}
        for idx, rb in enumerate(rules_b):
            key = self.normalizer.normalize_selector(rb.selector)
            b_by_selector.setdefault(key, []).append(idx)

        for ra in rules_a:
            key = self.normalizer.normalize_selector(ra.selector)
            match_idx = None
            for idx in b_by_selector.get(key, []):
                if idx not in consumed_b:
                    match_idx = idx
                    break

            rb = rules_b[match_idx] if match_idx is not None else None
            if match_idx is not None:
                consumed_b.add(match_idx)

            output.append(self._merge_one(ra, rb, context, conflict_lookup))

        for idx, rb in enumerate(rules_b):
            if idx in consumed_b:
                continue
            output.append(self._merge_one(None, rb, context, conflict_lookup))

        return output

    def _merge_one(
        self,
        ra: Optional[Rule],
        rb: Optional[Rule],
        context: Optional[str],
        conflict_lookup: Dict[Tuple[Optional[str], str, str], Conflict],
    ) -> Rule:
        base = ra or rb
        is_container = (ra is not None and ra.is_container()) or (rb is not None and rb.is_container())

        if is_container:
            nested_a = ra.nested_rules if (ra and ra.is_container()) else []
            nested_b = rb.nested_rules if (rb and rb.is_container()) else []
            merged_nested = self._merge_rule_lists(nested_a, nested_b, context=base.selector, conflict_lookup=conflict_lookup)
            return Rule(selector=base.selector, nested_rules=merged_nested, is_at_rule=True, source_file="merged")

        declarations = self._merge_declarations(context, base.selector, ra, rb, conflict_lookup)
        return Rule(selector=base.selector, declarations=declarations, is_at_rule=base.is_at_rule, source_file="merged")

    def _merge_declarations(
        self,
        context: Optional[str],
        selector: str,
        ra: Optional[Rule],
        rb: Optional[Rule],
        conflict_lookup: Dict[Tuple[Optional[str], str, str], Conflict],
    ) -> List[Declaration]:
        decls_a = {d.normalized_key(): d for d in (ra.declarations if ra else [])}
        decls_b = {d.normalized_key(): d for d in (rb.declarations if rb else [])}
        prop_order = list(dict.fromkeys(list(decls_a.keys()) + list(decls_b.keys())))
        normalized_selector = self.normalizer.normalize_selector(selector)

        result: List[Declaration] = []
        for prop in prop_order:
            da = decls_a.get(prop)
            db = decls_b.get(prop)

            if da and db:
                conflict = conflict_lookup.get((context, normalized_selector, prop))
                if conflict:
                    chosen = self._resolve(conflict)
                    conflict.resolution = "a" if chosen is conflict.declaration_a else "b"
                    result.append(chosen)
                else:
                    result.append(db)
            elif da:
                result.append(da)
            else:
                result.append(db)

        return result

    def _resolve(self, conflict: Conflict) -> Declaration:
        if self.strategy in {
            constants.STRATEGY_PREFER_FIRST,
            constants.STRATEGY_PREFER_STYLE1,
        }:
            return conflict.declaration_a
        if self.strategy in {
            constants.STRATEGY_PREFER_SECOND,
            constants.STRATEGY_PREFER_STYLE2,
            constants.STRATEGY_SAFE,
            constants.STRATEGY_AGGRESSIVE,
            constants.STRATEGY_PREFER_LAST_DEFINED,
        }:
            return conflict.declaration_b
        return conflict.declaration_b