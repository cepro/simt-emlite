import os
import sys
import structlog

from pathlib import Path

shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.TimeStamper("iso"),
]

if sys.stderr.isatty():
    processors = [
        structlog.dev.ConsoleRenderer()
    ]
else:
    processors = [
        structlog.processors.JSONRenderer(),
        structlog.processors.dict_tracebacks
    ]

structlog.configure(processors=shared_processors + processors)


def path_to_package_and_module(path: str):
    path_parts = Path(path).parts
    package_parts = path_parts[path_parts.index('emlite_mediator'):]
    # [:-3] chops off file extension '.py'
    return os.path.join(*package_parts).replace(os.sep, '.')[:-3]


def logger_module_name(name, file=None):
    if name != '__main__' or file == None:
        return name
    return path_to_package_and_module(file)


def get_logger(name: str, python_file: str):
    return structlog.get_logger(module=logger_module_name(name, python_file)
                                )
