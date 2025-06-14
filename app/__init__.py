# app/__init__.py
import os
from flask import Flask, jsonify # Ensure jsonify is imported here
from dotenv import load_dotenv
from loguru import logger # Ensure logger is imported here

# Import blueprints and extensions from relative paths
from .routes import bp as routes_bp
from .extensions import configure_logging, init_db

import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from loguru import logger
from .extensions import configure_logging, init_db
from .routes import bp as routes_bp # Assuming your blueprint is named 'bp' in routes.py

def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
    )

    if test_config:
        app.config.update(test_config)

    # For tests, we skip the real DB initialization.
    # A full testing setup would involve a separate test database.
    if not app.config.get("TESTING"):
        init_db(app)

    configure_logging(app)
    app.register_blueprint(routes_bp)

    if not app.config.get("TESTING"):
        @app.errorhandler(Exception)
        def global_handler(e):
            """Global error handler for production."""
            logger.exception(f"Unhandled exception caught by global handler: {e}")
            return jsonify({"error": "internal server error"}), 500

    return app