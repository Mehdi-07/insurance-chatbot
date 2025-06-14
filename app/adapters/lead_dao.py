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

# update to fix lead error

def save_lead(lead_data: dict):
    """Saves lead data to the database and posts it to the n8n webhook."""
    conn_url = os.getenv("DATABASE_URL")
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    sql = """INSERT INTO leads(name, email, zip_code, phone, quote_type, raw_message)
             VALUES(%s, %s, %s, %s, %s, %s) RETURNING id;"""
    
    conn = None
    try:
        conn = psycopg2.connect(conn_url)
        with conn.cursor() as cursor:
            
            # --- THIS IS THE FIX ---
            # Use the provided name, or create a placeholder if it's missing.
            lead_name = lead_data.get('name') or "New Inquiry"
            # --- END OF FIX ---

            cursor.execute(sql, (
                lead_name, # Use the new variable here
                lead_data.get('email'),
                lead_data.get('zip_code'),
                lead_data.get('phone'),
                lead_data.get('quote_type'),
                lead_data.get('raw_message')
            ))
            lead_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Successfully saved lead with ID: {lead_id}")

            if webhook_url:
                try:
                    # Add the new lead ID to the data sent to n8n
                    lead_data_with_id = {**lead_data, "id": lead_id, "name": lead_name}
                    requests.post(webhook_url, json=lead_data_with_id, timeout=5)
                    logger.info(f"Successfully posted lead {lead_id} to n8n webhook.")
                except Exception as e:
                    logger.error(f"Failed to post lead {lead_id} to n8n webhook: {e}")
            else:
                logger.warning("N8N_WEBHOOK_URL not set. Skipping webhook post.")

            return lead_id
    except Exception as e:
        logger.error(f"Failed to save lead: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()