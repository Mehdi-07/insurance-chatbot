# app/routes.py
from flask import Blueprint, request, jsonify, render_template
from .models import ChatRequest, ValidationError
# Import your GPT service function from its new location
# The `..` means go up one directory level (from `app/routes.py` to `app/`),
# then go into `adapters/`, then import from `llm_groq.py`.
from app.adapters.llm_groq import generate_gpt_reply

# Create a Blueprint instance
# 'main' is the name of this blueprint, and __name__ helps Flask locate resources
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Renders the main index page."""
    return render_template('index.html')

@bp.route('/chat', methods=['POST'])
def chat():
    """
    Handles chat messages, validates input with Pydantic,
    and returns GPT replies.
    """
    try:
        # Validate incoming JSON data against the ChatRequest model
        # request.get_json() gets the JSON data from the request body
        # ChatRequest.model_validate() attempts to parse and validate it
        data = ChatRequest.model_validate(request.get_json())
    except ValidationError as e:
        # If validation fails, return a 422 Unprocessable Entity status
        # and the detailed validation errors from Pydantic.
        return jsonify({"error": e.errors()}), 422
    except Exception as e:
        # Catch any other JSON parsing errors (e.g., if input is not valid JSON)
        return jsonify({"error": "Invalid JSON format in request body"}), 400

    # If validation is successful, access the message via data.message
    reply = generate_gpt_reply(data.message)
    return jsonify({"reply": reply})

@bp.route("/healthz", methods=["GET"]) # Use @bp.route or @bp.get
def health():
    """Health check endpoint for Kubernetes/ALB."""
    return jsonify(status="ok"), 200 # Returns JSON object directly