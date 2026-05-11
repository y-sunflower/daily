import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request, Response

from src.discord import post_embed
from src.formatters import format_event
from src.verify import verify_signature

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI()

load_dotenv()


@app.get("/api/webhook")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/webhook")
async def webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> Response:
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    discord_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not secret or not discord_url:
        log.error("missing env: GITHUB_WEBHOOK_SECRET or DISCORD_WEBHOOK_URL")
        raise HTTPException(status_code=500, detail="server not configured")

    body = await request.body()
    if not verify_signature(body, x_hub_signature_256, secret):
        raise HTTPException(status_code=401, detail="invalid signature")

    if x_github_event == "ping":
        return Response(status_code=204)

    payload = await request.json()
    embed = format_event(x_github_event or "", payload)
    if embed is None:
        return Response(status_code=204)

    await post_embed(discord_url, embed)
    return Response(status_code=204)
