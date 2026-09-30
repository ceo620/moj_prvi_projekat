import pytest


@pytest.mark.asyncio
async def test_viewer_cannot_create_project(client):
    await client.post("/auth/tenants", json={"slug": "tenant-viewer", "name": "Tenant Viewer"})
    await client.post(
        "/auth/register",
        json={
            "tenant_slug": "tenant-viewer",
            "email": "viewer@example.com",
            "full_name": "Viewer User",
            "password": "SuperPass123",
            "role": "viewer",
        },
    )
    login_response = await client.post(
        "/auth/login",
        json={"tenant_slug": "tenant-viewer", "email": "viewer@example.com", "password": "SuperPass123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/projects", headers=headers, json={"name": "Forbidden Project", "budget": "1000.00"})
    assert response.status_code == 403
