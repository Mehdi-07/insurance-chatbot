# app/extensions.py
import os
import logging # Keep this import for the LoguruHandler bridging
from flask import Flask, jsonify
from loguru import logger # This is the loguru logger object

# --- Loguru Global Configuration ---
# Configure Loguru to write to a file and manage it.
# Only configure file logging if NOT in testing mode
if os.getenv("TESTING") != "True":
    os.makedirs("logs", exist_ok=True)  # Ensure the logs directory exists
    logger.add("logs/app.log", rotation="1 MB", enqueue=True, level="INFO")
# --- End Loguru Global Configuration ---


def configure_logging(app: Flask):
    """
    Configures Flask's default logger to use Loguru handlers.
    This ensures app.logger messages also go through Loguru.
    """
    # Remove all existing handlers from Flask's default logger
    # This is crucial to prevent duplicate log messages if Flask adds its own handlers
    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)

    # Add Loguru's handler to Flask's app.logger
    # This redirects all messages sent to app.logger to Loguru
    app.logger.addHandler(LoguruHandler())
    # Set Flask's logger level to match Loguru's default or configured level
    app.logger.setLevel(logging.INFO) # Use logging.INFO as a standard level

    app.logger.info("Flask's default logger now handled by Loguru.")


# This helper class bridges Flask's standard logging to Loguru
# It needs the standard 'logging' module, hence the 'import logging' above.
class LoguruHandler(logging.Handler):
    def emit(self, record):
        try:
            # Attempt to map standard logging levels to Loguru's levels
            level = logger.level(record.levelname).name
        except ValueError:
            # Fallback if a direct mapping isn't found
            level = record.levelname

        # Determine the correct frame to get the source file/line for Loguru
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Use Loguru's logging capabilities
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


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