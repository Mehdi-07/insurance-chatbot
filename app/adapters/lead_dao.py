# app/adapters/lead_dao.py

import os
import sqlite3
from flask import Flask
from loguru import logger # Using loguru for consistency

def init_db(app: Flask):
    """
    Initializes the SQLite database.
    - For production/development, it creates a database file.
    - For testing, it uses a temporary in-memory database.
    """
    # Get the database path from the app's configuration
    db_path = app.config["DB_PATH"]
    logger.info(f"DB init: Using database path: {db_path}")

    # --- THIS IS THE KEY FIX ---
    # Only create directories if the database path is a file, NOT in-memory.
    # The special string ":memory:" tells sqlite3 to use RAM instead of a file.
    if db_path != ":memory:":
        db_folder = os.path.dirname(db_path)
        os.makedirs(db_folder, exist_ok=True)
    # --- END FIX ---

    try:
        # This connect call works for both file paths and ":memory:"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                zip TEXT,
                phone TEXT,
                quote_type TEXT,
                raw_message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database at {db_path}: {e}")

# You can add your other database functions (like save_lead) below this line