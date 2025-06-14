# In tests/test_chat.py
import json
from unittest.mock import patch
from app import create_app

CHAT_URL = "/chat"
# Define a dummy API key for all our tests
TEST_API_KEY = "test-secret-key"

def test_chat_valid_message_success():
    """Tests the /chat endpoint with a valid message and API key."""
    with patch('app.routes.generate_gpt_reply') as mock_generate_reply:
        mock_generate_reply.return_value = "Mocked GPT reply for valid message."

        client = create_app({
            "TESTING": True,
            # We add the dummy API key to the app's config for testing
            "WIDGET_API_KEY": TEST_API_KEY
        }).test_client()

        # We now add the "headers" parameter to our request
        response = client.post(
            CHAT_URL,
            data=json.dumps({"message": "What is life insurance?"}),
            content_type="application/json",
            headers={"X-API-Key": TEST_API_KEY} # <-- THE FIX IS HERE
        )

        assert response.status_code == 200
        assert response.json["reply"] == "Mocked GPT reply for valid message."

def test_chat_unauthorized_missing_key():
    """Tests that a request without an API key is rejected."""
    client = create_app({"TESTING": True, "WIDGET_API_KEY": TEST_API_KEY}).test_client()
    
    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "This should fail"}),
        content_type="application/json"
        # No header is sent
    )
    
    # We expect a 401 Unauthorized error
    assert response.status_code == 401

# --- Apply the same fix to your other tests ---

def test_chat_invalid_message_too_short():
    """Tests a message that is too short, expecting a 422."""
    client = create_app({"TESTING": True, "WIDGET_API_KEY": TEST_API_KEY}).test_client()
    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "Hi"}),
        content_type="application/json",
        headers={"X-API-Key": TEST_API_KEY} # <-- ADDED HEADER
    )
    assert response.status_code == 422

def test_chat_missing_message_field():
    """Tests a request with a missing message field, expecting a 422."""
    client = create_app({"TESTING": True, "WIDGET_API_KEY": TEST_API_KEY}).test_client()
    response = client.post(
        CHAT_URL,
        data=json.dumps({"name": "test"}),
        content_type="application/json",
        headers={"X-API-Key": TEST_API_KEY} # <-- ADDED HEADER
    )
    assert response.status_code == 422

def test_chat_invalid_json_format():
    """Tests an invalid JSON body, expecting a 400."""
    client = create_app({"TESTING": True, "WIDGET_API_KEY": TEST_API_KEY}).test_client()
    response = client.post(
        CHAT_URL,
        data="this is not json",
        content_type="application/json",
        headers={"X-API-Key": TEST_API_KEY} # <-- ADDED HEADER
    )
    assert response.status_code == 400

def test_chat_llm_adapter_failure():
    """Tests when the LLM adapter fails, expecting a 200 with an error reply."""
    with patch('app.routes.generate_gpt_reply') as mock_generate_reply:
        mock_generate_reply.return_value = "Error: LLM service is down."
        
        client = create_app({"TESTING": True, "WIDGET_API_KEY": TEST_API_KEY}).test_client()
        response = client.post(
            CHAT_URL,
            data=json.dumps({"message": "Test LLM failure"}),
            content_type="application/json",
            headers={"X-API-Key": TEST_API_KEY} # <-- ADDED HEADER
        )
        
        assert response.status_code == 200
        assert "LLM service is down" in response.json["reply"]