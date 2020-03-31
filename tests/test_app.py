import pytest

from app import create_app

@pytest.fixture
def app():
    app = create_app(testing=True)
    return app.test_client()
