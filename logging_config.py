"""Centralized logging configuration for the application."""

import logging


def configure_logging(level=logging.INFO, format_string=None):
    """
    Configure logging for the application.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string (uses default if None)
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=level,
        format=format_string
    )
