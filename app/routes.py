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
    req_data = request.get_json()
    if not req_data: return jsonify({"error": "Invalid JSON"}), 400
        
    user_message = req_data.get("message", "")
    session_id = session.get("uid")
    current_node_id = wizard_service.get_current_node_id(session_id)

    # Scenario 1: User clicked a button
    if user_message.startswith("__CLICKED__"):
        clicked_value = user_message.split(":", 1)[1]
        current_node_data = wizard_service.get_node_data(current_node_id)
        
        answer_key = current_node_data.get("save_as") if current_node_data else None
        if answer_key:
            wizard_service.save_answer(session_id, answer_key, clicked_value)

        next_node_id = "get_contact_info" # Default to final step
        if current_node_data and "buttons" in current_node_data:
            for button in current_node_data["buttons"]:
                if button.get("value") == clicked_value:
                    next_node_id = button.get("next_node")
                    break
        
        next_node_data = wizard_service.get_node_data(next_node_id)
        wizard_service.advance_to_node(session_id, next_node_id)
        return jsonify(next_node_data)

    # Scenario 2: It's the user's first message
    elif current_node_id == "start":
        start_node_data = wizard_service.get_node_data("start")
        return jsonify(start_node_data)

    # Scenario 3: It's a free-text answer (final submission)
    else:
        try:
            current_data = ChatRequest.model_validate(req_data)
        except ValidationError as e:
            return jsonify({"error": e.errors()}), 422

        # Gather ALL answers from the Redis session
        session_answers = wizard_service.get_all_answers(session_id)
        
        # Combine session answers with data from the final message
        final_lead_data = {
            **session_answers, 
            **current_data.model_dump(exclude_none=True)
        }
        final_lead_data['raw_message'] = current_data.message
        final_lead_data['session_id'] = session_id
        
        # Save the complete lead to the database (which also triggers n8n)
        lead_dao.save_lead(final_lead_data)
        
        # For the final reply, we can just send a simple confirmation
        return jsonify({"reply": "Thank you! An agent will be in touch with your quote shortly."})


@bp.route('/healthz', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify(status="ok"), 200