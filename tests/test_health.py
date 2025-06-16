# tests/test_health.py
from app import create_app # Import your application factory

# In tests/test_health.py

def test_health_endpoint(client):
    """Tests the /healthz endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json["status"] == "ok"