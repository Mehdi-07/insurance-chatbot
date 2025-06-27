# app/extensions.py
import os
import sys
import logging # Keep this import for the LoguruHandler bridging
from flask import Flask, jsonify
from loguru import logger # This is the loguru logger object

# --- Loguru Global Configuration ---
# Configure Loguru to write to a file and manage it.
# --- End Loguru Global Configuration ---


class LoguruHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(app: Flask):
    """
    Configures Loguru for JSON output and intercepts Flask's default loggers.
    """

    logger.remove()
    logger.add(
        sys.stdout,
        serialize=True, # Format logs as JSON
        level="INFO",
        enqueue=True
    )

    
    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)
    
    app.logger.addHandler(LoguruHandler())
    
    logger.info("Loguru logging configured and Flask's logger is intercepted.")


def init_db(app: Flask):
    """
    Initializes the database by calling the init_db function from lead_dao.
    """
    from .adapters.lead_dao import init_db as lead_dao_init_db
    with app.app_context():
        try:
            lead_dao_init_db(app)
            logger.info("Database initialization requested via lead_dao.") # Use loguru.logger
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}") #
            raise