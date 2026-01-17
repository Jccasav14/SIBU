def test_list_events_empty_200(client):
    r = client.get("/notifications/events")
    assert r.status_code == 200
    assert r.json() == []


def test_list_events_limit_validation_422(client):
    r = client.get("/notifications/events?limit=0")
    assert r.status_code == 422

    r = client.get("/notifications/events?limit=999")
    assert r.status_code == 422


def test_list_events_offset_validation_422(client):
    r = client.get("/notifications/events?offset=-1")
    assert r.status_code == 422


def test_list_events_offset_and_limit_ok(client):
    # still empty, but validates query params
    r = client.get("/notifications/events?limit=10&offset=0")
    assert r.status_code == 200
    assert r.json() == []
