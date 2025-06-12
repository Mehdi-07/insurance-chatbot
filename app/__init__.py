# app/__init__.py
import os
from flask import Flask, jsonify # Ensure jsonify is imported here
from dotenv import load_dotenv
from loguru import logger # Ensure logger is imported here

# Import blueprints and extensions from relative paths
from .routes import bp as routes_bp
from .extensions import configure_logging, init_db

def create_app(test_config: dict | None = None) -> Flask:
    # Load environment variables early in the app lifecycle
    load_dotenv()

    app = Flask(__name__)

    # Apply configuration (e.g., from a config file or test_config)
    if test_config:
        app.config.update(test_config)

    # Configure logging for the application using Loguru
    configure_logging(app)

    # Initialize the database (creates leads.db if it doesn't exist)
    init_db(app)

    # Register blueprints to organize routes
    app.register_blueprint(routes_bp)

    # Global error handler for all unhandled exceptions
    @app.errorhandler(Exception)
    def global_handler(e):
        """
        Global error handler for all unhandled exceptions in the application.
        Logs the exception and returns a generic internal server error response.
        """
        # Log the exception with traceback using loguru's logger
        logger.exception(f"Unhandled exception caught by global handler: {e}")
        # Return a generic JSON error response to the client
        return jsonify({"error": "internal server error"}), 500

    return app