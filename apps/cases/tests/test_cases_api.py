import os
import pytest
from fastapi.testclient import TestClient

# for tests use sqlite in memory file
os.environ["DATABASE_URL"] = "sqlite:///./test_cases.db"
os.environ["AUTH_DISABLED"] = "true"

from apps.cases.app.main import create_app  # noqa: E402

@pytest.fixture(scope="session")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "cases"

def test_crud_flow(client):
    # create
    r = client.post(
        "/cases",
        json={
            "student_id": "student-001",
            "owner_area": "PSY",
            "title": "Caso 1",
            "description": "Detalle",
            "priority": "HIGH",
        },
    )
    assert r.status_code == 201
    case = r.json()
    case_id = case["id"]
    assert case["status"] == "OPEN"

    # list
    r = client.get("/cases")
    assert r.status_code == 200
    assert any(x["id"] == case_id for x in r.json())

    # historial por estudiante
    r = client.get("/cases/by-student/student-001")
    assert r.status_code == 200
    assert any(x["id"] == case_id for x in r.json())

    # update
    r = client.patch(f"/cases/{case_id}", json={"title": "Caso 1 editado"})
    assert r.status_code == 200
    assert r.json()["title"] == "Caso 1 editado"

    # assign
    r = client.post(f"/cases/{case_id}/assign", json={"professional_id": "prof-123"})
    assert r.status_code == 200
    assert r.json()["assigned_professional_id"] == "prof-123"

    # change status
    r = client.post(f"/cases/{case_id}/status", json={"status": "IN_PROGRESS"})
    assert r.status_code == 200
    assert r.json()["status"] == "IN_PROGRESS"

    # timeline
    r = client.get(f"/cases/{case_id}/timeline")
    assert r.status_code == 200
    events = r.json()
    assert len(events) >= 3  # created, updated, assigned, status_changed...
