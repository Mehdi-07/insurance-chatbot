# In app/routes.py

from flask import Blueprint, request, jsonify, render_template
from loguru import logger
from pydantic import ValidationError

# --- CORRECTED IMPORTS BASED ON YOUR FILE STRUCTURE ---
from app.middleware import require_api_key, rate_limiter

# Assumes ChatRequest is in a file named `app/models.py`
from app.models import ChatRequest

# Points to your generate_gpt_reply function in `app/adapters/llm_groq.py`
from app.adapters.llm_groq import generate_gpt_reply

# Points to your lead_dao module in `app/adapters/`
from app.adapters import lead_dao

# Points to your is_valid_zip function in `app/services/zip_validator.py`
from app.services.zip_validator import is_valid_zip

# --- END OF IMPORTS ---


bp = Blueprint('routes', __name__)

# --- ADD THIS NEW ROUTE FOR YOUR HOMEPAGE ---
@bp.route('/', methods=['GET'])
def index():
    """Serves the main HTML page that will host the chat widget."""
    return render_template('index.html')
# --- END OF NEW ROUTE ---

@bp.route('/chat', methods=['POST'])
@require_api_key  # Authenticate first
@rate_limiter     # Then apply rate limiting
def chat():
    """
    Handles chat messages, validates input, saves a lead,
    enqueues notifications, and returns GPT replies.
    """
    try:
        data = ChatRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 422
    except Exception:
        return jsonify({"error": "Invalid JSON format in request body"}), 400
    
    # Validate the ZIP code if provided
    if data.zip_code and not is_valid_zip(data.zip_code):
        return jsonify({
        "reply": f"I'm sorry, it looks like we do not currently serve the {data.zip_code} area. We are expanding soon!"
        }), 200

    # If validation is successful, get the reply from the LLM
    reply = generate_gpt_reply(data.message)

    # After getting the reply, save the lead to the database.
    # This will trigger the background notifications via the RQ worker.
    try:
        # Create a dictionary from the Pydantic model to pass to the save function
        lead_data = data.model_dump()
        lead_data['raw_message'] = data.message

        lead_id = lead_dao.save_lead(lead_data)
        if lead_id:
            logger.info(f"Chat handled and successfully saved lead with ID: {lead_id}")
        else:
            logger.error("Chat handled but failed to save lead to the database.")
    except Exception as e:
        # Log the error but don't block the user from getting their chat reply
        logger.error(f"An exception occurred during lead saving: {e}")

    return jsonify({"reply": reply})


@bp.route('/healthz', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify(status="ok"), 200