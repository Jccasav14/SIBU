import os
import pytest

os.environ["SIBU_TESTING"] = "1"


@pytest.fixture
def app():
    from apps.auth.app.main import app as fastapi_app
    return fastapi_app
