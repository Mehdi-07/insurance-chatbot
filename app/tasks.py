# In app/tasks.py
import os
from loguru import logger
from rq import Queue
from redis import Redis # Import the base Redis class

# --- This is the corrected, robust initialization ---

# This variable will hold our Redis connection, real or fake.
redis_conn = None
# Start with a dummy queue that does nothing. We provide a dummy connection
# that will never be used, just to satisfy the constructor.
q = Queue(is_async=False, connection=Redis(host='unreachable')) 

# Check for the testing environment variable set by the GitHub Action
is_testing = os.getenv("IS_TESTING") == "True"

if is_testing:
    # For tests, use a fake in-memory Redis.
    try:
        import fakeredis
        redis_conn = fakeredis.FakeStrictRedis()
        q = Queue('default', connection=redis_conn) # Replace the dummy queue with the fake one
        logger.info("--- INITIALIZED FAKE REDIS FOR TESTING ---")
    except ImportError:
        logger.error("fakeredis is not installed. Tests will fail.")
else:
    # For production on Render, connect to the real Redis service.
    from redis import from_url
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_conn = from_url(redis_url)
            q = Queue('default', connection=redis_conn) # Replace the dummy queue with the real one
            logger.info("Successfully connected to REAL Redis.")
        except Exception as e:
            logger.error(f"Could not connect to REAL Redis: {e}")
            
# The rest of your functions below do not need to change.
# They will correctly use the 'q' object, which is now guaranteed to be valid.

def slack_alert(message: str):
    logger.info(f"TASK: Sending Slack alert -> {message}")
    return f"Sent to Slack: {message}"

def twilio_sms(phone_number: str, message: str):
    logger.info(f"TASK: Sending Twilio SMS to {phone_number} -> {message}")
    return f"Sent SMS to {phone_number}"

def enqueue_notifications(lead_info: dict):
    if redis_conn and q.is_async:
        message = f"New lead: {lead_info.get('name')}, Email: {lead_info.get('email')}"
        q.enqueue(slack_alert, message)
        if lead_info.get('phone'):
            q.enqueue(twilio_sms, lead_info.get('phone'), "A new lead was created.")
        logger.info("Enqueued Slack and SMS notification tasks.")
    else:
        logger.warning("Redis not connected or in test mode. Skipping task queueing.")