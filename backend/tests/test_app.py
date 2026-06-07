import pytest
from httpx import ASGITransport, AsyncClient
from app import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_homepage_works(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    assert "王者荣耀世界" in r.text


async def test_pvp_page_works(client: AsyncClient):
    r = await client.get("/pvp")
    assert r.status_code == 200
    assert "PVP" in r.text


async def test_pve_page_works(client: AsyncClient):
    r = await client.get("/pve")
    assert r.status_code == 200
    assert "探索" in r.text


async def test_guide_detail_exists(client: AsyncClient):
    r = await client.get("/guide/pvp/1")
    assert r.status_code == 200
    assert "上官婉儿" in r.text


async def test_guide_detail_not_found(client: AsyncClient):
    r = await client.get("/guide/pvp/999")
    assert r.status_code == 404


async def test_partial_pvp_returns_cards(client: AsyncClient):
    r = await client.get("/partials/pvp?category=all")
    assert r.status_code == 200
    assert "card" in r.text


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
    assert len(data["items"]) > 0


async def test_api_list_codes(client: AsyncClient):
    r = await client.get("/api/codes")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) > 0


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


async def test_admin_auth_flow(client: AsyncClient):
    r = await client.post("/api/admin/login", json={"username": "admin", "password": "admin888"})
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    r2 = await client.get("/api/admin/stats", headers=headers)
    assert r2.status_code == 200
    stats = r2.json()
    assert "pvp_guides" in stats


async def test_admin_crud_flow(client: AsyncClient):
    r = await client.post("/api/admin/login", json={"username": "admin", "password": "admin888"})
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    r2 = await client.get("/api/admin/data/pvp_guides", headers=headers)
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) > 0
    assert items[0]["title"] == "上官婉儿"


async def test_admin_media_list(client: AsyncClient):
    r = await client.post("/api/admin/login", json={"username": "admin", "password": "admin888"})
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    r2 = await client.get("/api/admin/media", headers=headers)
    assert r2.status_code == 200
