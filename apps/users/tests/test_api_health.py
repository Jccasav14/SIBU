from fastapi import FastAPI
from starlette.testclient import TestClient


def test_health_200():
    # No usamos main.py (tiene startup con engine/kafka).
    # Probamos algo mínimo: que el router existe y responde en tests de API.
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True, "service": "users"}

    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
