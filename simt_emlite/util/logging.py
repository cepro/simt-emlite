import os
import logging
import structlog
import sys

from pathlib import Path

shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.format_exc_info,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.ExceptionPrettyPrinter(),
    structlog.processors.TimeStamper("iso"),
]

if sys.stderr.isatty():
    processors = [
        structlog.dev.ConsoleRenderer()
    ]
else:
    processors = [
        structlog.processors.JSONRenderer(),
    ]

structlog.configure(processors=shared_processors + processors)


def path_to_package_and_module(path: str):
    path_parts = Path(path).parts
    package_parts = path_parts[path_parts.index('simt_emlite'):]
    # [:-3] chops off file extension '.py'
    return os.path.join(*package_parts).replace(os.sep, '.')[:-3]


def logger_module_name(name, file=None):
    if name != '__main__' or file is None:
        return name
    return path_to_package_and_module(file)


def get_logger(name: str, python_file: str):
    return structlog.get_logger(
        module=logger_module_name(name, python_file)
    )


#
# Configure 'logging' so that logs from dependencies are somewhat consistent
# with structlog. Well this simply logs the string message of logging output
# without any structure at all.
#
# This approach is in the structlog docs here:
#   https://www.structlog.org/en/17.2.0/standard-library.html#rendering-within-structlog
#
# NOTE: We may want something better than this eventually and there are other
# solutions like wiring up logging to use JSON output.
#

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)
