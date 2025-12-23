import pytest
import httpx

from server.app.main import app
from server.utils.security import utils as security_utils


@pytest.mark.anyio
async def test_admin_redirects_when_unauthenticated(monkeypatch):
    async def fake_check(_request):
        return {"authorized": False, "user_id": None, "payload": None}

    monkeypatch.setattr(security_utils, "check_if_user_authorized", fake_check)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/admin", follow_redirects=False)

    assert resp.status_code in (302, 303)
    assert resp.headers.get("location") == "/login"


@pytest.mark.anyio
async def test_admin_forbidden_when_not_superuser(monkeypatch):
    async def fake_check(_request):
        return {"authorized": True, "user_id": 1, "payload": {"sub": "1"}}

    class FakeUser:
        id = 1
        email = "user@example.com"
        username = "user"
        is_superuser = False

    async def fake_get_by_id(_db, _user_id):
        return FakeUser()

    monkeypatch.setattr(security_utils, "check_if_user_authorized", fake_check)

    # Patch where it is imported/used in the route module
    import server.app.api.admin as admin_module

    monkeypatch.setattr(admin_module, "async_get_by_id", fake_get_by_id)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/admin")

    assert resp.status_code == 403
