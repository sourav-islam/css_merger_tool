from __future__ import annotations

from pathlib import Path

from merger.css_merger_engine import constants, utils
from merger.css_merger_engine.config import AppConfig
from merger.css_merger_engine.models import Rule, Stylesheet

INDENT_UNIT = "  "


class CSSWriter:
    def __init__(self, encoding: str = constants.DEFAULT_ENCODING):
        self.encoding = encoding
        self.logger = utils.setup_logger(self.__class__.__name__)

    def render(self, stylesheet: Stylesheet) -> str:
        return self._render_rules(stylesheet.rules, indent=0)

    def write_css(self, stylesheet: Stylesheet, path: Path) -> None:
        self._write_text(path, self.render(stylesheet))

    def write_text(self, content: str, path: Path) -> None:
        self._write_text(path, content)

    def write_all(self, merged: Stylesheet, conflicts_text: str, report_text: str, config: AppConfig) -> None:
        self.write_css(merged, config.merged_css_path)
        self.write_text(conflicts_text, config.conflicts_path)
        self.write_text(report_text, config.report_path)

    def _render_rules(self, rules, indent: int) -> str:
        pad = INDENT_UNIT * indent
        lines = []
        for rule in rules:
            lines.append(f"{pad}{rule.selector} {{")
            if rule.is_container():
                lines.append(self._render_rules(rule.nested_rules, indent + 1))
            else:
                for decl in rule.declarations:
                    lines.append(f"{pad}{INDENT_UNIT}{decl.as_css()}")
            lines.append(f"{pad}}}")
            lines.append("")
        return "\n".join(lines)

    def _write_text(self, path: Path, content: str) -> None:
        path = Path(path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=self.encoding)
            self.logger.info("Wrote %s (%d bytes)", path, len(content))
        except OSError as exc:
            self.logger.error("Failed to write %s: %s", path, exc)
            raise