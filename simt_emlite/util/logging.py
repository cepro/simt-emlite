import logging
import os
import sys
from pathlib import Path
from typing import Any, List

import structlog


def suppress_noisy_loggers() -> None:
    """Suppress verbose debug logs from noisy third-party libraries."""
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("h2").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# Configure standard library logging FIRST
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)
suppress_noisy_loggers()

shared_processors: List[Any] = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.format_exc_info,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.ExceptionPrettyPrinter(),
    structlog.processors.TimeStamper("iso"),
]

processors: List[Any]
if sys.stderr.isatty():
    processors = [structlog.dev.ConsoleRenderer()]
else:
    processors = [
        structlog.processors.JSONRenderer(),
    ]

# This is the key change - configure structlog to use stdlib logger
structlog.configure(
    processors=shared_processors + processors,
    logger_factory=structlog.stdlib.LoggerFactory(),  # Use stdlib logger
    wrapper_class=structlog.stdlib.BoundLogger,  # Use stdlib wrapper
    cache_logger_on_first_use=True,
)


def path_to_package_and_module(path: str) -> str:
    path_parts = Path(path).parts
    package_parts = path_parts[path_parts.index("simt_emlite") :]
    # [:-3] chops off file extension '.py'
    return os.path.join(*package_parts).replace(os.sep, ".")[:-3]


def logger_module_name(name: str, file: str | None = None) -> str:
    if name != "__main__" or file is None:
        return name
    return path_to_package_and_module(file)


def get_logger(name: str, python_file: str) -> Any:
    return structlog.get_logger(module=logger_module_name(name, python_file))
