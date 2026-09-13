import logging
import sys
import re

KEY_VALUE_PATTERN = re.compile(r'(?i)(api[_-]?key|secret|token|password|bearer\s+)[=:\s]+([\w\-]{8,})')
BEARER_PATTERN = re.compile(r'sk-[a-zA-Z0-9]{20,}')

class SanitizingFormatter(logging.Formatter):
    def format(self, record):
        orig_msg = super().format(record)
        orig_msg = KEY_VALUE_PATTERN.sub(r'\1=***REDACTED***', orig_msg)
        orig_msg = BEARER_PATTERN.sub('***REDACTED***', orig_msg)
        return orig_msg

def setup_logger(name="billinger", log_level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = SanitizingFormatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger()
