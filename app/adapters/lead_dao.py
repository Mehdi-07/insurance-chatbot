# app/adapters/lead_dao.py
import sqlite3
import os
import logging
from flask import Flask, current_app # Import current_app for accessing app context within _init

logger = logging.getLogger(__name__)

def init_db(app_or_path: Flask | str):
    """
    Initializes the SQLite database and creates the 'leads' table if it doesn't exist.
    Can be called with a Flask app instance (for app context) or a direct path.
    """
    if isinstance(app_or_path, Flask):
        app = app_or_path
    # Prefer DB_PATH from config, fallback to instance_path/leads.db
        db_path = app.config.get["DB_PATH"]
        logger.info(f"DB init: Using Flask app context. DB path: {db_path}")
    else:  # It's a string path, likely for testing or direct script
        db_path = app_or_path
        logger.info(f"DB init: Using direct path. DB path: {db_path}")

    db_folder = os.path.dirname(db_path)
    if not os.path.exists(db_folder):
        os.makedirs(db_folder, exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE, -- Email is unique, but can be NULL
                zip TEXT,
                phone TEXT,
                quote_type TEXT,
                raw_message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info(f"Database 'leads.db' initialized or already exists at {db_path}.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database at {db_path}: {e}")
        raise # Re-raise to ensure calling function knows there's a problem

# You would add functions here for saving/retrieving leads, e.g.:
# def save_lead(lead_data: dict):
#     # ... connect to db, insert data ...
#     pass
# def get_all_leads():
#     # ... connect to db, select data ...
#     pass