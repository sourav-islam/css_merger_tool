from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Declaration:
    property: str
    value: str
    important: bool = False
    source_file: Optional[str] = None
    line_number: Optional[int] = None

    def as_css(self) -> str:
        suffix = " !important" if self.important else ""
        return f"{self.property}: {self.value}{suffix};"

    def normalized_key(self) -> str:
        return self.property.strip().lower()


@dataclass
class Rule:
    selector: str
    declarations: List[Declaration] = field(default_factory=list)
    nested_rules: List["Rule"] = field(default_factory=list)
    is_at_rule: bool = False
    source_file: Optional[str] = None
    line_number: Optional[int] = None

    def is_container(self) -> bool:
        return self.is_at_rule and bool(self.nested_rules)

    def normalized_selector(self) -> str: #div      .btn => div .btn
        return " ".join(self.selector.split())


@dataclass
class Stylesheet:
    rules: List[Rule] = field(default_factory=list)
    source_file: Optional[str] = None

    def __len__(self) -> int:
        return len(self.rules)

    def all_rules_flat(self) -> List[Rule]:
        flat: List[Rule] = []

        def _walk(rules: List[Rule]) -> None:
            for rule in rules:
                flat.append(rule)
                if rule.nested_rules:
                    _walk(rule.nested_rules)

        _walk(self.rules)
        return flat


@dataclass
class Conflict:
    selector: str
    property: str
    declaration_a: Declaration
    declaration_b: Declaration
    context: Optional[str] = None # context in which the conflict occurred
    resolution: Optional[str] = None #merger decide keep first or second store here

    def describe(self) -> str: # describe creates a human-readable description of the conflict
        ctx = f" (within {self.context})" if self.context else ""
        return (
            f"Selector '{self.selector}'{ctx}: property '{self.property}' "
            f"differs — {self.declaration_a.source_file}='{self.declaration_a.value}' "
            f"vs {self.declaration_b.source_file}='{self.declaration_b.value}'"
        )


@dataclass
class ComparisonEntry:  # comparator needs a result container
    context: Optional[str]
    selector: str
    only_in_a: List[Declaration] = field(default_factory=list)
    only_in_b: List[Declaration] = field(default_factory=list)
    matching: List[Declaration] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)