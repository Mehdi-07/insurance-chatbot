# In app/__init__.py

import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from loguru import logger

# We need to import the functions to initialize them
from .extensions import configure_logging, init_db
from .routes import bp as routes_bp

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- 1. SET CONFIGURATION ---
    # The configuration is loaded in a specific order:
    # a. Default values are set first.
    # b. Values from environment variables (like on Render) are loaded next, overriding defaults.
    # c. Test-specific config is loaded last, overriding everything else if it exists.
    
    app.config.from_mapping(
        # Set default values
        SECRET_KEY='dev',
        TESTING=False,
        # Default to a local SQLite file if DATABASE_URL is not set
        DATABASE_URL=f"sqlite:///{os.path.join(app.instance_path, 'app.db')}",
    )

    # This will find and load variables from a .env file for local development
    load_dotenv()
    
    # Update the config from environment variables if they exist
    # This is the key part that loads your Render secrets into Flask's config
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'REDIS_URL': os.getenv('REDIS_URL'),
        'WIDGET_API_KEY': os.getenv('WIDGET_API_KEY'),
        'N8N_WEBHOOK_URL': os.getenv('N8N_WEBHOOK_URL'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY')
    })
    
    if test_config:
        # Load the test config if passed in, overriding production settings
        app.config.update(test_config)

    # --- 2. INITIALIZE EXTENSIONS AND BLUEPRINTS ---
    configure_logging(app)
    init_db(app) # The init_db function needs the DATABASE_URL from the config
    app.register_blueprint(routes_bp)

    # --- 3. REGISTER ERROR HANDLERS ---
    # Only register the generic error handler when NOT in testing
    if not app.config.get("TESTING"):
        @app.errorhandler(Exception)
        def global_handler(e):
            logger.exception(f"Unhandled exception caught by global handler: {e}")
            return jsonify({"error": "internal server error"}), 500

    return app