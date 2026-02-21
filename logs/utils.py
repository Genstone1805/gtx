"""
Logging utility to capture all application logs to file.
"""
import logging
import os
from django.conf import settings

# Create logs directory
LOGS_DIR = os.path.join(settings.BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Log file path
LOG_FILE = os.path.join(LOGS_DIR, 'application.log')

# Get Django configured logger
logger = logging.getLogger('gtx')


def log_debug(message, name='gtx'):
    """Log debug message."""
    logging.getLogger(name).debug(message)


def log_info(message, name='gtx'):
    """Log info message."""
    logging.getLogger(name).info(message)


def log_warning(message, name='gtx'):
    """Log warning message."""
    logging.getLogger(name).warning(message)


def log_error(message, name='gtx'):
    """Log error message."""
    logging.getLogger(name).error(message)


def log_critical(message, name='gtx'):
    """Log critical message."""
    logging.getLogger(name).critical(message)


def get_client_ip(request):
    """Get client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'Unknown')


# Export logger for use in other modules
__all__ = [
    'logger', 'LOG_FILE', 'LOGS_DIR',
    'log_debug', 'log_info', 'log_warning', 
    'log_error', 'log_critical', 'get_client_ip'
]
