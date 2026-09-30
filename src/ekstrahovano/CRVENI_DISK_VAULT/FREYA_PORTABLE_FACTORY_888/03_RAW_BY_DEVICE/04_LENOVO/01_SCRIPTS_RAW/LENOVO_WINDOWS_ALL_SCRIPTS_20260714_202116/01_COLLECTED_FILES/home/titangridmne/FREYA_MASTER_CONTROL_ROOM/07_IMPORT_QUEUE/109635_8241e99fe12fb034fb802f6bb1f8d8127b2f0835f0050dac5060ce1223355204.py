import pytest


@pytest.mark.asyncio
async def test_refresh_token_rotation(client):
    await client.post("/auth/tenants", json={"slug": "tenant-r", "name": "Tenant R"})
    await client.post(
        "/auth/register",
        json={"tenant_slug": "tenant-r", "email": "refresh@example.com", "full_name": "Refresh User", "password": "StrongPass123", "role": "admin"},
    )
    login = await client.post(
        "/auth/login",
        json={"tenant_slug": "tenant-r", "email": "refresh@example.com", "password": "StrongPass123"},
    )
    assert login.status_code == 200
    old_refresh = login.json()["refresh_token"]

    refreshed = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh != old_refresh

    reuse_old = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_old.status_code == 401
