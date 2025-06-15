# In app/middleware.py
import os
from functools import wraps
from flask import request, abort, current_app
from loguru import logger

# We will import the Redis connection from your tasks file
from app.tasks import redis_conn

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        expected_api_key = os.getenv('WIDGET_API_KEY')
        provided_api_key = request.headers.get('X-API-Key')
        if not expected_api_key or not provided_api_key or provided_api_key != expected_api_key:
            abort(401, description="Unauthorized: Invalid or missing API Key.")
        return f(*args, **kwargs)
    return decorated_function

def rate_limiter(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Use a pipeline to make our Redis commands atomic and efficient
        pipe = redis_conn.pipeline()
        # Get the user's IP address. In a production setup behind a proxy like
        # Render's, we check headers that forward the original IP.
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        key = f"rate_limit:{ip_address}"

        # Increment the key and get the new value
        pipe.incr(key, 1)
        # Set it to expire in 10 seconds
        pipe.expire(key, 10)

        # Execute the commands and get the results
        result = pipe.execute()
        request_count = result[0]

        if request_count > 5: # 5 requests per 10 seconds limit
            # Too many requests, block them.
            return abort(429, description="Rate limit exceeded.")

        # If the limit is not exceeded, proceed to the route function
        return f(*args, **kwargs)
    return decorated_function