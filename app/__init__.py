# In app/__init__.py

import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from loguru import logger

# Import your functions and blueprints
from .extensions import configure_logging, init_db
from .routes import bp as routes_bp

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- START OF CONFIGURATION LOGIC ---
    # Set default values first
    app.config.from_mapping(
        SECRET_KEY='dev',
        TESTING=False,
    )

    if test_config is None:
        # If NOT testing, load config from environment variables set by Render
        load_dotenv() # Loads .env for local dev
        app.config.update({
            'WIDGET_API_KEY': os.getenv('WIDGET_API_KEY'),
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            # Add any other production keys here
        })
    else:
        # If testing, load the test_config dictionary
        app.config.from_mapping(test_config)
    # --- END OF CONFIGURATION LOGIC ---


    # In testing, we will use an in-memory database by default
    # and we will not initialize a real database connection.
    if app.config.get("TESTING"):
        app.config["DB_PATH"] = ":memory:"
    else:
        # In production, initialize the real database
        init_db(app)

    # Initialize other parts of the app
    configure_logging(app)
    app.register_blueprint(routes_bp)

    # Only register the generic error handler when NOT in testing
    if not app.config.get("TESTING"):
        @app.errorhandler(Exception)
        def global_handler(e):
            logger.exception(f"Unhandled exception caught by global handler: {e}")
            return jsonify({"error": "internal server error"}), 500

    return app