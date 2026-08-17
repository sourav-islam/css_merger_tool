from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from merger.css_merger_engine import constants


@dataclass
class AppConfig:
    input_dir: Path = Path(constants.DEFAULT_INPUT_DIR)
    output_dir: Path = Path(constants.DEFAULT_OUTPUT_DIR)
    style1_filename: str = constants.DEFAULT_STYLE1_FILENAME
    style2_filename: str = constants.DEFAULT_STYLE2_FILENAME
    strategy: str = constants.DEFAULT_STRATEGY
    log_level: str = constants.DEFAULT_LOG_LEVEL

    @property
    def style1_path(self) -> Path:
        return self.input_dir / self.style1_filename

    @property
    def style2_path(self) -> Path:
        return self.input_dir / self.style2_filename

    @property
    def merged_css_path(self) -> Path:
        return self.output_dir / constants.MERGED_CSS_FILENAME

    @property
    def conflicts_path(self) -> Path:
        return self.output_dir / constants.CONFLICTS_FILENAME

    @property
    def report_path(self) -> Path:
        return self.output_dir / constants.REPORT_FILENAME

    def validate(self) -> None:
        if self.strategy not in constants.VALID_STRATEGIES:
            raise ValueError(f"Invalid strategy: {self.strategy}")
        if not self.style1_path.exists():
            raise FileNotFoundError(f"Missing input file: {self.style1_path}")
        if not self.style2_path.exists():
            raise FileNotFoundError(f"Missing input file: {self.style2_path}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_args(cls, args=None) -> "AppConfig":
        import argparse

        parser = argparse.ArgumentParser(prog="css-merger")
        parser.add_argument("--input-dir", default=constants.DEFAULT_INPUT_DIR)
        parser.add_argument("--output-dir", default=constants.DEFAULT_OUTPUT_DIR)
        parser.add_argument("--style1", default=constants.DEFAULT_STYLE1_FILENAME)
        parser.add_argument("--style2", default=constants.DEFAULT_STYLE2_FILENAME)
        parser.add_argument("--strategy", default=constants.DEFAULT_STRATEGY,
                             choices=sorted(constants.VALID_STRATEGIES))
        parser.add_argument("--log-level", default=constants.DEFAULT_LOG_LEVEL)
        parsed = parser.parse_args(args)

        return cls(
            input_dir=Path(parsed.input_dir),
            output_dir=Path(parsed.output_dir),
            style1_filename=parsed.style1,
            style2_filename=parsed.style2,
            strategy=parsed.strategy,
            log_level=parsed.log_level,
        )