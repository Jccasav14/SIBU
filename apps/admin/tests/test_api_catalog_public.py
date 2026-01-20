def test_public_catalog_areas_filters_only_enabled(client, make_token):
    token = make_token(email="pro@test.com", role="professional")
    r = client.get("/catalog/areas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert all(item["enabled"] is True for item in data)
    assert {i["name"] for i in data} == {"PSYCHOLOGY"}


def test_public_catalog_areas_uses_cache_second_time(client, make_token):
    token = make_token(email="pro@test.com", role="professional")
    # first call sets cache
    r1 = client.get("/catalog/areas", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200
    # mutate repo to prove cache is used
    client.fake_repo.areas.append(type("X", (), {"id": 99, "name": "SHOULD_NOT_APPEAR", "enabled": True})())
    r2 = client.get("/catalog/areas", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert {i["name"] for i in r2.json()} == {"PSYCHOLOGY"}
