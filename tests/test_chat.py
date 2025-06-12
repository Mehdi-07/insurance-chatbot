# tests/test_chat.py
import json
from unittest.mock import patch # Import patch for mocking

from app import create_app # Import your application factory

# Define the base URL for the chat endpoint
CHAT_URL = "/chat"

def test_chat_valid_message_success():
    """
    Tests the /chat endpoint with a valid message, expecting a successful GPT reply.
    Mocks the LLM adapter to prevent actual API calls.
    """
    # Mock the generate_gpt_reply function to control its return value
    # We patch the path where it's *used*, which is app.routes
    with patch('app.routes.generate_gpt_reply') as mock_generate_reply:
        # Configure the mock to return a predictable response
        mock_generate_reply.return_value = "Mocked GPT reply for valid message."

        # Create a test client from the Flask app
        client = create_app({
            "TESTING": True,
            "DB_PATH": "/tmp/leads.db"
        }).test_client()

        # Send a POST request with valid JSON data
        response = client.post(
            CHAT_URL,
            data=json.dumps({"message": "What is life insurance?"}),
            content_type="application/json"
        )

        # Assert the response status code is 200 OK
        assert response.status_code == 200
        # Assert the mocked LLM function was called once with the correct message
        mock_generate_reply.assert_called_once_with("What is life insurance?")
        # Assert the JSON response contains the mocked reply
        assert response.json == {"reply": "Mocked GPT reply for valid message."}

def test_chat_invalid_message_too_short():
    """
    Tests the /chat endpoint with a message that is too short,
    expecting a 422 Unprocessable Entity due to Pydantic validation.
    """
    client = create_app({"TESTING": True}).test_client()
    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "hi"}), # Message shorter than min_length=3
        content_type="application/json"
    )

    # Assert status code is 422 (Unprocessable Entity)
    assert response.status_code == 422
    # Assert the error message structure from Pydantic validation
    assert "error" in response.json
    assert isinstance(response.json["error"], list)
    assert any("message" in err["loc"] and "String should have at least 3 characters" in err["msg"] for err in response.json["error"])
def test_chat_missing_message_field():
    """
    Tests the /chat endpoint with missing 'message' field,
    expecting a 422 Unprocessable Entity due to Pydantic validation.
    """
    client = create_app({"TESTING": True}).test_client()
    response = client.post(
        CHAT_URL,
        data=json.dumps({"text": "some random field"}), # 'message' field is missing
        content_type="application/json"
    )

    # Assert status code is 422
    assert response.status_code == 422
    # Assert error message structure
    assert "error" in response.json
    assert isinstance(response.json["error"], list)
    assert any("message" in err["loc"] and "Field required" in err["msg"] for err in response.json["error"])

def test_chat_invalid_json_format():
    """
    Tests the /chat endpoint with invalid (non-JSON) request body,
    expecting a 400 Bad Request error.
    """
    client = create_app({"TESTING": True}).test_client()
    response = client.post(
        CHAT_URL,
        data="This is not JSON data.", # Invalid JSON
        content_type="text/plain" # Or omit content_type
    )

    # Assert status code is 400 (Bad Request)
    assert response.status_code == 400
    # Assert the specific error message for invalid JSON
    assert response.json == {"error": "Invalid JSON format in request body"}

def test_chat_llm_adapter_failure():
    """
    Tests the /chat endpoint when the LLM adapter (generate_gpt_reply) fails,
    expecting a 200 OK with an error reply from the adapter.
    """
    with patch('app.routes.generate_gpt_reply') as mock_generate_reply:
        # Configure the mock to return an error message
        mock_generate_reply.return_value = "Error: LLM service is down."

        client = create_app({"TESTING": True}).test_client()
        response = client.post(
            CHAT_URL,
            data=json.dumps({"message": "Test LLM failure"}),
            content_type="application/json"
        )

        assert response.status_code == 200 # Still 200 because the adapter returns an error string
        mock_generate_reply.assert_called_once_with("Test LLM failure")
        assert response.json == {"reply": "Error: LLM service is down."}