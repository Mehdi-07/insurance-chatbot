# In app/middleware.py
import os
from functools import wraps
# We MUST import 'current_app' to access the application's config
from flask import request, abort, current_app
from loguru import logger

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # --- THIS IS THE CORRECT, FINAL LOGIC ---
        # Read the key from the currently running Flask application's config.
        # This works for both tests and production on Render.
        expected_api_key = current_app.config.get('WIDGET_API_KEY')
        
        provided_api_key = request.headers.get('X-API-Key')
        
        if not expected_api_key or not provided_api_key or provided_api_key != expected_api_key:
            abort(401, description="Unauthorized: Invalid or missing API Key.")
        
        return f(*args, **kwargs)
    return decorated_function