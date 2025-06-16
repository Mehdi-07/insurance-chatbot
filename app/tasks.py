# In app/tasks.py
import os
from loguru import logger
from rq import Queue
from redis import Redis # Import the base Redis class

# This variable will hold our Redis connection, real or fake.
redis_conn = None
# This is a placeholder queue that will be replaced if a real connection is made.
q = Queue(is_async=False, connection=Redis(host='dummy')) 

# Check if we are running in the test environment set by GitHub Actions
is_testing = os.getenv("IS_TESTING") == "True"

if is_testing:
    # For tests, use a fake in-memory Redis.
    try:
        import fakeredis
        redis_conn = fakeredis.FakeStrictRedis()
        q = Queue('default', connection=redis_conn) # Replace the dummy queue
        logger.info("--- USING FAKE REDIS FOR TESTING ---")
    except ImportError:
        logger.error("fakeredis is not installed. Tests will fail.")
        redis_conn = None
else:
    # For production on Render, connect to the real Redis service.
    from redis import from_url
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_conn = from_url(redis_url)
            q = Queue('default', connection=redis_conn) # Replace the dummy queue
            logger.info("Successfully connected to REAL Redis.")
        except Exception as e:
            logger.error(f"Could not connect to REAL Redis: {e}")
            redis_conn = None
    else:
        logger.warning("REDIS_URL not set. Redis features will be disabled.")


# The rest of your task functions do not need to change.
def slack_alert(message: str):
    logger.info(f"TASK: Sending Slack alert -> {message}")
    return f"Sent to Slack: {message}"

def twilio_sms(phone_number: str, message: str):
    logger.info(f"TASK: Sending Twilio SMS to {phone_number} -> {message}")
    return f"Sent SMS to {phone_number}"

def enqueue_notifications(lead_info: dict):
    # This check ensures we only queue tasks if we have a real or fake connection
    if redis_conn:
        message = f"New lead: {lead_info.get('name')}, Email: {lead_info.get('email')}"
        q.enqueue(slack_alert, message)
        if lead_info.get('phone'):
            q.enqueue(twilio_sms, lead_info.get('phone'), "A new lead was created.")
        logger.info("Enqueued Slack and SMS notification tasks.")
    else:
        logger.warning("Redis not connected. Skipping task queueing.")