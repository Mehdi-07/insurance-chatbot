# In app/adapters/lead_dao.py
import os
import psycopg2
import requests  # <-- We use requests to call the webhook
from loguru import logger
# We no longer import from app.tasks
# from app.tasks import enqueue_notifications 

# The init_db function is correct and does not need to change.
def init_db(app):
    # ... (this function is fine as is) ...
    conn_url = os.getenv("DATABASE_URL")
    if not conn_url:
        logger.error("DATABASE_URL environment variable is not set.")
        return
    # ... etc ...

def save_lead(lead_data: dict):
    """Saves lead data to the database and posts it to the n8n webhook."""
    conn_url = os.getenv("DATABASE_URL")
    webhook_url = os.getenv("N8N_WEBHOOK_URL") # <-- Get the n8n URL
    sql = """INSERT INTO leads(name, email, zip_code, phone, quote_type, raw_message)
             VALUES(%s, %s, %s, %s, %s, %s) RETURNING id;"""
    
    conn = None
    try:
        conn = psycopg2.connect(conn_url)
        with conn.cursor() as cursor:
            cursor.execute(sql, (
                lead_data.get('name'),
                lead_data.get('email'),
                lead_data.get('zip_code'),
                lead_data.get('phone'),
                lead_data.get('quote_type'),
                lead_data.get('raw_message')
            ))
            lead_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Successfully saved lead with ID: {lead_id}")

            # --- THIS IS THE NEW LOGIC THAT REPLACES THE OLD ONE ---
            if webhook_url:
                try:
                    # Send the lead data to the n8n webhook
                    requests.post(webhook_url, json=lead_data, timeout=5)
                    logger.info(f"Successfully posted lead {lead_id} to n8n webhook.")
                except Exception as e:
                    logger.error(f"Failed to post lead {lead_id} to n8n webhook: {e}")
            else:
                logger.warning("N8N_WEBHOOK_URL not set. Skipping webhook post.")
            # --- END OF NEW LOGIC ---

            return lead_id
    except Exception as e:
        logger.error(f"Failed to save lead: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()