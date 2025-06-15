# In app/middleware.py

import os
from functools import wraps
from flask import request, abort
from loguru import logger

# This import will now work correctly
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
        # If the Redis connection failed on startup, bypass the rate limiter
        if not redis_conn:
            logger.warning("Redis connection not available, skipping rate limiter.")
            return f(*args, **kwargs)

        pipe = redis_conn.pipeline()
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        key = f"rate_limit:{ip_address}"
        
        pipe.incr(key, 1)
        pipe.expire(key, 10)
        result = pipe.execute()
        request_count = result[0]

        if request_count > 5: # 5 requests per 10 seconds limit
            return abort(429, description="Rate limit exceeded.")
        
        return f(*args, **kwargs)
    return decorated_function