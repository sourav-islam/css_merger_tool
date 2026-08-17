from __future__ import annotations

import logging

from merger.css_merger_engine import constants


def strip_comments(css_text: str) -> str:
    return constants.COMMENT_PATTERN.sub("", css_text)


def collapse_whitespace(text: str) -> str:
    return constants.WHITESPACE_PATTERN.sub(" ", text).strip()


def is_at_rule(selector: str) -> bool:
    return bool(constants.AT_RULE_PATTERN.match(selector.strip()))


def at_rule_name(selector: str) -> str:
    match = constants.AT_RULE_PATTERN.match(selector.strip())
    return match.group(0) if match else ""


def setup_logger(name: str, level: str = constants.DEFAULT_LOG_LEVEL) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(constants.LOG_FORMAT, constants.LOG_DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    return logger