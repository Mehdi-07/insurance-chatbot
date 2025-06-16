# In tests/conftest.py

import pytest
from unittest.mock import patch, MagicMock
from app import create_app

@pytest.fixture(scope="session", autouse=True)
def mock_all_external_services():
    """
    This fixture runs once for the entire test session.
    It mocks all external services to prevent real network calls.
    'autouse=True' means it runs for every test without needing to be requested.
    """
    # This block now correctly patches the 'redis_conn' object where it is defined.
    # Any other module that imports it will now get the mock instead.
    with patch('app.tasks.redis_conn', new_callable=MagicMock) as mock_redis, \
         patch('app.routes.generate_gpt_reply') as mock_llm, \
         patch('app.routes.lead_dao.save_lead') as mock_db_save:
        
        # Configure the mock to behave like a real Redis connection
        # so that calls to it don't fail.
        mock_redis.pipeline.return_value.execute.return_value = [1]
        
        # Yield control to let all the tests run with these mocks active.
        yield

@pytest.fixture
def client():
    """Creates a Flask test client that all tests can use."""
    app = create_app({
        'TESTING': True,
        'WIDGET_API_KEY': 'test-secret-key',
        'REDIS_URL': 'redis://mock-redis:6379' # Provide a dummy URL for tests
    })
    
    # We also patch init_db to prevent any DB operations during app creation for tests
    with patch('app.init_db'):
        yield app.test_client()

@pytest.fixture
def key_header():
    """Provides the correct API key header for tests."""
    return {'X-API-Key': 'test-secret-key'}