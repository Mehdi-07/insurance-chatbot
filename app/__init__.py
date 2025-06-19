# In app/__init__.py
import os
import secrets
from datetime import datetime, timezone
from flask import Flask, jsonify, session
from dotenv import load_dotenv
from loguru import logger
from flask_cors import CORS

from .extensions import configure_logging
from .routes import bp as routes_bp
from .tasks import redis_conn
from .services.wizard_service import load_flow
from .services.zip_validator import load_zips

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True, static_folder=None)

    CORS(app)
    load_dotenv()

    # --- Configuration ---
    app.config.from_mapping(SECRET_KEY=os.getenv('SECRET_KEY', 'dev'), TESTING=False)
    if test_config:
        app.config.update(test_config)
    else:
        app.config.update({
            'WIDGET_API_KEY': os.getenv('WIDGET_API_KEY'),
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'REDIS_URL': os.getenv('REDIS_URL'),
            'N8N_WEBHOOK_URL': os.getenv('N8N_WEBHOOK_URL')
        })

    # Defer initialization until the app context is available
    with app.app_context():
        load_flow(app)
        load_zips(app)

    @app.before_request
    def init_session():
        if not session.get('uid'):
            session['uid'] = secrets.token_urlsafe(16)
            if redis_conn:
                redis_conn.hset(f"ctx:{session['uid']}", "current_node", "start")
                redis_conn.expire(f"ctx:{session['uid']}", 60 * 60 * 24 * 7)

    app.register_blueprint(routes_bp)
    configure_logging(app)
    
    if not app.config.get("TESTING"):
        @app.errorhandler(Exception)
        def global_handler(e):
            logger.exception(f"Unhandled exception caught by global handler: {e}")
            return jsonify({"error": "internal server error"}), 500

    return app