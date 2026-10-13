"""Webhook notifier for scheduler alerts."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from httpx import AsyncClient, HTTPError

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NotifierConfig:
    url: str
    secret: Optional[str]
    retries: int
    backoff_seconds: int


class WebhookNotifier:
    def __init__(self, config: NotifierConfig) -> None:
        self.config = config
        self._client = AsyncClient(timeout=10.0)

    async def send(self, event: str, payload: Dict[str, Any]) -> None:
        attempt = 0
        exc: Exception | None = None
        while attempt <= self.config.retries:
            if attempt:
                await asyncio.sleep(self.config.backoff_seconds)
            attempt += 1
            try:
                await self._post(event, payload)
                return
            except HTTPError as err:
                exc = err
                logger.exception("Failed to deliver webhook (attempt %s): %s", attempt, err)

        if exc is not None:
            raise exc

    async def _post(self, event: str, payload: Dict[str, Any]) -> None:
        headers = {
            "Content-Type": "application/json",
            "X-Scheduler-Event": event,
        }
        if self.config.secret:
            headers["X-Webhook-Secret"] = self.config.secret
        body = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": payload,
        }
        response = await self._client.post(self.config.url, content=json.dumps(body), headers=headers)
        response.raise_for_status()

    async def aclose(self) -> None:
        await self._client.aclose()
