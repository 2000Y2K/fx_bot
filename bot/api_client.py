import aiohttp
from typing import Any


class APIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"API {status}: {message}")


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def get(self, path: str) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{path}") as r:
                if r.status >= 400:
                    raise APIError(r.status, await r.text())
                return await r.json()

    async def post(self, path: str, body: dict) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}{path}", json=body) as r:
                if r.status >= 400:
                    raise APIError(r.status, await r.text())
                return await r.json()

    async def patch(self, path: str, body: dict) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.patch(f"{self.base_url}{path}", json=body) as r:
                if r.status >= 400:
                    raise APIError(r.status, await r.text())
                return await r.json()