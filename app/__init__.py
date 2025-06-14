# In app/__init__.py

import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from loguru import logger
from .extensions import configure_logging, init_db
from .routes import bp as routes_bp

def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    # Set default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
    )

    if test_config:
        app.config.update(test_config)

    # Logic to determine database path for deployment vs. testing
    if app.config.get("TESTING"):
        app.config["DB_PATH"] = ":memory:" # Use in-memory DB for tests
    else:
        # For production/deployment, use the DATABASE_URL from Render's env
        app.config["DB_PATH"] = os.getenv('DATABASE_URL')

    # Initialize extensions
    # In testing, we don't call the real init_db to avoid external connections
    if not app.config.get("TESTING"):
        init_db(app)

    configure_logging(app)

    # Register blueprints
    app.register_blueprint(routes_bp)

    # --- THIS IS THE CRITICAL FIX ---
    # Only register the generic error handler when NOT in testing mode.
    # In testing, we want to see the real exceptions and status codes.
    if not app.config.get("TESTING"):
        @app.errorhandler(Exception)
        def global_handler(e):
            """Global error handler for production."""
            logger.exception(f"Unhandled exception caught by global handler: {e}")
            return jsonify({"error": "internal server error"}), 500
    # --- END OF FIX ---

    return app