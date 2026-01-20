def test_list_events_admin_ok_and_redacts_sensitive(client, make_token):
    token = make_token(email="admin@u.edu", role="admin")
    r = client.get("/audit/events", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

    data = r.json()
    assert data["total"] >= 1
    item = data["items"][0]
    assert item["event_id"] == "e1"
    # redact() must hide sensitive keys
    assert item["payload_raw"]["token"] == "***REDACTED***"
    assert item["payload_norm"]["password"] == "***REDACTED***"


def test_list_events_bad_sort_400(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/events?sort=nope", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert r.json()["detail"] == "sort inválido"


def test_list_events_bad_date_400(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/events?from=NOT_A_DATE", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert "Fecha inválida" in r.json()["detail"]


def test_get_event_404(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/events/does-not-exist", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
    assert r.json()["detail"] == "No encontrado"


def test_get_event_ok(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/events/e1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["event_id"] == "e1"


def test_by_entity_ok(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/entities/user/u1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["entity_type"] == "user"
    assert data[0]["entity_id"] == "u1"


def test_summary_ok_two_windows(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert [x["window"] for x in data] == ["24h", "7d"]
    assert all("total" in x for x in data)


def test_top_actors_ok(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/top-actors?hours=24&limit=10", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert data[0]["actor"] in ("admin@u.edu", "pro@u.edu")
    assert "count" in data[0]
