from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(slots=True)
class BackendFile:
    filename: str
    content: bytes
    content_type: str


class BackendAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _base_url() -> str:
    return (os.getenv("BACKEND_API_URL") or os.getenv("BOT_BACKEND_API_URL") or "").rstrip("/")


def _token() -> str:
    return os.getenv("CLIENT_BOT_API_TOKEN") or ""


def is_configured() -> bool:
    return bool(_base_url() and _token())


def _headers(telegram_id: int) -> dict[str, str]:
    return {
        "Accept": "application/json, application/octet-stream, image/*, */*",
        "X-Client-Bot-Token": _token(),
        "X-Telegram-Id": str(telegram_id),
    }


def _request_json(path: str, telegram_id: int) -> Any:
    if not is_configured():
        raise BackendAPIError("Backend API не настроен. Укажите BACKEND_API_URL и CLIENT_BOT_API_TOKEN в .env бота.")
    request = Request(f"{_base_url()}{path}", headers=_headers(telegram_id), method="GET")
    try:
        with urlopen(request, timeout=25) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("detail") or raw
        except Exception:
            detail = raw or exc.reason
        raise BackendAPIError(str(detail), exc.code) from exc
    except URLError as exc:
        raise BackendAPIError(f"Не удалось подключиться к backend: {exc}") from exc


def _request_file(path: str, telegram_id: int, fallback_filename: str) -> BackendFile:
    if not is_configured():
        raise BackendAPIError("Backend API не настроен. Укажите BACKEND_API_URL и CLIENT_BOT_API_TOKEN в .env бота.")
    request = Request(f"{_base_url()}{path}", headers=_headers(telegram_id), method="GET")
    try:
        with urlopen(request, timeout=35) as response:
            content = response.read()
            content_type = response.headers.get("Content-Type") or "application/octet-stream"
            disposition = response.headers.get("Content-Disposition") or ""
            filename = fallback_filename
            if "filename=" in disposition:
                filename = disposition.split("filename=", 1)[1].split(";", 1)[0].strip('"') or filename
            return BackendFile(filename=filename, content=content, content_type=content_type)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("detail") or raw
        except Exception:
            detail = raw or exc.reason
        raise BackendAPIError(str(detail), exc.code) from exc
    except URLError as exc:
        raise BackendAPIError(f"Не удалось подключиться к backend: {exc}") from exc


async def get_my_wg_clients(telegram_id: int) -> dict[str, Any]:
    return await asyncio.to_thread(_request_json, "/client/wg-clients", telegram_id)


async def get_config(telegram_id: int, client_id: int) -> BackendFile:
    return await asyncio.to_thread(_request_file, f"/client/wg-clients/{client_id}/config", telegram_id, f"wg-client-{client_id}.conf")


async def get_qr(telegram_id: int, client_id: int) -> BackendFile:
    return await asyncio.to_thread(_request_file, f"/client/wg-clients/{client_id}/qr", telegram_id, f"wg-client-{client_id}-qr.svg")
