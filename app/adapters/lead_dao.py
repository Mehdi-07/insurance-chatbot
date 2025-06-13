# app/adapters/lead_dao.py
import os
import psycopg2 # Use the new PostgreSQL driver
from flask import Flask
from ..tasks import enqueue_notifications
from loguru import logger

def init_db(app: Flask):
    """Initializes the PostgreSQL database and creates the 'leads' table."""
    conn_url = os.getenv("DATABASE_URL")

    if not conn_url:
        logger.error("DATABASE_URL environment variable is not set. Cannot initialize database.")
        return

    logger.info("Attempting to connect to PostgreSQL database...")
    try:
        conn = psycopg2.connect(conn_url)
        with conn.cursor() as cursor:
            # Use PostgreSQL-compatible data types
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    zip_code TEXT,
                    phone TEXT,
                    quote_type TEXT,
                    raw_message TEXT NOT NULL,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}")
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()

# Your other functions like 'save_lead' will also need to be updated.
# Here is an example of how 'save_lead' would look:
def save_lead(lead_data: dict):
    conn_url = os.getenv("DATABASE_URL")
    sql = """INSERT INTO leads(name, email, zip_code, phone, quote_type, raw_message)
             VALUES(%s, %s, %s, %s, %s, %s) RETURNING id;"""
    
    conn = None
    try:
        conn = psycopg2.connect(conn_url)
        with conn.cursor() as cursor:
            cursor.execute(sql, (
                lead_data.get('name'),
                lead_data.get('email'),
                lead_data.get('zip'),
                lead_data.get('phone'),
                lead_data.get('quote_type'),
                lead_data.get('raw_message')
            ))
            lead_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Successfully saved lead with ID: {lead_id}")
            enqueue_notifications(lead_data)
            return lead_id
    except Exception as e:
        logger.error(f"Failed to save lead: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()