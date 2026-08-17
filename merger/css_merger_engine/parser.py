from __future__ import annotations

from pathlib import Path
from typing import List

from merger.css_merger_engine import constants, utils
from merger.css_merger_engine.models import Declaration, Rule, Stylesheet


class CSSParser:
    def __init__(self, encoding: str = constants.DEFAULT_ENCODING):
        self.encoding = encoding
        self.logger = utils.setup_logger(self.__class__.__name__)

    def parse_file(self, path: Path) -> Stylesheet:
        path = Path(path)
        try:
            text = path.read_text(encoding=self.encoding)
        except FileNotFoundError:
            self.logger.error("File not found: %s", path)
            raise
        except OSError as exc:
            self.logger.error("Failed to read %s: %s", path, exc)
            raise

        self.logger.info("Parsing %s (%d bytes)", path.name, len(text))
        return self.parse_text(text, source_file=path.name)

    def parse_text(self, css_text: str, source_file: str) -> Stylesheet:
        cleaned = utils.strip_comments(css_text)
        rules = self._parse_rules(cleaned, source_file)
        self.logger.info("Parsed %d top-level rules from %s", len(rules), source_file)
        return Stylesheet(rules=rules, source_file=source_file)

    def _parse_rules(self, text: str, source_file: str) -> List[Rule]:
        rules: List[Rule] = []
        i = 0
        n = len(text)

        while i < n:
            while i < n and text[i].isspace():
                i += 1
            if i >= n:
                break

            open_pos = text.find("{", i)
            if open_pos == -1:
                break

            selector = utils.collapse_whitespace(text[i:open_pos])
            close_pos = self._find_matching_close(text, open_pos)
            line_no = text.count("\n", 0, i) + 1

            if not selector:
                i = close_pos + 1
                continue

            if utils.is_at_rule(selector):
                name = utils.at_rule_name(selector)
                if name in constants.CONTAINER_AT_RULES or name == constants.KEYFRAME_AT_RULE:
                    inner_text = text[open_pos + 1:close_pos]
                    nested = self._parse_rules(inner_text, source_file)
                    rule = Rule(
                        selector=selector,
                        nested_rules=nested,
                        is_at_rule=True,
                        source_file=source_file,
                        line_number=line_no,
                    )
                else:
                    decl_text = text[open_pos + 1:close_pos]
                    declarations = self._parse_declarations(decl_text, source_file, line_no)
                    rule = Rule(
                        selector=selector,
                        declarations=declarations,
                        is_at_rule=True,
                        source_file=source_file,
                        line_number=line_no,
                    )
            else:
                decl_text = text[open_pos + 1:close_pos]
                declarations = self._parse_declarations(decl_text, source_file, line_no)
                rule = Rule(
                    selector=selector,
                    declarations=declarations,
                    source_file=source_file,
                    line_number=line_no,
                )

            rules.append(rule)
            i = close_pos + 1

        return rules

    def _find_matching_close(self, text: str, open_pos: int) -> int:
        depth = 1
        i = open_pos + 1
        n = len(text)
        while i < n:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        self.logger.warning("Unclosed brace starting at position %d", open_pos)
        return n

    def _parse_declarations(self, decl_text: str, source_file: str, line_no: int) -> List[Declaration]:
        declarations: List[Declaration] = []
        for match in constants.DECLARATION_PATTERN.finditer(decl_text):
            prop = match.group(1).strip()
            value = match.group(2).strip()
            important = bool(constants.IMPORTANT_PATTERN.search(value))
            if important:
                value = constants.IMPORTANT_PATTERN.sub("", value).strip()
            declarations.append(
                Declaration(
                    property=prop,
                    value=value,
                    important=important,
                    source_file=source_file,
                    line_number=line_no,
                )
            )
        return declarations