# app/extensions.py
import os
import sys
import logging # Keep this import for the LoguruHandler bridging
from flask import Flask, jsonify
from loguru import logger # This is the loguru logger object

# --- Loguru Global Configuration ---
# Configure Loguru to write to a file and manage it.
# Only configure file logging if NOT in testing mode
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
    # Step 1: Remove default handlers and add our primary JSON handler.
    # This is the part from my last message.
    logger.remove()
    logger.add(
        sys.stdout,
        serialize=True, # Format logs as JSON
        level="INFO",
        enqueue=True
    )

    # Step 2: Now, redirect Flask's loggers to our configured Loguru sink.
    # This is the part you already had.
    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)
    
    app.logger.addHandler(LoguruHandler())
    
    logger.info("Loguru logging configured and Flask's logger is intercepted.")


def init_db(app: Flask):
    """
    Initializes the database by calling the init_db function from lead_dao.
    """
    # Import here to avoid potential circular dependencies if lead_dao also imports from extensions
    from .adapters.lead_dao import init_db as lead_dao_init_db
    with app.app_context():
        try:
            # Pass the app instance to lead_dao's init_db
            lead_dao_init_db(app)
            logger.info("Database initialization requested via lead_dao.") # Use loguru.logger here
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}") # Use loguru.logger here
            # For a critical dependency like DB, re-raising might be appropriate to stop app start-up
            raise