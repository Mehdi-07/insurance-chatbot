# In app/middleware.py
import os
from functools import wraps
from flask import request, abort

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the secret key from our application's environment variables
        expected_api_key = os.getenv('WIDGET_API_KEY')
        # Get the key sent by the client in the request headers
        provided_api_key = request.headers.get('X-API-Key')

        # If the key is missing or doesn't match, block the request
        if not provided_api_key or provided_api_key != expected_api_key:
            abort(401, description="Unauthorized: Invalid or missing API Key.")

        # If the key is valid, proceed to the original route function
        return f(*args, **kwargs)
    return decorated_function