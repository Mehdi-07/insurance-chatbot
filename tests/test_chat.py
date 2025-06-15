# In tests/test_chat.py
import json
from unittest.mock import patch
from app import create_app

CHAT_URL = "/chat"
TEST_API_KEY = "test-secret-key"

# This patch decorator will apply to ALL test functions in this file,
# preventing them from making real database or LLM calls.
@patch('app.middleware.redis_conn')
@patch('app.routes.lead_dao.save_lead', return_value=1)
@patch('app.routes.generate_gpt_reply')
def test_chat_logic(mock_generate_reply, mock_save_lead, mock_redis_conn):
    """
    Tests all chat logic scenarios.
    Mocks are passed as arguments by the decorator.
    """
    mock_redis_conn.pipeline.return_value.execute.return_value = [1]  # Simulate Redis rate limit success

    client = create_app({
        "TESTING": True,
        "WIDGET_API_KEY": TEST_API_KEY
    }).test_client()

    # --- Test: Valid message success ---
    mock_generate_reply.return_value = "Mocked GPT reply."
    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "This is a valid message"}),
        content_type="application/json",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    assert response.json["reply"] == "Mocked GPT reply."
    mock_save_lead.assert_called_once() # Verify that we TRIED to save the lead
    mock_save_lead.reset_mock() # Reset the mock for the next test case

    # --- Test: Missing message field should fail validation ---
    response = client.post(
        CHAT_URL,
        data=json.dumps({"name": "test"}), # Missing 'message'
        content_type="application/json",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 422
    assert mock_save_lead.call_count == 0 # Verify we did NOT try to save the lead

    # --- Test: Invalid JSON format should fail ---
    response = client.post(
        CHAT_URL,
        data="this is not valid json",
        content_type="application/json",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 400
    assert mock_save_lead.call_count == 0

# NOTE: The test for "message too short" has been removed, as it's now a feature.

# This test is separate because it doesn't need the mocks above
def test_chat_unauthorized_missing_key():
    """Tests that a request without an API key is rejected."""
    client = create_app({"TESTING": True, "WIDGET_API_KEY": TEST_API_KEY}).test_client()
    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "This should fail"})
    )
    assert response.status_code == 401

    response = client.post(
        CHAT_URL,
        data=json.dumps({"message": "This should also fail"}),
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401