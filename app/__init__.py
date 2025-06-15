# app/__init__.py
import os
from flask import Flask, jsonify
from loguru import logger

# Import your functions and blueprints
from .extensions import configure_logging, init_db
from .routes import bp as routes_bp

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- CONFIGURATION SETUP ---
    # 1. Set default values first
    app.config.update(
        SECRET_KEY='dev',
        TESTING=False,
        DB_PATH=':memory:'
    )
    
    # 2. Apply test configuration if provided
    if test_config is not None:
        app.config.update(test_config)
    
    # 3. For non-testing environments, load from actual environment variables
    if not app.config['TESTING']:
        # Directly use environment variables without dotenv
        app.config.setdefault('WIDGET_API_KEY', os.getenv('WIDGET_API_KEY'))
        app.config.setdefault('DATABASE_URL', os.getenv('DATABASE_URL'))
    else:
        # In testing, ensure we don't accidentally use production values
        app.config.setdefault('WIDGET_API_KEY', 'test-key-not-set')
        app.config.setdefault('DATABASE_URL', 'sqlite:///:memory:')

    # --- DATABASE INITIALIZATION ---
    if not app.config['TESTING']:
        init_db(app)

    # --- EXTENSIONS SETUP ---
    configure_logging(app)
    app.register_blueprint(routes_bp)

    # --- ERROR HANDLING ---
    if not app.config['TESTING']:
        @app.errorhandler(Exception)
        def global_handler(e):
            logger.exception(f"Unhandled exception caught by global handler: {e}")
            return jsonify({"error": "internal server error"}), 500
    
    # --- HEALTH CHECK ENDPOINT ---
    @app.route('/readyz')
    def readiness_check():
        """Application readiness check for Kubernetes"""
        # Add any additional checks here (database connection, etc.)
        return jsonify(status="ready"), 200
    
    return app