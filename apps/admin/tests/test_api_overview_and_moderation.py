def test_admin_overview_ok_and_cached(client, make_token):
    token = make_token(role="admin")
    r1 = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert set(data1.keys()) >= {"counts", "flags", "settings", "catalog", "users_service"}
    assert "areas" in data1["catalog"]
    assert "services" in data1["catalog"]

    # second call must come from cache (repo change shouldn't reflect)
    client.fake_repo.flags["feature_x"] = False
    r2 = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["flags"]["feature_x"] is True


def test_patch_user_status_degraded_when_users_url_missing(client, make_token):
    token = make_token(role="admin")
    r = client.patch(
        "/admin/users/test@example.com/status",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    # USERS_URL missing => users client returns ok False + reason (no status_code)
    assert body["users"]["ok"] is False
    assert "reason" in body["users"]
