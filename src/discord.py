import asyncio
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


async def post_embed(webhook_url: str, embed: dict[str, Any]) -> None:
    payload = {"embeds": [embed]}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in (1, 2):
            try:
                resp = await client.post(webhook_url, json=payload)
            except httpx.HTTPError as exc:
                log.warning("discord post failed (attempt %d): %s", attempt, exc)
                if attempt == 2:
                    raise
                await asyncio.sleep(1)
                continue
            if resp.status_code < 400:
                return
            if 500 <= resp.status_code < 600 and attempt == 1:
                log.warning("discord 5xx (attempt %d): %s", attempt, resp.status_code)
                await asyncio.sleep(1)
                continue
            log.error("discord rejected payload: %s %s", resp.status_code, resp.text)
            return
