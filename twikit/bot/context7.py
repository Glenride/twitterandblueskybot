"""Minimal async client for the Context7 API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class Context7Client:
    """Thin wrapper around the Context7 REST API."""

    def __init__(self, base_url: str, api_key: str) -> None:
        if not base_url:
            raise ValueError("Context7 base URL is required")
        if not api_key:
            raise ValueError("Context7 API key is required")
        base = base_url.rstrip("/")
        if not base.endswith("/api") and not base.endswith("/api/v1"):
            # Ensure we point at the versioned API root.
            if base.endswith("/v1"):
                base = f"{base}/api"
            else:
                base = f"{base}/api/v1"
        self._client = httpx.AsyncClient(base_url=base)
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._cache: dict[tuple[Any, ...], Any] = {}

    async def search(self, query: str) -> dict[str, Any]:
        """Run a library search and return the JSON payload."""
        cache_key = ("search", query)
        if cache_key in self._cache:
            return self._cache[cache_key]
        response = await self._client.get("/search", params={"query": query}, headers=self._headers)
        response.raise_for_status()
        payload = response.json()
        self._cache[cache_key] = payload
        return payload

    async def fetch_doc(
        self,
        path: str,
        *,
        response_type: str = "txt",
        topic: str | None = None,
        tokens: int | None = None,
    ) -> str:
        """Fetch documentation content for a given library path."""
        normalized = path if path.startswith("/") else f"/{path}"
        cache_key = ("doc", normalized, response_type, topic, tokens)
        if cache_key in self._cache:
            return self._cache[cache_key]
        params: dict[str, Any] = {"type": response_type}
        if topic:
            params["topic"] = topic
        if tokens is not None:
            params["tokens"] = str(tokens)
        response = await self._client.get(normalized, params=params, headers=self._headers)
        response.raise_for_status()
        if response_type == "json":
            payload: Any = response.json()
        else:
            payload = response.text
        self._cache[cache_key] = payload
        return payload

    async def aclose(self) -> None:
        await self._client.aclose()
