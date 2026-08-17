import re

DEFAULT_ENCODING = "utf-8"

DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "output"

DEFAULT_STYLE1_FILENAME = "style1.css"
DEFAULT_STYLE2_FILENAME = "style2.css"

MERGED_CSS_FILENAME = "merged.css"
CONFLICTS_FILENAME = "conflicts.txt"
REPORT_FILENAME = "report.txt"

CONTAINER_AT_RULES = {"@media", "@supports", "@document", "@layer"}
FLAT_AT_RULES = {"@font-face", "@page"}
KEYFRAME_AT_RULE = "@keyframes"

COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
IMPORTANT_PATTERN = re.compile(r"!\s*important\s*$", re.IGNORECASE)

DECLARATION_PATTERN = re.compile(
    r"([a-zA-Z\-\_\*][a-zA-Z0-9\-\_]*)\s*:\s*([^;{}]+);?"
)

AT_RULE_PATTERN = re.compile(r"^@[a-zA-Z\-]+")

WHITESPACE_PATTERN = re.compile(r"\s+")

STRATEGY_PREFER_FIRST = "prefer_first"
STRATEGY_PREFER_SECOND = "prefer_second"
STRATEGY_PREFER_LAST_DEFINED = "prefer_last_defined"
STRATEGY_PREFER_STYLE1 = "prefer_style1"
STRATEGY_PREFER_STYLE2 = "prefer_style2"
STRATEGY_SAFE = "safe"
STRATEGY_AGGRESSIVE = "aggressive"

VALID_STRATEGIES = {
    STRATEGY_PREFER_FIRST,
    STRATEGY_PREFER_SECOND,
    STRATEGY_PREFER_LAST_DEFINED,
    STRATEGY_PREFER_STYLE1,
    STRATEGY_PREFER_STYLE2,
    STRATEGY_SAFE,
    STRATEGY_AGGRESSIVE,
}

DEFAULT_STRATEGY = STRATEGY_PREFER_STYLE2

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = "INFO"