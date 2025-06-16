# In app/services/wizard_service.py
import json
import os
from loguru import logger
from app.tasks import redis_conn

# Load the entire conversation flow from the JSON file into memory
try:
    # This path assumes your flows folder is in the project root
    with open('flows/premium.json', 'r') as f:
        FLOW_DEFINITION = json.load(f)
    logger.info("Successfully loaded premium.json conversation flow.")
except FileNotFoundError:
    logger.error("CRITICAL: flows/premium.json not found. The button wizard will not work.")
    FLOW_DEFINITION = {}

def get_current_node_id(session_id: str) -> str:
    """Gets the user's current position in the flow from Redis."""
    if not redis_conn:
        return "start" # Default to start if redis is down
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