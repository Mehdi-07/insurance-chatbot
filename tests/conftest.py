# In tests/conftest.py

import pytest
from unittest.mock import patch
from app import create_app

@pytest.fixture(scope="session", autouse=True)
def mock_all_external_services():
    """
    This fixture automatically mocks all external services (Redis, etc.)
    for every test to ensure complete isolation from the network.
    """
    with patch('app.tasks.redis_conn') as mock_redis, \
         patch('app.routes.generate_gpt_reply') as mock_llm, \
         patch('app.routes.lead_dao.save_lead') as mock_db_save:
        
        if mock_redis:
            mock_redis.ping.return_value = True
            mock_redis.hset.return_value = 1
            mock_redis.hget.return_value = b'start'
            mock_redis.pipeline.return_value.execute.return_value = [1]
        
        yield

@pytest.fixture
def client():
    """Creates a Flask test client that all tests can use."""
    app = create_app({
        'TESTING': True,
        'WIDGET_API_KEY': 'test-secret-key'
    })
    
    with patch('app.init_db'):
        yield app.test_client()

@pytest.fixture
def key_header():
    """Provides the correct API key header for tests."""
    return {'X-API-Key': 'test-secret-key'}