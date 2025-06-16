# In tests/conftest.py

import pytest
from unittest.mock import patch
from app import create_app

# In tests/conftest.py

@pytest.fixture(autouse=True)
def mock_all_external_services():
    """
    Mocks all external services for all tests to ensure isolation.
    """
    # We will mock the 'redis_conn' object in the 'tasks' module where it is created.
    # Any other module that imports it will now get the mock instead.
    with patch('app.tasks.redis_conn') as mock_redis, \
         patch('app.routes.generate_gpt_reply') as mock_llm, \
         patch('app.routes.lead_dao.save_lead') as mock_db_save:
        
        # If redis is None (because the connection failed), we can't set attributes on it.
        # So we only configure it if the mock was successful.
        if mock_redis:
            mock_redis.hget.return_value = b'start'
            mock_redis.pipeline.return_value.execute.return_value = [1]

        yield

@pytest.fixture
def client():
    """Creates a Flask test client for use in tests."""
    app = create_app({
        'TESTING': True,
        'WIDGET_API_KEY': 'test-secret-key'
    })
    return app.test_client()

@pytest.fixture
def key_header():
    """Provides the authorization header for protected routes."""
    return {'X-API-Key': 'test-secret-key'}