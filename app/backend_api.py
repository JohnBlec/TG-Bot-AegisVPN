from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import aiohttp


class BackendAPIError(Exception):
    pass


@dataclass(slots=True)
class BackendFile:
    content: bytes
    filename: str
    content_type: str


class BackendAPI:
    def __init__(self) -> None:
        self.base_url = (os.getenv("ADMIN_BACKEND_URL") or "").rstrip("/")
        self.token = os.getenv("CLIENT_BOT_API_TOKEN") or ""
        self.timeout = aiohttp.ClientTimeout(total=int(os.getenv("ADMIN_BACKEND_TIMEOUT", "30")))

    def _ensure_configured(self) -> None:
        if not self.base_url:
            raise BackendAPIError("Не задан ADMIN_BACKEND_URL в .env клиентского бота.")
        if not self.token:
            raise BackendAPIError("Не задан CLIENT_BOT_API_TOKEN в .env клиентского бота.")

    @property
    def headers(self) -> dict[str, str]:
        return {"X-Client-Bot-Token": self.token}

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/{path.lstrip('/')}"

    async def _request_json(self, path: str, telegram_id: int) -> dict[str, Any]:
        self._ensure_configured()
        url = self._url(path)
        params = {"telegram_id": str(telegram_id)}
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url, params=params, headers=self.headers) as response:
                data = await response.json(content_type=None)
                if response.status >= 400:
                    raise BackendAPIError(self._format_error(data))
                return data

    async def _request_file(self, path: str, telegram_id: int, filename: str) -> BackendFile:
        self._ensure_configured()
        url = self._url(path)
        params = {"telegram_id": str(telegram_id)}
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url, params=params, headers=self.headers) as response:
                content = await response.read()
                if response.status >= 400:
                    try:
                        data = await response.json(content_type=None)
                        raise BackendAPIError(self._format_error(data))
                    except BackendAPIError:
                        raise
                    except Exception:
                        raise BackendAPIError(content.decode("utf-8", errors="replace")[:500])
                return BackendFile(
                    content=content,
                    filename=filename,
                    content_type=response.headers.get("Content-Type", "application/octet-stream"),
                )

    @staticmethod
    def _format_error(data: Any) -> str:
        if isinstance(data, dict):
            if "customer" in data:
                return "К вашему Telegram-аккаунту пока не привязан клиент в админ-панели."
            if "token" in data:
                return "Ошибка авторизации клиентского бота в административном backend."
            return "; ".join(f"{key}: {value}" for key, value in data.items())
        return str(data)

    async def me(self, telegram_id: int) -> dict[str, Any]:
        return await self._request_json("client-bot/me", telegram_id)

    async def wg_client(self, telegram_id: int, client_id: int) -> dict[str, Any]:
        return await self._request_json(f"client-bot/wg-clients/{client_id}", telegram_id)

    async def config(self, telegram_id: int, client_id: int, wg_name: str) -> BackendFile:
        safe_name = quote(wg_name or f"wg-client-{client_id}")
        return await self._request_file(f"client-bot/wg-clients/{client_id}/config", telegram_id, f"{safe_name}.conf")

    async def config_text(self, telegram_id: int, client_id: int) -> str:
        data = await self._request_json(f"client-bot/wg-clients/{client_id}/config-text", telegram_id)
        return str(data.get("config") or "")

    async def qr(self, telegram_id: int, client_id: int, wg_name: str) -> BackendFile:
        safe_name = quote(wg_name or f"wg-client-{client_id}")
        return await self._request_file(f"client-bot/wg-clients/{client_id}/qr", telegram_id, f"{safe_name}-qr.svg")


backend_api = BackendAPI()
