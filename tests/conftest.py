# In tests/conftest.py
import pytest
from unittest.mock import patch, MagicMock
from app import create_app

@pytest.fixture(scope="session", autouse=True)
def mock_all_external_services():
    """
    This single fixture runs once and automatically mocks all external services
    for every test, ensuring complete isolation and preventing network errors.
    """
    # Patch redis_conn where it is defined. Any module that imports it will get this mock.
    with patch('app.tasks.redis_conn', new_callable=MagicMock) as mock_redis, \
         patch('app.routes.generate_gpt_reply') as mock_llm, \
         patch('app.routes.lead_dao.save_lead') as mock_db_save:
        
        # Configure the mock to handle all required Redis calls
        if mock_redis:
            # For the rate limiter
            mock_redis.pipeline.return_value.execute.return_value = [1] 
            # For the session wizard logic
            mock_redis.hget.return_value = b'start' 
            mock_redis.hset.return_value = 1
            mock_redis.expire.return_value = 1
        
        # Allow all tests to run with these mocks active
        yield


@pytest.fixture
def client():
    """A fixture that creates a test client for the application."""
    app = create_app({
        'TESTING': True,
        'WIDGET_API_KEY': 'test-secret-key'
    })
    
    # Also patch init_db to prevent any real DB operations during app creation
    with patch('app.extensions.init_db'): # Corrected path to init_db
        yield app.test_client()


@pytest.fixture
def key_header():
    """A fixture that provides the correct API key header for tests."""
    return {'X-API-Key': 'test-secret-key'}