# in app/tasks.py
import os
from loguru import logger
from redis import from_url
from rq import Queue

# Get the Redis URL from environment variables, with a fallback for local dev
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

# Establish a connection to Redis
try:
    conn = from_url(redis_url)
    # Create a queue. 'default' is the standard queue name.
    q = Queue('default', connection=conn)
    logger.info("Successfully connected to Redis and created queue.")
except Exception as e:
    logger.error(f"Could not connect to Redis: {e}")
    # If Redis isn't available, we create a 'dummy' queue for the app to not crash.
    # The 'is_async=False' means jobs will run immediately instead of being queued.
    q = Queue(is_async=False) 

def slack_alert(message: str):
    """Placeholder task for sending a Slack notification."""
    logger.info(f"TASK: Sending Slack alert -> {message}")
    # In a real app, you would have your Slack API call here.
    return f"Sent to Slack: {message}"

def twilio_sms(phone_number: str, message: str):
    """Placeholder task for sending an SMS via Twilio."""
    logger.info(f"TASK: Sending Twilio SMS to {phone_number} -> {message}")
    # In a real app, you would have your Twilio API call here.
    return f"Sent SMS to {phone_number}"

def enqueue_notifications(lead_info: dict):
    """Adds notification jobs to the Redis queue."""
    if q.is_async: # Only enqueue if we are connected to a real Redis server
        message = f"New lead: {lead_info.get('name')}, Email: {lead_info.get('email')}"
        q.enqueue(slack_alert, message)

        if lead_info.get('phone'):
            q.enqueue(twilio_sms, lead_info.get('phone'), "A new lead was created.")

        logger.info("Enqueued Slack and SMS notification tasks.")
    else:
        logger.warning("Redis not connected. Skipping task queueing.")