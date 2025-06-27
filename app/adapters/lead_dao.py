import os
import psycopg2
import requests
from loguru import logger
from flask import Flask

def init_db(app: Flask):
    """Initializes the PostgreSQL database with the full leads schema."""
    conn_url = os.getenv("DATABASE_URL")
    if not conn_url:
        logger.error("DATABASE_URL environment variable is not set.")
        return

    conn = None  # Define conn outside the try block for access in finally
    try:
        conn = psycopg2.connect(conn_url)
        with conn.cursor() as cursor:
            #schema
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
        if conn:
            conn.close()

def save_lead(lead_data: dict):
    """Saves complete lead data to the database and posts it to the n8n webhook."""
    conn_url = os.getenv("DATABASE_URL")
    webhook_url = os.getenv("N8N_WEBHOOK_URL")

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
                try:
                    # --- IMPROVEMENT 1: Explicit Payload ---
                    # This explicitly builds the data packet for n8n, ensuring all
                    # fields are included correctly every time.
                    n8n_payload = {
                        "id": lead_id,
                        "name": lead_name,
                        "email": lead_data.get('email'),
                        "phone": lead_data.get('phone'),
                        "zip_code": lead_data.get('zip_code'),
                        "quote_type": lead_data.get('quote_type'),
                        "coverage_category": lead_data.get('coverage_category'),
                        "vehicle_year": lead_data.get('vehicle_year'),
                        "home_type": lead_data.get('home_type'),
                        "raw_message": lead_data.get('raw_message'),
                        "session_id": lead_data.get('session_id')
                    }
                    requests.post(webhook_url, json=n8n_payload, timeout=5)
                    logger.info(f"Successfully posted lead {lead_id} to n8n webhook.")
                except Exception as e:
                    logger.error(f"Failed to post lead {lead_id} to n8n webhook: {e}")
            
            return lead_id
    except psycopg2.Error as e: # <-- IMPROVEMENT 2: More Specific Exception
        # By catching a specific database error, our logs will be clearer.
        logger.error(f"Database error while saving lead: {e}")
        if conn: conn.rollback()
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in save_lead: {e}")
        if conn: conn.rollback()
        
        return None
    finally:
        if conn:
            conn.close()

