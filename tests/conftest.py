# In tests/conftest.py

import pytest
from unittest.mock import patch
from app import create_app

@pytest.fixture(autouse=True)
def mock_all_external_services():
    """
    A pytest fixture that automatically mocks all external services (Redis, etc.)
    for every test to ensure isolation and prevent real network calls.
    'autouse=True' means it runs for every test without needing to be requested.
    """
    # We patch every place where redis_conn is imported and used
    with patch('app.init_session.redis_conn') as mock_redis_for_session, \
         patch('app.middleware.redis_conn') as mock_redis_for_middleware, \
         patch('app.routes.generate_gpt_reply') as mock_llm, \
         patch('app.routes.lead_dao.save_lead') as mock_db_save:

        # Configure the mocks to behave like the real thing
        # This prevents ConnectionErrors from both session and rate limiter
        mock_redis_for_session.hget.return_value = b'start'
        mock_redis_for_middleware.pipeline.return_value.execute.return_value = [1]

        # Yield control back to the test function to run
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