# In app/tasks.py
import os
from loguru import logger
from rq import Queue
from redis import Redis

# This variable will hold our Redis connection, real or fake.
redis_conn = None
# This is a placeholder queue that will be replaced if a real connection is made.
q = Queue(name='default', is_async=False, connection=Redis(host='unreachable-host')) 

# Check for the testing environment variable set by your GitHub Action
if os.getenv("IS_TESTING") == "True":
    try:
        import fakeredis
        redis_conn = fakeredis.FakeStrictRedis()
        q = Queue('default', connection=redis_conn)
        logger.info("--- INITIALIZED FAKE REDIS FOR TESTING ---")
    except ImportError:
        logger.error("fakeredis is not installed. Run 'pip install fakeredis' and add to requirements.txt")
else:
    # This is the logic for production on Render
    from redis import from_url
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_conn = from_url(redis_url)
            q = Queue('default', connection=redis_conn)
            logger.info("Successfully connected to REAL Redis.")
        except Exception as e:
            logger.error(f"Could not connect to REAL Redis: {e}")

# The rest of your functions below do not need to change.
def enqueue_notifications(lead_info: dict):
    if redis_conn and q.is_async:
        logger.info(f"Enqueuing notifications for lead: {lead_info.get('name')}")
        # Your actual task enqueuing logic would go here