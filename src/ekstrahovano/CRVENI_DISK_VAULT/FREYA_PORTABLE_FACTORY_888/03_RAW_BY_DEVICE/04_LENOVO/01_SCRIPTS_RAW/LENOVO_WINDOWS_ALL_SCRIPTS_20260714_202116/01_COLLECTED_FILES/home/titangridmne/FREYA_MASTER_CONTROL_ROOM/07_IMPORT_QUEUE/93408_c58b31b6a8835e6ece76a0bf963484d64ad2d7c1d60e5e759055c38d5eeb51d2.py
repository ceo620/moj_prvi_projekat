import pytest


@pytest.mark.asyncio
async def test_create_and_list_projects(client):
    await client.post("/auth/tenants", json={"slug": "tenant-project", "name": "Tenant Project"})
    await client.post(
        "/auth/register",
        json={
            "tenant_slug": "tenant-project",
            "email": "cfo@example.com",
            "full_name": "CFO User",
            "password": "SuperPass123",
            "role": "cfo",
        },
    )
    login_response = await client.post(
        "/auth/login",
        json={"tenant_slug": "tenant-project", "email": "cfo@example.com", "password": "SuperPass123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post(
        "/projects",
        headers=headers,
        json={
            "name": "ARS Metal Industries",
            "description": "Transformer tank facility",
            "sponsor": "ARS",
            "sector": "Industrial",
            "country": "Montenegro",
            "currency": "EUR",
            "budget": "15000000.00",
            "status": "active",
        },
    )
    assert create_response.status_code == 201

    list_response = await client.get("/projects", headers=headers)
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "ARS Metal Industries"
