# In app/__init__.py

import os
import secrets
from datetime import datetime
from flask import Flask, jsonify, session
from dotenv import load_dotenv
from loguru import logger

# Import your functions, blueprints, and the redis_conn
from .extensions import configure_logging, init_db
from .routes import bp as routes_bp
from .tasks import redis_conn # <-- IMPORTANT IMPORT

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    load_dotenv()

    # --- ROBUST CONFIGURATION ---
    # Set default values for local development
    app.config.from_mapping(
        SECRET_KEY='dev',
        TESTING=False
    )

    if test_config is None:
        # If NOT testing, load config from Render's environment variables
        app.config.update({
            'WIDGET_API_KEY': os.getenv('WIDGET_API_KEY'),
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'REDIS_URL': os.getenv('REDIS_URL')
            # Add other production keys here as needed
        })
    else:
        # If testing, load the test_config dictionary
        app.config.from_mapping(test_config)
    # --- END CONFIGURATION ---


    # --- ADD SESSION HANDLING LOGIC ---
    @app.before_request
    def init_session():
        """Create a unique, secure session for each user."""
        if not session.get('uid'):
            # Create a new session ID
            session['uid'] = secrets.token_urlsafe(16)
            # If we have a Redis connection, create a hash for this new session
            if redis_conn:
                session_key = f"ctx:{session['uid']}"
                redis_conn.hset(session_key, mapping={
                    "created": datetime.utcnow().isoformat(),
                    "current_node": "start" # All conversations start at the 'start' node
                })
                # Set the session to expire in 7 days, per your plan
                redis_conn.expire(session_key, 60 * 60 * 24 * 7)
    # --- END SESSION LOGIC ---


    # Initialize the database only when not testing
    if not app.config.get("TESTING"):
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