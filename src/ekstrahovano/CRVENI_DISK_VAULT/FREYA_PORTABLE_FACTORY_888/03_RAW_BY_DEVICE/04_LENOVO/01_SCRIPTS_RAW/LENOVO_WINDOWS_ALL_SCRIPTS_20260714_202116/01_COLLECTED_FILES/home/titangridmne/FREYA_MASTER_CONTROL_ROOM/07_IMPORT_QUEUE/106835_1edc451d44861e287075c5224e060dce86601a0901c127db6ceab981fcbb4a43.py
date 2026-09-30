import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    tenant_response = await client.post("/auth/tenants", json={"slug": "tenant-auth", "name": "Tenant Auth"})
    assert tenant_response.status_code == 201

    register_payload = {
        "tenant_slug": "tenant-auth",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "SuperPass123",
        "role": "admin",
    }
    register_response = await client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_payload = {"tenant_slug": "tenant-auth", "email": "admin@example.com", "password": "SuperPass123"}
    login_response = await client.post("/auth/login", json=login_payload)
    assert login_response.status_code == 200
    body = login_response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
