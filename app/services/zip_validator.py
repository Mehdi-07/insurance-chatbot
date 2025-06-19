# In app/services/zip_validator.py
import os
import pandas as pd
import requests
from loguru import logger
from flask import Flask

# Global variable to hold the loaded data
APPROVED_ZIPS_SET = set()

def load_zips(app: Flask):
    """Loads ZIP codes from CSV using a reliable path from the app's root."""
    global APPROVED_ZIPS_SET
    try:
        # This corrected path is simpler and more reliable inside Docker.
        csv_path = os.path.join(app.root_path, 'data', 'zips.csv')
        
        df = pd.read_csv(csv_path, dtype={'zip_code': str})
        APPROVED_ZIPS_SET = set(df['zip_code'])
        logger.info(f"Successfully loaded {len(APPROVED_ZIPS_SET)} ZIP codes from local CSV.")
    except FileNotFoundError:
        logger.error(f"Could not find the ZIP code CSV file at '{csv_path}'. Fallback will not work.")
        APPROVED_ZIPS_SET = set()

def _is_valid_zip_from_csv(zip_code: str) -> bool:
    """Fallback function to check the ZIP against the loaded local CSV file."""
    return zip_code in APPROVED_ZIPS_SET

def is_valid_zip(zip_code: str) -> bool:
    """
    Validates a ZIP code against a list of approved states.
    Tries a free public API first, and falls back to a local CSV on any error.
    """
    try:
        # Try the free Zippopotam.us API
        response = requests.get(f"https://api.zippopotam.us/us/{zip_code}", timeout=2)
        response.raise_for_status()
        data = response.json()
        state = data['places'][0]['state abbreviation']
        
        # Check if the state from the API response is in our approved list
        approved_states = {'MS', 'AL', 'LA', 'GA'}
        logger.info(f"API lookup for ZIP {zip_code} returned state: {state}")
        return state in approved_states
    except Exception as e:
        logger.warning(f"ZIP code API lookup failed: {e}. Using CSV fallback.")
        return _is_valid_zip_from_csv(zip_code)