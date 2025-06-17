# In app/__init__.py
import os
import secrets
from datetime import datetime, timezone
from flask import Flask, jsonify, session
from dotenv import load_dotenv
from loguru import logger

# Import functions/blueprints that will be initialized/registered
from .extensions import configure_logging, init_db
from .routes import bp as routes_bp
from .tasks import redis_conn
from .services.wizard_service import load_flow
from .services.zip_validator import load_zips

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    load_dotenv()

    # --- Configuration ---
    # Load default config, then override with environment variables, then test_config
    app.config.from_mapping(SECRET_KEY='dev', TESTING=False)
    app.config.update({
        'WIDGET_API_KEY': os.getenv('WIDGET_API_KEY'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'REDIS_URL': os.getenv('REDIS_URL')
    })
    if test_config:
        app.config.from_mapping(test_config)
    # --- End Configuration ---

    # --- Defer initialization until app context is available ---
    with app.app_context():
        load_flow(app)
        load_zips(app)

    @app.before_request
    def init_session():
        if not session.get('uid'):
            session['uid'] = secrets.token_urlsafe(16)
            if redis_conn: # redis_conn is now the safe fake or real connection
                session_key = f"ctx:{session['uid']}"
                redis_conn.hset(session_key, mapping={
                    "created": datetime.now(timezone.utc).isoformat(),
                    "current_node": "start"
                })
                redis_conn.expire(session_key, 60 * 60 * 24 * 7)

    app.register_blueprint(routes_bp)
    configure_logging(app)
    
    if not app.config.get("TESTING"):
        @app.errorhandler(Exception)
        def global_handler(e):
            logger.exception(f"Unhandled exception caught by global handler: {e}")
            return jsonify({"error": "internal server error"}), 500

    return app