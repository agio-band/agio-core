import re
import shlex
from pathlib import Path
from logging import *
from logging.config import dictConfig
import os
import sys
from . import env_names


def debug_flag_is_set():
    first_cmd = ' '.join(sys.argv).split('--')[0]
    first_cmd_args = shlex.split(re.split(r'\s\b\w+\b', first_cmd)[0])
    return '--debug' in first_cmd_args


DEBUG_MODE = bool(os.getenv("DEBUG") or os.getenv(env_names.DEBUG)) or debug_flag_is_set()
if DEBUG_MODE:
    print(" Debug mode is on ".center(40, '='), flush=True) #type: ignore
USER_PREF_DIR = Path(os.getenv("USER_PREF_DIR", "~/.agio")).expanduser().resolve()
DEFAULT_LOG_DIR = Path(USER_PREF_DIR, "logs").expanduser().resolve()
# default level
DEFAULT_LEVEL = DEBUG if DEBUG_MODE else (os.getenv(env_names.LOG_LEVEL) or INFO)
DEFAULT_LEVEL_NAME = getLevelName(DEFAULT_LEVEL)
DEFAULT_FILE_LEVEL = DEBUG if DEBUG_MODE else (os.getenv(env_names.FILE_LOG_LEVEL) or WARNING)
# file paths
LOG_DIR = Path(os.getenv(env_names.LOG_DIR) or DEFAULT_LOG_DIR).expanduser().resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file_prefix = os.getenv(env_names.LOG_FILE_PREFIX, "")
LOG_FILE = LOG_DIR / (log_file_prefix + "stdout.log")
ERROR_LOG_FILE = LOG_DIR / (log_file_prefix + "stderr.log")
DEBUG_LOG_FILE = LOG_DIR / (log_file_prefix + "debug.log")
FILE_COUNT = 10
# # maximum file size
FILE_SIZE_MB = float(os.getenv(env_names.LOG_FILE_SIZE, 10))  # 10 Mb
FILE_SIZE = int(FILE_SIZE_MB * 1024 * 1024)
# # max file count
MESSAGE_FORMAT = (
    os.getenv(env_names.LOGGING_MESSAGE_FORMAT)
    or "%(asctime)s | %(levelname)-8s | %(name)-50s | %(lineno)-4d  | %(message)s"
)
MESSAGE_FORMAT_CONSOLE = (
    os.getenv(env_names.LOGGING_MESSAGE_FORMAT_CONSOLE) or "%(levelname)-8s | %(name)-50s | %(lineno)-4d  | %(message)s"
)
DATETIME_FORMAT = os.getenv(env_names.LOGGING_DATETIME_FORMAT) or "%Y.%m.%d %H:%M:%S"

disabled_loggers = [
    "urllib3.connectionpool"
]
DISABLED_LOGGERS = os.getenv(env_names.DISABLED_LOGGERS)
if DISABLED_LOGGERS:
    disabled_loggers.extend(DISABLED_LOGGERS.split(","))

LOG_SETTINGS = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": DEFAULT_LEVEL,
        "handlers": [
            "console",
            "file",
            "file_errors",
        ],
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": DEFAULT_LEVEL,
            "formatter": "console",
            "stream": "ext://sys.stdout",   # for streaming to stdout instead stderr
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": DEFAULT_FILE_LEVEL,
            "formatter": "detailed",
            "filename": LOG_FILE if not DEBUG_MODE else DEBUG_LOG_FILE,
            "mode": "a",
            "maxBytes": FILE_SIZE,
            "backupCount": FILE_COUNT,
        },
        "file_errors": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": ERROR,
            "formatter": "detailed",
            "filename": ERROR_LOG_FILE,
            "mode": "a",
            "maxBytes": FILE_SIZE,
            "backupCount": FILE_COUNT,
        },
    },
    "formatters": {
        "detailed": {
            "format": MESSAGE_FORMAT,
            "datefmt": DATETIME_FORMAT,
        },
        "info": {
            "format": MESSAGE_FORMAT,
            "datefmt": DATETIME_FORMAT,
        },
        "console": {
            "format": MESSAGE_FORMAT_CONSOLE,
            "datefmt": DATETIME_FORMAT,
        },
    },
    "loggers": {
        lgr: {
            "level": "CRITICAL",
            "propagate": False,
        } for lgr in disabled_loggers
    },
}
# ==== APPLY CONFIG ====
dictConfig(LOG_SETTINGS)
