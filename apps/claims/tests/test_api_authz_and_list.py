def test_list_claims_without_token_401(client):
    r = client.get("/claims")
    assert r.status_code == 401
    assert r.json()["detail"] == "Missing bearer token"


def test_list_claims_invalid_token_401(client):
    r = client.get("/claims", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401
    assert "Invalid token" in r.json()["detail"]


def test_list_claims_wrong_role_403(client, make_token):
    token = make_token(email="pro@u.edu", role="professional")
    r = client.get("/claims", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "This service is restricted to insurance and admin roles"


def test_list_claims_valid_token_200(client, make_token):
    token = make_token(email="ins@u.edu", role="insurance")
    r = client.get("/claims?limit=10&offset=0", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "limit" in data and "offset" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1


def test_list_claims_validation_422_limit_too_small(client, make_token):
    token = make_token()
    r = client.get("/claims?limit=0", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


def test_get_claim_404_when_missing(client, make_token):
    token = make_token()
    r = client.get("/claims/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Claim not found"


def test_get_claim_200_and_caches(client, make_token):
    token = make_token()
    cid = "11111111-1111-1111-1111-111111111111"

    r1 = client.get(f"/claims/{cid}", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["id"] == cid
    assert data1["student_id"] == "stu-001"

    # second call should hit cache (same response)
    r2 = client.get(f"/claims/{cid}", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["id"] == cid


def test_overview_200_and_caches(client, make_token):
    token = make_token(role="admin")
    r1 = client.get("/claims/overview", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200
    assert "total" in r1.json()

    r2 = client.get("/claims/overview", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
