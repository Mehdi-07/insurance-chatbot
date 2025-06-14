# In app/middleware.py
import os
from functools import wraps
# We need to import 'current_app' from Flask
from flask import request, abort, current_app

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # --- THIS IS THE FIX ---
        # Read the key from the application's config, not the system environment
        expected_api_key = current_app.config.get('WIDGET_API_KEY')
        # --- END FIX ---

        provided_api_key = request.headers.get('X-API-Key')

        # Check if either key is missing, or if they don't match
        if not expected_api_key or not provided_api_key or provided_api_key != expected_api_key:
            abort(401, description="Unauthorized: Invalid or missing API Key.")

        # If the keys match, proceed to the original route function
        return f(*args, **kwargs)
    return decorated_function