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

    # --- 1. Set Default Configuration ---
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        # Set the default database path for production/development
        DB_PATH=os.path.join(app.instance_path, 'leads.db')
    )

    if test_config:
        app.config.update(test_config)

    # --- 2. Override Database for Testing (CRITICAL FIX) ---
    if app.config.get("TESTING"):
        # For tests, set the DB_PATH to the special in-memory string
        app.config["DB_PATH"] = ":memory:"

    # --- 3. Initialize App ---
    configure_logging(app)
    init_db(app) # This will now use the correct DB_PATH
    app.register_blueprint(routes_bp)

    @app.errorhandler(Exception)
    def global_handler(e):
        logger.exception(f"Unhandled exception caught by global handler: {e}")
        return jsonify({"error": "internal server error"}), 500

    return app