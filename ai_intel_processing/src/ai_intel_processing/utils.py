import logging
import sys
import json
from typing import Any

class StructuredMessage:
    def __init__(self, message: str, **kwargs: Any):
        self.message = message
        self.kwargs = kwargs

    def __str__(self) -> str:
        return json.dumps({"message": self.message, **self.kwargs})

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a structured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Helper for logging
def log_struct(logger: logging.Logger, level: int, message: str, **kwargs):
    if logger.isEnabledFor(level):
        logger.log(level, StructuredMessage(message, **kwargs))
