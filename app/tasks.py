# In app/tasks.py
import os
from loguru import logger
from rq import Queue

redis_conn = None
q = Queue(is_async=False)  # Dummy queue to prevent crashes

if os.getenv("IS_TESTING") == "True":
    try:
        import fakeredis
        redis_conn = fakeredis.FakeStrictRedis()
        q = Queue('default', connection=redis_conn)
        logger.info("--- INITIALIZED FAKE REDIS FOR TESTING ---")
    except ImportError:
        logger.error("fakeredis is not installed. Tests will fail.")
else:
    from redis import from_url
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_conn = from_url(redis_url)
            q = Queue('default', connection=redis_conn)
            logger.info("Successfully connected to REAL Redis.")
        except Exception as e:
            logger.error(f"Could not connect to REAL Redis: {e}")
            
# The rest of your task functions do not need to change
def slack_alert(message: str):
    logger.info(f"TASK: Sending Slack alert -> {message}")

def twilio_sms(phone_number: str, message: str):
    logger.info(f"TASK: Sending Twilio SMS to {phone_number}")

def enqueue_notifications(lead_info: dict):
    if redis_conn and q.is_async:
        message = f"New lead: {lead_info.get('name')}"
        q.enqueue(slack_alert, message)