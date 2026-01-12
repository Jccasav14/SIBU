import pytest


@pytest.mark.asyncio
async def test_insurance_ok(client, make_token):
    token = make_token("insurance")
    r = await client.get("/health", headers={"Authorization": f"Bearer {token}"})
    # /health does not require auth
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_professional_forbidden(client, make_token):
    token = make_token("professional")
    r = await client.get("/claims", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_ok(client, make_token):
    token = make_token("admin")
    r = await client.get("/claims", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
