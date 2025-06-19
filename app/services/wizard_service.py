# In app/services/wizard_service.py
import json
import os
from loguru import logger
from flask import Flask
from app.tasks import redis_conn

# Global variable to hold the loaded flow
FLOW_DEFINITION = {}

def load_flow(app: Flask):
    """Loads the conversation flow JSON using the app's root path."""
    global FLOW_DEFINITION
    try:
        # Build a reliable, absolute path to the data file
        flow_path = os.path.join(app.root_path, '..', 'flows', 'premium.json')
        with open(flow_path, 'r') as f:
            FLOW_DEFINITION = json.load(f)
        logger.info("Successfully loaded premium.json conversation flow.")
    except FileNotFoundError:
        logger.error(f"CRITICAL: Conversation flow file not found at '{flow_path}'. Wizard will not work.")

def get_current_node_id(session_id: str) -> str:
    """Gets the user's current position in the flow from Redis."""
    if not redis_conn:
        return "start"
    current_node_bytes = redis_conn.hget(f"ctx:{session_id}", "current_node")
    # hget returns bytes, so we need to decode it to a string
    return current_node_bytes.decode('utf-8') if current_node_bytes else "start"

def get_node_data(node_id: str) -> dict:
    """Retrieves the text and buttons for a given node ID from the JSON flow."""
    return FLOW_DEFINITION.get(node_id)

def save_answer(session_id: str, key: str, value: str):
    """Saves a user's answer to the session hash in Redis."""
    if not redis_conn or not key:
        return
    session_key = f"ctx:{session_id}"
    redis_conn.hset(session_key, f"answers:{key}", value)
    logger.info(f"Saved answer for session {session_id}: {key} = {value}")

def advance_to_node(session_id: str, node_id: str):
    """Updates the user's current position in the flow in Redis."""
    if not redis_conn:
        return
    session_key = f"ctx:{session_id}"
    redis_conn.hset(session_key, "current_node", node_id)
    logger.info(f"Advanced session {session_id} to node: {node_id}")

# Add this function to the bottom of app/services/wizard_service.py
def get_all_answers(session_id: str) -> dict:
    """Retrieves all answers for a given session from Redis."""
    if not redis_conn:
        return {}
    
    answers_bytes = redis_conn.hgetall(f"ctx:{session_id}")
    # hgetall returns bytes, so we decode them into a clean dictionary
    answers = {k.decode('utf-8'): v.decode('utf-8') for k, v in answers_bytes.items()}
    
    # We only want the 'answers:', so let's filter for them
    final_answers = {}
    for key, value in answers.items():
        if key.startswith("answers:"):
            final_answers[key.replace("answers:", "")] = value
            
    return final_answers