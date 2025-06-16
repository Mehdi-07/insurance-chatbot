# In app/tasks.py
import os
from loguru import logger
from rq import Queue

# This variable will hold our Redis connection, real or fake.
redis_conn = None

# Check for a special environment variable that we will set only during tests.
if os.getenv("IS_TESTING") == "True":
    # If testing, use a fake in-memory Redis that requires no network.
    try:
        import fakeredis
        redis_conn = fakeredis.FakeStrictRedis()
        logger.info("--- USING FAKE REDIS FOR TESTS ---")
    except ImportError:
        logger.error("fakeredis is not installed. pip install fakeredis")
        redis_conn = None
else:
    # If not testing (i.e., on Render), connect to the real Redis service.
    from redis import from_url
    redis_url = os.getenv("REDIS_URL")
    try:
        if redis_url:
            redis_conn = from_url(redis_url)
            logger.info("Successfully connected to REAL Redis.")
        else:
            logger.warning("REDIS_URL not set. Redis features will be disabled.")
    except Exception as e:
        redis_conn = None
        logger.error(f"Could not connect to REAL Redis: {e}")

# Create the queue using the connection object we just created (real or fake).
if redis_conn:
    q = Queue('default', connection=redis_conn)
else:
    # If no Redis is available, create a dummy queue that runs tasks immediately
    q = Queue(is_async=False)


# The rest of your task functions do not need to change.
def slack_alert(message: str):
    logger.info(f"TASK: Sending Slack alert -> {message}")
    return f"Sent to Slack: {message}"

def twilio_sms(phone_number: str, message: str):
    logger.info(f"TASK: Sending Twilio SMS to {phone_number} -> {message}")
    return f"Sent SMS to {phone_number}"

def enqueue_notifications(lead_info: dict):
    # This check is still good practice.
    if q and q.is_async:
        message = f"New lead: {lead_info.get('name')}, Email: {lead_info.get('email')}"
        q.enqueue(slack_alert, message)
        if lead_info.get('phone'):
            q.enqueue(twilio_sms, lead_info.get('phone'), "A new lead was created.")
        logger.info("Enqueued Slack and SMS notification tasks.")
    else:
        logger.warning("Redis not connected or in test mode. Skipping task queueing.")