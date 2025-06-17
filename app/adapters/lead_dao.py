# In app/adapters/lead_dao.py
import os
import psycopg2
import requests
from loguru import logger
from flask import Flask

def init_db(app: Flask):
    """Initializes the PostgreSQL database with the full leads schema."""
    conn_url = os.getenv("DATABASE_URL")
    if not conn_url:
        logger.error("DATABASE_URL not set.")
        return

    try:
        conn = psycopg2.connect(conn_url)
        with conn.cursor() as cursor:
            # ADDED NEW COLUMNS FOR WIZARD DATA
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    zip_code TEXT,
                    quote_type TEXT,
                    raw_message TEXT NOT NULL,
                    coverage_category TEXT,
                    vehicle_year TEXT,
                    home_type TEXT,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        conn.commit()
        logger.info("Database initialized successfully with full schema.")
    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def save_lead(lead_data: dict):
    """Saves complete lead data to the database."""
    conn_url = os.getenv("DATABASE_URL")
    webhook_url = os.getenv("N8N_WEBHOOK_URL")

    # UPDATED SQL TO INCLUDE NEW COLUMNS
    sql = """INSERT INTO leads(name, email, phone, zip_code, quote_type, 
                               coverage_category, vehicle_year, home_type, raw_message)
             VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"""

    conn = None
    try:
        conn = psycopg2.connect(conn_url)
        with conn.cursor() as cursor:
            lead_name = lead_data.get('name') or "New Inquiry"

            cursor.execute(sql, (
                lead_name,
                lead_data.get('email'),
                lead_data.get('phone'),
                lead_data.get('zip_code'),
                lead_data.get('quote_type'),
                lead_data.get('coverage_category'),
                lead_data.get('vehicle_year'),
                lead_data.get('home_type'),
                lead_data.get('raw_message')
            ))
            lead_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Successfully saved lead with ID: {lead_id}")

            if webhook_url:
                requests.post(webhook_url, json={**lead_data, "id": lead_id, "name": lead_name}, timeout=5)
                logger.info(f"Successfully posted lead {lead_id} to n8n webhook.")

            return lead_id
    except Exception as e:
        logger.error(f"Failed to save lead: {e}")
        if conn: conn.rollback()
        return None
    finally:
        if conn: conn.close()