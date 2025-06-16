# In tests/conftest.py

import pytest
from unittest.mock import patch
from app import create_app

@pytest.fixture(scope="session", autouse=True)
def mock_all_external_services():
    """
    This fixture automatically mocks all external services for all tests,
    preventing real network calls. It runs once for the whole test session.
    """
    # Patch the redis_conn object at its source. Any other module that
    # imports it during a test will now get this harmless mock instead.
    with patch('app.tasks.redis_conn') as mock_redis, \
         patch('app.routes.generate_gpt_reply') as mock_llm, \
         patch('app.routes.lead_dao.save_lead') as mock_db_save:
        
        # Configure the mock to prevent errors when its methods are called
        if mock_redis:
            mock_redis.pipeline.return_value.execute.return_value = [1]

        # Let the tests run with these mocks active
        yield


@pytest.fixture
def client():
    """A fixture that creates and configures a test app instance for tests."""
    app = create_app({
        'TESTING': True,
        'WIDGET_API_KEY': 'test-secret-key'
    })
    
    # Also patch init_db to prevent real DB operations during app creation
    with patch('app.init_db'):
        yield app.test_client()


@pytest.fixture
def key_header():
    """A fixture that provides the correct API key header for tests."""
    return {'X-API-Key': 'test-secret-key'}