# In app/routes.py

from flask import Blueprint, request, jsonify, render_template, session
from loguru import logger
from pydantic import ValidationError

# All imports are now absolute and based on your confirmed project structure
from app.middleware import require_api_key, rate_limiter
from app.models import ChatRequest
from app.adapters import lead_dao
from app.adapters.llm_groq import generate_gpt_reply
from app.services.zip_validator import is_valid_zip
from app.services import wizard_service

# This line creates the 'bp' object that your __init__.py needs to import
bp = Blueprint('routes', __name__)


@bp.route('/', methods=['GET'])
def index():
    """Serves the main HTML page that will host the chat widget."""
    return render_template('index.html')


@bp.route('/chat', methods=['POST'])
@require_api_key
@rate_limiter
def chat():
    """
    Handles all chat interactions, including starting the flow, button clicks,
    and free-text messages.
    """
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "Invalid JSON format"}), 400
        
    user_message = req_data.get("message", "")
    session_id = session.get("uid")
    current_node_id = wizard_service.get_current_node_id(session_id)

    # Scenario 1: The user clicked a button.
    if user_message.startswith("__CLICKED__"):
        clicked_value = user_message.split(":", 1)[1]
        
        current_node_data = wizard_service.get_node_data(current_node_id)
        
        answer_key = current_node_data.get("save_as") if current_node_data else None
        if answer_key:
            wizard_service.save_answer(session_id, answer_key, clicked_value)

        next_node_id = None
        if current_node_data and "buttons" in current_node_data:
            for button in current_node_data["buttons"]:
                if button.get("value") == clicked_value:
                    next_node_id = button.get("next_node")
                    break
        
        if next_node_id:
            next_node_data = wizard_service.get_node_data(next_node_id)
            wizard_service.advance_to_node(session_id, next_node_id)
            return jsonify(next_node_data)
        else:
            final_node = wizard_service.get_node_data("get_contact_info")
            wizard_service.advance_to_node(session_id, "get_contact_info")
            return jsonify(final_node)

    # Scenario 2: This is the user's very first message in a session.
    elif current_node_id == "start":
        logger.info(f"New conversation for session {session_id}. Starting wizard.")
        start_node_data = wizard_service.get_node_data("start")
        return jsonify(start_node_data)

    # Scenario 3: It's a regular free-text message. Use the LLM.
    else:
        logger.info(f"Handling free-text input for session {session_id}.")
        try:
            data = ChatRequest.model_validate(req_data)
        except ValidationError as e:
            return jsonify({"error": e.errors()}), 422

        if data.zip_code and not is_valid_zip(data.zip_code):
            return jsonify({
                "reply": f"I'm sorry, we do not currently serve the {data.zip_code} area."
            }), 200
        
        current_node_data = wizard_service.get_node_data(current_node_id)
        answer_key = current_node_data.get("save_as") if current_node_data else None
        if answer_key:
             wizard_service.save_answer(session_id, answer_key, data.message)

        prompt_context = f"User message: '{data.message}'"
        reply = generate_gpt_reply(prompt_context)

        try:
            lead_data = data.model_dump()
            lead_data['raw_message'] = data.message
            lead_dao.save_lead(lead_data)
            logger.info("Chat handled and lead saved.")
        except Exception as e:
            logger.error(f"An exception occurred during lead saving: {e}")

        return jsonify({"reply": reply})


@bp.route('/healthz', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify(status="ok"), 200