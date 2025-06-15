# In app/tasks.py

import os
from loguru import logger
from redis import from_url
from rq import Queue

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    # RENAMED this variable for clarity
    redis_conn = from_url(redis_url)
    # USE the renamed variable here
    q = Queue('default', connection=redis_conn)
    logger.info("Successfully connected to Redis and created queue.")
except Exception as e:
    logger.error(f"Could not connect to Redis: {e}")
    # If connection fails, set redis_conn to None so other parts of the app don't crash
    redis_conn = None
    q = Queue(is_async=False)

def slack_alert(message: str):
    """Placeholder task for sending a Slack notification."""
    logger.info(f"TASK: Sending Slack alert -> {message}")
    return f"Sent to Slack: {message}"

def twilio_sms(phone_number: str, message: str):
    """Placeholder task for sending an SMS via Twilio."""
    logger.info(f"TASK: Sending Twilio SMS to {phone_number} -> {message}")
    return f"Sent SMS to {phone_number}"

def enqueue_notifications(lead_info: dict):
    """Adds notification jobs to the Redis queue."""
    # Check if the queue is actually connected to Redis before trying to use it
    if q.is_async:
        message = f"New lead: {lead_info.get('name')}, Email: {lead_info.get('email')}"
        q.enqueue(slack_alert, message)
        
        if lead_info.get('phone'):
            q.enqueue(twilio_sms, lead_info.get('phone'), "A new lead was created.")
        
        logger.info("Enqueued Slack and SMS notification tasks.")
    else:
        logger.warning("Redis not connected. Skipping task queueing.")