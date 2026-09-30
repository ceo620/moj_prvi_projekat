import pytest


@pytest.mark.asyncio
async def test_tenant_isolation(client):
    await client.post("/auth/tenants", json={"slug": "tenant-a", "name": "Tenant A"})
    await client.post("/auth/tenants", json={"slug": "tenant-b", "name": "Tenant B"})

    await client.post(
        "/auth/register",
        json={"tenant_slug": "tenant-a", "email": "a@example.com", "full_name": "User A", "password": "StrongPass123", "role": "cfo"},
    )
    await client.post(
        "/auth/register",
        json={"tenant_slug": "tenant-b", "email": "b@example.com", "full_name": "User B", "password": "StrongPass123", "role": "cfo"},
    )

    login_a = await client.post("/auth/login", json={"tenant_slug": "tenant-a", "email": "a@example.com", "password": "StrongPass123"})
    token_a = login_a.json()["access_token"]
    login_b = await client.post("/auth/login", json={"tenant_slug": "tenant-b", "email": "b@example.com", "password": "StrongPass123"})
    token_b = login_b.json()["access_token"]

    await client.post("/projects", headers={"Authorization": f"Bearer {token_a}"}, json={"name": "Tenant A Project", "budget": "1000.00"})

    resp_a = await client.get("/projects", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = await client.get("/projects", headers={"Authorization": f"Bearer {token_b}"})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert resp_a.json()["total"] == 1
    assert resp_b.json()["total"] == 0
