# tests/test_health.py
from app import create_app # Import your application factory

def test_health_endpoint(): # <--- ENSURE THIS FUNCTION STARTS WITH 'test_'
    """
    Tests the /healthz endpoint to ensure it returns a 200 OK status
    and the correct JSON response.
    """
    # Create a test Flask application instance
    # Set TESTING to True to disable error catching during tests
    client = create_app({
        "TESTING": True,
        "DB_PATH": "/tmp/leads.db"
    }).test_client()

    # Make a GET request to the /healthz endpoint
    res = client.get("/healthz")

    # Assert that the status code is 200 (OK)
    assert res.status_code == 200

    # Assert that the JSON response contains {"status": "ok"}
    assert res.json == {"status": "ok"}