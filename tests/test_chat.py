# In tests/test_chat.py
import json
from unittest.mock import patch

CHAT_URL = "/chat"

# We now patch only the functions used in this specific file
@patch('app.routes.generate_gpt_reply')
@patch('app.routes.lead_dao.save_lead')
def test_chat_success(mock_save, mock_llm, client, key_header):
    """Tests a valid, authorized request."""
    # Configure the mock to return a simple string
    mock_llm.return_value = "This is a successful mock reply."

    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "This is a valid message", "name": "Test User"}),
        content_type="application/json",
        headers=key_header
    )
    assert response.status_code == 200
    assert response.json["reply"] == "This is a successful mock reply."
    mock_save.assert_called_once()


def test_chat_unauthorized(client):
    """Tests that a request without an API key is rejected."""
    response = client.post(CHAT_URL, data=json.dumps({"message": "This should fail"}))
    assert response.status_code == 401


# We only need to mock the save_lead function here, as the LLM is not called
@patch('app.routes.lead_dao.save_lead')
def test_chat_bad_request(mock_save, client, key_header):
    """Tests requests with invalid data."""
    response = client.post(
        CHAT_URL,
        data=json.dumps({"name": "test"}), # Missing message
        content_type="application/json",
        headers=key_header
    )
    assert response.status_code == 422
    # Assert that save was NOT called
    mock_save.assert_not_called()