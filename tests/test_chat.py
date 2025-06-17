# In tests/test_chat.py
import json
from unittest.mock import patch

# In tests/test_chat.py
import json

CHAT_URL = "/chat"

def test_wizard_flow_starts_on_first_message(client, key_header):
    """
    Tests that the wizard flow correctly starts on the user's first message.
    """
    # Simulate the user's first message
    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "hi"}),
        content_type="application/json",
        headers=key_header
    )
    
    # VERIFY that the response is the 'start' node of the wizard
    assert response.status_code == 200
    assert response.json['save_as'] == "coverage_category"
    assert "Personal or Business" in response.json['text']


def test_wizard_flow_handles_button_click(client, key_header):
    """
    Tests that the wizard correctly handles a button click and advances the conversation.
    """
    # First, start the conversation
    client.post(CHAT_URL, data=json.dumps({"message": "hi"}), headers=key_header)

    # Now, simulate clicking the "Personal" button
    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "__CLICKED__:personal"}),
        content_type="application/json",
        headers=key_header
    )

    # VERIFY that the response is the next step in the flow
    assert response.status_code == 200
    assert response.json['save_as'] == "quote_type"
    assert "What type of personal insurance" in response.json['text']

def test_chat_unauthorized(client):
    """Tests that a request without an API key is still rejected."""
    response = client.post(CHAT_URL, data=json.dumps({"message": "this should fail"}))
    assert response.status_code == 401