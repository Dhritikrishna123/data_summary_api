import logging
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

class StructuredFormatter(logging.Formatter):
    """ custom formatter for structure logging """
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat()+ 'z',
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'funcName': record.funcName,
            'line': record.lineno,
        }

        # add extra fields if present
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)

        return json.dumps(log_entry)


def setup_logging():
    """ configure logging """

    # create logger
    logger = logging.getLogger('data_summary_api')
    logger.setLevel(logging.INFO)

    # remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())

    # file handler for errors
    file_handler = logging.FileHandler( filename='data_summary_api_app.log',mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # prevent duplicate logs
    logger.propagate = False

    return logger

