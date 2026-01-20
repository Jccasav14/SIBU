import os
import sys
import types

import pytest

# ---------------------------------------------------------
# IMPORTANT: set env & stub deps at COLLECTION (import) time
# ---------------------------------------------------------
os.environ.setdefault("SIBU_TESTING", "1")
os.environ.setdefault("KAFKA_ENABLED", "false")  # avoid starting kafka loop in startup
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

# Make `import app...` work (service uses absolute import `from app...`)
HERE = os.path.dirname(__file__)
SVC_ROOT = os.path.abspath(os.path.join(HERE, ".."))  # apps/notifications
if SVC_ROOT not in sys.path:
    sys.path.insert(0, SVC_ROOT)

# Stub aiokafka if not installed (import-time safe)
try:
    import aiokafka  # noqa: F401
except Exception:
    aiokafka_mod = types.ModuleType("aiokafka")

    class AIOKafkaConsumer:  # minimal stub
        def __init__(self, *args, **kwargs):
            self.started = False

        async def start(self):
            self.started = True

        async def stop(self):
            self.started = False

        def __aiter__(self):
            async def _gen():
                if False:
                    yield None  # pragma: no cover
            return _gen()

    aiokafka_mod.AIOKafkaConsumer = AIOKafkaConsumer
    sys.modules["aiokafka"] = aiokafka_mod


@pytest.fixture()
def app():
    # Import after env is set
    from app.main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)
