import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request, Response

from src.discord import post_embed
from src.formatters import format_event
from src.verify import verify_signature

logging.basicConfig(level=logging.INFO, force=True)
log = logging.getLogger("webhook")
log.setLevel(logging.INFO)

app = FastAPI()

load_dotenv()


@app.get("/api/webhook")
async def health() -> dict[str, object]:
    log.info("Checking...")
    return {
        "status": "ok",
        "secret_configured": bool(os.environ.get("GITHUB_WEBHOOK_SECRET")),
        "discord_configured": bool(os.environ.get("DISCORD_WEBHOOK_URL")),
    }


@app.post("/api/webhook")
async def webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
) -> Response:
    log.info(
        "incoming webhook delivery=%s event=%s sig_present=%s",
        x_github_delivery,
        x_github_event,
        bool(x_hub_signature_256),
    )

    secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    discord_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not secret or not discord_url:
        log.error(
            "missing env: secret=%s discord=%s",
            bool(secret),
            bool(discord_url),
        )
        raise HTTPException(status_code=500, detail="server not configured")

    body = await request.body()
    if not verify_signature(body, x_hub_signature_256, secret):
        log.warning("signature verification failed (delivery=%s)", x_github_delivery)
        raise HTTPException(status_code=401, detail="invalid signature")
    log.info("signature ok (delivery=%s)", x_github_delivery)

    if x_github_event == "ping":
        log.info("ping received (delivery=%s)", x_github_delivery)
        return Response(status_code=204)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        log.error("invalid JSON body: %s", exc)
        raise HTTPException(status_code=400, detail="invalid json")

    action = payload.get("action")
    repo = payload.get("repository", {}).get("full_name", "?")
    log.info(
        "parsed payload event=%s action=%s repo=%s delivery=%s",
        x_github_event,
        action,
        repo,
        x_github_delivery,
    )

    embed = format_event(x_github_event or "", payload)
    if embed is None:
        log.info(
            "no formatter for event=%s action=%s (ignored)",
            x_github_event,
            action,
        )
        return Response(status_code=204)

    log.info("posting embed to discord (title=%r)", embed.get("title"))
    await post_embed(discord_url, embed)
    log.info("discord post complete (delivery=%s)", x_github_delivery)
    return Response(status_code=204)
