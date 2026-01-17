def test_create_case_201(client, make_token):
    token = make_token(sub="admin-1", roles=["admin"], area="PSY")
    r = client.post(
        "/cases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_id": "student-001",
            "owner_area": "PSY",
            "title": "Caso 1",
            "description": "Detalle del caso",
            "priority": "HIGH",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["student_id"] == "student-001"
    assert data["status"] == "OPEN"
    assert data["priority"] == "HIGH"
    assert "id" in data


def test_list_cases_200_includes_created(client, make_token):
    token = make_token()
    r = client.get("/cases", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_update_case_200(client, make_token):
    token = make_token()
    # create
    created = client.post(
        "/cases",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": "s2", "owner_area": "PSY", "title": "Caso X", "description": "Desc", "priority": "LOW"},
    ).json()
    case_id = created["id"]

    # update
    r = client.patch(
        f"/cases/{case_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Caso X editado"},
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Caso X editado"


def test_change_status_200(client, make_token):
    token = make_token()
    created = client.post(
        "/cases",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": "s3", "owner_area": "PSY", "title": "Caso S", "description": "Desc", "priority": "MEDIUM"},
    ).json()
    case_id = created["id"]

    r = client.post(
        f"/cases/{case_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "IN_PROGRESS"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "IN_PROGRESS"
