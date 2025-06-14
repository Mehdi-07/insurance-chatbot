# In app/middleware.py
import os # Make sure os is imported
from functools import wraps
from flask import request, abort
from loguru import logger

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # --- THIS IS THE FIX ---
        # Read the key directly from the system environment variables set by Render.
        expected_api_key = os.getenv('WIDGET_API_KEY')
        # --- END FIX ---
        
        provided_api_key = request.headers.get('X-API-Key')
        
        # We can remove the debug logging now
        
        if not expected_api_key or not provided_api_key or provided_api_key != expected_api_key:
            abort(401, description="Unauthorized: Invalid or missing API Key.")
        
        return f(*args, **kwargs)
    return decorated_function