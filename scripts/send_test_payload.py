"""Sign and POST a fixture against a running webhook server.

Usage:
    uv run python scripts/send_test_payload.py issue_opened
    uv run python scripts/send_test_payload.py pr_opened
    uv run python scripts/send_test_payload.py pr_merged
    uv run python scripts/send_test_payload.py pr_closed_unmerged

Reads GITHUB_WEBHOOK_SECRET from env (default "dev-secret"), and posts to
WEBHOOK_URL (default http://127.0.0.1:8000/api/webhook).
"""

import hashlib
import hmac
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

EVENT_BY_FIXTURE = {
    "issue_opened": "issues",
    "pr_opened": "pull_request",
    "pr_merged": "pull_request",
    "pr_closed_unmerged": "pull_request",
}

load_dotenv()


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in EVENT_BY_FIXTURE:
        print(f"choose one of: {', '.join(EVENT_BY_FIXTURE)}", file=sys.stderr)
        sys.exit(1)
    name = sys.argv[1]
    body = (FIXTURES / f"{name}.json").read_bytes()
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "dev-secret")
    url = os.environ.get("WEBHOOK_URL", "http://127.0.0.1:8000/api/webhook")
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    resp = httpx.post(
        url,
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": EVENT_BY_FIXTURE[name],
            "X-Hub-Signature-256": sig,
        },
        timeout=15.0,
    )
    print(f"{resp.status_code} {resp.text!r}")


if __name__ == "__main__":
    main()
