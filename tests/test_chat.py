# In tests/test_chat.py
import json

CHAT_URL = "/chat"

def test_chat_success(client, key_header):
    """Tests a valid, authorized request."""
    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "This is a valid message"}),
        content_type="application/json",
        headers=key_header
    )
    assert response.status_code == 200
    assert "reply" in response.json

def test_chat_unauthorized(client):
    """Tests that a request without an API key is rejected."""
    response = client.post(CHAT_URL, data=json.dumps({"message": "This should fail"}))
    assert response.status_code == 401

def test_chat_bad_request(client, key_header):
    """Tests requests with missing or invalid data."""
    # Test missing message field
    response = client.post(
        CHAT_URL,
        data=json.dumps({"name": "test"}),
        content_type="application/json",
        headers=key_header
    )
    assert response.status_code == 422

    # Test invalid JSON
    response = client.post(
        CHAT_URL,
        data="this is not valid json",
        content_type="application/json",
        headers=key_header
    )
    assert response.status_code == 400