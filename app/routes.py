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
        return jsonify({"error": "Invalid JSON format in request body"}), 400
        
    user_message = req_data.get("message", "")
    session_id = session.get("uid")

    # --- 3. ADD THIS NEW WIZARD LOGIC ---
    # Check if the message is a special command from a button click
    if user_message.startswith("__CLICKED__"):
        # The value of the button click, e.g., "ask_auto_year"
        clicked_node_id = user_message.split(":", 1)[1]
        
        # Find out what the last question was to save the answer correctly
        current_node_id = wizard_service.get_current_node_id(session_id)
        current_node_data = wizard_service.get_node_data(current_node_id)
        
        # Save the answer to Redis (e.g., save 'quote_type' as 'ask_auto_year')
        answer_key = current_node_data.get("save_as")
        if answer_key:
            wizard_service.save_answer(session_id, answer_key, clicked_node_id)
            
        # Get the next question/node from the flow definition
        next_node_data = wizard_service.get_node_data(clicked_node_id)
        # Update the user's position in the flow
        wizard_service.advance_to_node(session_id, clicked_node_id)
        
        # Return the next question and buttons directly, without calling the LLM
        return jsonify(next_node_data)
    # --- END OF WIZARD LOGIC ---

    # --- This is your existing logic for handling regular text messages ---
    try:
        data = ChatRequest.model_validate(req_data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 422

    if data.zip_code and not is_valid_zip(data.zip_code):
        return jsonify({
            "reply": f"I'm sorry, we do not currently serve the {data.zip_code} area."
        }), 200
    
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