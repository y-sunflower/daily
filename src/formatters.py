from typing import Any

COLOR_ISSUE_OPENED = 0x2CBE4E
COLOR_PR_OPENED = 0x0366D6
COLOR_PR_MERGED = 0x6F42C1
COLOR_PR_CLOSED = 0xCB2431

BODY_PREVIEW_CHARS = 280


def _truncate(text: str | None, n: int = BODY_PREVIEW_CHARS) -> str:
    if not text:
        return "_No description provided._"
    text = text.strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut + "…"


def _author_block(repo: dict[str, Any]) -> dict[str, str]:
    return {
        "name": repo["full_name"],
        "url": repo["html_url"],
        "icon_url": repo["owner"]["avatar_url"],
    }


def _user_field(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "Author",
        "value": f"[@{user['login']}]({user['html_url']})",
        "inline": True,
    }


def _labels_field(labels: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not labels:
        return None
    names = ", ".join(f"`{lbl['name']}`" for lbl in labels)
    return {"name": "Labels", "value": names, "inline": True}


def _build_fields(*items: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [item for item in items if item is not None]


def issue_opened(payload: dict[str, Any]) -> dict[str, Any]:
    issue = payload["issue"]
    repo = payload["repository"]
    return {
        "author": _author_block(repo),
        "title": f"🐛 Issue #{issue['number']}: {issue['title']}",
        "url": issue["html_url"],
        "color": COLOR_ISSUE_OPENED,
        "description": _truncate(issue.get("body")),
        "fields": _build_fields(
            _user_field(issue["user"]),
            _labels_field(issue.get("labels", [])),
        ),
        "timestamp": issue["created_at"],
    }


def pr_opened(payload: dict[str, Any]) -> dict[str, Any]:
    pr = payload["pull_request"]
    repo = payload["repository"]
    branches = {
        "name": "Branches",
        "value": f"`{pr['head']['ref']}` → `{pr['base']['ref']}`",
        "inline": True,
    }
    return {
        "author": _author_block(repo),
        "title": f"🔀 PR #{pr['number']}: {pr['title']}",
        "url": pr["html_url"],
        "color": COLOR_PR_OPENED,
        "description": _truncate(pr.get("body")),
        "fields": _build_fields(
            _user_field(pr["user"]),
            branches,
            _labels_field(pr.get("labels", [])),
        ),
        "timestamp": pr["created_at"],
    }


def pr_closed(payload: dict[str, Any]) -> dict[str, Any]:
    pr = payload["pull_request"]
    repo = payload["repository"]
    merged = bool(pr.get("merged"))
    if merged:
        emoji, color, verb = "🟣", COLOR_PR_MERGED, "merged"
    else:
        emoji, color, verb = "🔴", COLOR_PR_CLOSED, "closed"
    stats = {
        "name": "Changes",
        "value": f"+{pr.get('additions', 0)} −{pr.get('deletions', 0)} across {pr.get('changed_files', 0)} file(s)",
        "inline": True,
    }
    return {
        "author": _author_block(repo),
        "title": f"{emoji} PR #{pr['number']} {verb}: {pr['title']}",
        "url": pr["html_url"],
        "color": color,
        "description": _truncate(pr.get("body")),
        "fields": _build_fields(
            _user_field(pr["user"]),
            stats,
        ),
        "timestamp": pr["closed_at"] or pr["updated_at"],
    }


def format_event(event: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    action = payload.get("action")
    if event == "issues" and action == "opened":
        return issue_opened(payload)
    if event == "pull_request" and action == "opened":
        return pr_opened(payload)
    if event == "pull_request" and action == "closed":
        return pr_closed(payload)
    return None
