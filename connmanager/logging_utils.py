"""
logging_utils.py

Utility module for setting up logging configuration for the CLI tool.
"""
import logging

def setup_logging(debug: bool = False) -> None:
    """
    Set up logging configuration for the application.

    Args:
        debug (bool): If True, set logging level to DEBUG. Otherwise, INFO.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
