"""
Merger service that orchestrates the CSS engine.
This module should call into the existing `css_merger` package in the repo.
"""
from typing import List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MergeService:
    def __init__(self, user):
        self.user = user

    def run_merge(self, input_files: List[Path], strategy: str = "prefer_style2"):
        logger.info("Starting merge for user %s with %d files", self.user, len(input_files))
        # Placeholder: integrate existing css_merger engine modules here
        # from css_merger import parser, normalizer, comparator, merger, writer
        # parsed = [parser.parse_text(f.read_text()) for f in input_files]
        # ...
        return {
            "status": "not_implemented",
            "message": "Merger service is scaffolded. Implement integration with css_merger engine.",
        }
