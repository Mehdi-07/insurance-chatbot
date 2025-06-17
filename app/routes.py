# In app/routes.py

from flask import Blueprint, request, jsonify, render_template, session # 1. Import 'session'
from loguru import logger
from pydantic import ValidationError

from app.middleware import require_api_key, rate_limiter
from app.models import ChatRequest
from app.adapters.llm_groq import generate_gpt_reply
from app.adapters import lead_dao
from app.services.zip_validator import is_valid_zip
from app.services import wizard_service # 2. Import our new wizard_service

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
    Handles all chat interactions, including button clicks and free-text messages.
    """
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "Invalid JSON format"}), 400
        
    user_message = req_data.get("message", "")
    session_id = session.get("uid")

    # --- THIS IS THE CORRECTED WIZARD LOGIC ---
    if user_message.startswith("__CLICKED__"):
        # The value from the button click, e.g., "personal" or "ask_auto_year"
        clicked_value = user_message.split(":", 1)[1]
        
        # Find out what the last question was
        current_node_id = wizard_service.get_current_node_id(session_id)
        current_node_data = wizard_service.get_node_data(current_node_id)
        
        # Find the specific button that was clicked to get the correct next_node
        next_node_id = None
        if current_node_data and "buttons" in current_node_data:
            for button in current_node_data["buttons"]:
                if button.get("value") == clicked_value:
                    next_node_id = button.get("next_node")
                    break
        
        # Save the answer to Redis (e.g., save 'coverage_category' as 'personal')
        answer_key = current_node_data.get("save_as") if current_node_data else None
        if answer_key:
            wizard_service.save_answer(session_id, answer_key, clicked_value)
            
        # Get the data for the next step in the conversation
        if next_node_id:
            next_node_data = wizard_service.get_node_data(next_node_id)
            wizard_service.advance_to_node(session_id, next_node_id)
            return jsonify(next_node_data)
        else:
            # If we can't find a next node, something is wrong or the flow ended.
            # Fall back to a safe final message.
            final_node = wizard_service.get_node_data("get_contact_info")
            return jsonify(final_node)
    # --- END OF CORRECTED WIZARD LOGIC ---

    # --- Logic for handling free-text messages (this part is fine) ---
    try:
        data = ChatRequest.model_validate(req_data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 422

    if data.zip_code and not is_valid_zip(data.zip_code):
        return jsonify({"reply": f"Sorry, we do not serve the {data.zip_code} area."}), 200
    
    # Build a contextual prompt for the LLM
    prompt_context = f"""A user has provided the following information.
    Name: {data.name or 'Not Provided'}
    ZIP Code: {data.zip_code or 'Not Provided'}
    Their message is: "{data.message}"
    Generate a helpful, context-aware response."""
    reply = generate_gpt_reply(prompt_context)

    try:
        lead_data = data.model_dump()
        lead_data['raw_message'] = data.message
        lead_id = lead_dao.save_lead(lead_data)
        if lead_id:
            logger.info(f"Chat handled and successfully saved lead with ID: {lead_id}")
        else:
            logger.error("Chat handled but failed to save lead to the database.")
    except Exception as e:
        logger.error(f"An exception occurred during lead saving: {e}")

    return jsonify({"reply": reply})

@bp.route('/healthz', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify(status="ok"), 200