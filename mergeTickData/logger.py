#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import logging
import logging.config
import os
from datetime import date

reload(sys)
sys.setdefaultencoding("utf-8")

PATH = "log/"
# "format": "%(asctime)s [%(levelname)s] [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] - %(message)s"
XTLS_LOGGING_CONF = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": PATH + "info-" + date.today().isoformat() + ".log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": PATH + "errors-" + date.today().isoformat() + ".log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }
    },
    'loggers': {
        "": {
            "level": "INFO",
            "handlers": ["console", "info_file_handler", "error_file_handler"]
        }
    }
}


def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)


assure_path_exists(PATH)

default_level = logging.INFO,
logging.config.dictConfig(XTLS_LOGGING_CONF)

logger = logging


def get_logger(filename):
    return logging.getLogger(filename)
