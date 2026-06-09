import pytest
from httpx import AsyncClient


async def test_homepage_works(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200


async def test_pvp_page_works(client: AsyncClient):
    r = await client.get("/pvp")
    assert r.status_code == 200


async def test_pve_page_works(client: AsyncClient):
    r = await client.get("/pve")
    assert r.status_code == 200


async def test_guide_detail_not_found(client: AsyncClient):
    r = await client.get("/guide/pvp/999")
    assert r.status_code == 404


async def test_partial_pvp_returns_cards(client: AsyncClient):
    r = await client.get("/partials/pvp?category=all")
    assert r.status_code == 200


async def test_partial_hero_works(client: AsyncClient):
    r = await client.get("/partials/hero")
    assert r.status_code == 200


async def test_partial_codes_works(client: AsyncClient):
    r = await client.get("/partials/codes")
    assert r.status_code == 200


async def test_partial_quickref_works(client: AsyncClient):
    r = await client.get("/partials/quickref")
    assert r.status_code == 200


async def test_api_list_pvp(client: AsyncClient):
    r = await client.get("/api/pvp")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


async def test_api_list_codes(client: AsyncClient):
    r = await client.get("/api/codes")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


async def test_admin_requires_auth(client: AsyncClient):
    r = await client.get("/api/admin/stats")
    assert r.status_code == 401


async def test_admin_login_wrong_password(client: AsyncClient):
    r = await client.post("/api/admin/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


async def test_admin_login_success(client: AsyncClient):
    r = await client.post("/api/admin/login", json={"username": "admin", "password": "admin888"})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "token" in data


async def test_admin_auth_flow(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/admin/stats", headers=auth_headers)
    assert r.status_code == 200
    stats = r.json()
    assert "pvp_guides" in stats


async def test_admin_crud_flow(client: AsyncClient, auth_headers: dict):
    # Create a guide
    r = await client.post("/api/admin/pvp_guides", headers=auth_headers, json={
        "title": "Test Guide",
        "description": "Test description",
        "category": "general",
        "sort_order": 0,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    item_id = data["id"]

    # List guides (paginated)
    r = await client.get("/api/admin/data/pvp_guides", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["total_pages"] == 1
    assert body["items"][0]["title"] == "Test Guide"

    # Update guide
    r = await client.put(f"/api/admin/pvp_guides/{item_id}", headers=auth_headers, json={
        "title": "Updated Guide",
    })
    assert r.status_code == 200

    # Delete guide
    r = await client.delete(f"/api/admin/pvp_guides/{item_id}", headers=auth_headers)
    assert r.status_code == 200

    # Verify deleted
    r = await client.get("/api/admin/data/pvp_guides", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert len(body["items"]) == 0


async def test_admin_media_list(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/admin/media", headers=auth_headers)
    assert r.status_code == 200


async def test_health_endpoint(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


async def test_admin_pagination(client: AsyncClient, auth_headers: dict):
    # Create 3 items
    for i in range(3):
        r = await client.post("/api/admin/pvp_guides", headers=auth_headers, json={
            "title": f"Guide {i}", "category": "general", "sort_order": i,
        })
        assert r.status_code == 200

    # Page 1 with page_size=2
    r = await client.get("/api/admin/data/pvp_guides?page=1&page_size=2", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2

    # Page 2
    r = await client.get("/api/admin/data/pvp_guides?page=2&page_size=2", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 1


async def test_admin_audit_log(client: AsyncClient, auth_headers: dict):
    # Create then delete an item to generate audit logs
    r = await client.post("/api/admin/pvp_guides", headers=auth_headers, json={
        "title": "Audit Test", "category": "general", "sort_order": 0,
    })
    assert r.status_code == 200
    item_id = r.json()["id"]

    await client.delete(f"/api/admin/pvp_guides/{item_id}", headers=auth_headers)

    # Check stats include audit logs
    r = await client.get("/api/admin/stats", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "logs" in data
    log_actions = [log["action"] for log in data["logs"]]
    assert "create" in log_actions
    assert "delete" in log_actions


async def test_admin_xss_sanitization(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/admin/pvp_guides", headers=auth_headers, json={
        "title": "<script>alert('xss')</script>Safe Title",
        "description": "<img onerror=alert(1) src=x>Desc",
        "content": "<p>Safe content</p><script>bad</script>",
        "category": "general",
        "sort_order": 0,
    })
    assert r.status_code == 200
    item_id = r.json()["id"]

    r = await client.get("/api/admin/data/pvp_guides", headers=auth_headers)
    body = r.json()
    item = next(i for i in body["items"] if i["id"] == item_id)
    assert "<script>" not in item["title"]
    assert "<script>" not in item["description"]
    assert "<script>" not in item["content"]
    assert "<p>Safe content</p>" in item["content"]
