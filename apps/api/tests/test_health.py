import asyncio

import httpx

from clinic_api.main import app


def get(path: str) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.get(path)

    return asyncio.run(request())


def test_health_returns_ok() -> None:
    response = get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_api_path_does_not_expose_internal_details() -> None:
    response = get("/api/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    assert "traceback" not in response.text.lower()


def test_debug_mode_is_disabled() -> None:
    assert app.debug is False
