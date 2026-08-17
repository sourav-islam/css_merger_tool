from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from merger.css_merger_engine import utils
from merger.css_merger_engine.models import Declaration, Rule, Stylesheet

HEX_COLOR_PATTERN = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")


class Normalizer:
    def normalize_selector(self, selector: str) -> str:
        parts = [utils.collapse_whitespace(p) for p in selector.split(",")]
        parts = [re.sub(r"\s*([>+~])\s*", r" \1 ", p) for p in parts]
        return ", ".join(parts)

    def normalize_value(self, value: str) -> str:
        value = utils.collapse_whitespace(value)
        value = HEX_COLOR_PATTERN.sub(lambda m: m.group(0).lower(), value)
        value = value.replace("'", '"')
        return value

    def build_index(
        self, stylesheet: Stylesheet
    ) -> Dict[Tuple[Optional[str], str], List[Rule]]:
        index: Dict[Tuple[Optional[str], str], List[Rule]] = {}
        self._index_rules(stylesheet.rules, context=None, index=index)
        return index

    def _index_rules(
        self,
        rules: List[Rule],
        context: Optional[str],
        index: Dict[Tuple[Optional[str], str], List[Rule]],
    ) -> None:
        for rule in rules:
            if rule.is_container():
                self._index_rules(rule.nested_rules, context=rule.selector, index=index)
                continue

            key = (context, self.normalize_selector(rule.selector))
            index.setdefault(key, []).append(rule)

    def normalized_declarations(self, rule: Rule) -> Dict[str, Declaration]:
        result: Dict[str, Declaration] = {}
        for decl in rule.declarations:
            result[decl.normalized_key()] = decl
        return result