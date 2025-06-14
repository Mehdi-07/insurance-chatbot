# In app/middleware.py
import os
from functools import wraps
from flask import request, abort, current_app
from loguru import logger # Make sure logger is imported

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        expected_api_key = current_app.config.get('WIDGET_API_KEY')
        provided_api_key = request.headers.get('X-API-Key')
        
        # --- ADD THIS DEBUG LOGGING ---
        # We print the keys surrounded by pipes | to easily see any extra spaces
        logger.info("--- API KEY CHECK ---")
        logger.info(f"Expected Key (from Render Env): |{expected_api_key}|")
        logger.info(f"Provided Key (from Postman):   |{provided_api_key}|")
        # --- END DEBUG LOGGING ---

        # Check if either key is missing, or if they don't match
        if not expected_api_key or not provided_api_key or provided_api_key != expected_api_key:
            logger.warning("API Key check FAILED.")
            abort(401, description="Unauthorized: Invalid or missing API Key.")
        
        logger.success("API Key check PASSED.")
        return f(*args, **kwargs)
    return decorated_function