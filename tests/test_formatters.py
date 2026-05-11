from src.formatters import (
    COLOR_ISSUE_CLOSED_COMPLETED,
    COLOR_ISSUE_CLOSED_NOT_PLANNED,
    COLOR_ISSUE_OPENED,
    COLOR_PR_CLOSED,
    COLOR_PR_MERGED,
    COLOR_PR_OPENED,
    format_event,
)


def test_issue_opened(load_fixture):
    embed = format_event("issues", load_fixture("issue_opened"))
    assert embed is not None
    assert embed["color"] == COLOR_ISSUE_OPENED
    assert embed["title"] == "🐛 Issue #42: Plots render blank on dark backgrounds"
    assert embed["url"] == "https://github.com/y-sunflower/morethemes/issues/42"
    assert embed["author"]["name"] == "y-sunflower/morethemes"
    assert embed["timestamp"] == "2026-05-11T10:23:00Z"
    field_names = [f["name"] for f in embed["fields"]]
    assert "Author" in field_names
    assert "Labels" in field_names
    labels_value = next(f["value"] for f in embed["fields"] if f["name"] == "Labels")
    assert "`bug`" in labels_value
    assert "`good first issue`" in labels_value


def test_issue_closed_completed(load_fixture):
    embed = format_event("issues", load_fixture("issue_closed_completed"))
    assert embed is not None
    assert embed["color"] == COLOR_ISSUE_CLOSED_COMPLETED
    assert embed["title"].startswith("✅ Issue #1 closed:")
    assert embed["timestamp"] == "2026-05-11T12:43:48Z"
    reason = next(f for f in embed["fields"] if f["name"] == "Reason")
    assert reason["value"] == "Completed"


def test_issue_closed_not_planned(load_fixture):
    embed = format_event("issues", load_fixture("issue_closed_not_planned"))
    assert embed is not None
    assert embed["color"] == COLOR_ISSUE_CLOSED_NOT_PLANNED
    assert embed["title"].startswith("🚫 Issue #7 closed:")
    reason = next(f for f in embed["fields"] if f["name"] == "Reason")
    assert reason["value"] == "Not planned"


def test_pr_opened(load_fixture):
    embed = format_event("pull_request", load_fixture("pr_opened"))
    assert embed is not None
    assert embed["color"] == COLOR_PR_OPENED
    assert embed["title"].startswith("🔀 PR #17")
    branches = next(f for f in embed["fields"] if f["name"] == "Branches")
    assert branches["value"] == "`feature/dark-themes` → `main`"


def test_pr_merged(load_fixture):
    embed = format_event("pull_request", load_fixture("pr_merged"))
    assert embed is not None
    assert embed["color"] == COLOR_PR_MERGED
    assert "merged" in embed["title"]
    assert embed["title"].startswith("🟣")
    changes = next(f for f in embed["fields"] if f["name"] == "Changes")
    assert "+120" in changes["value"]
    assert "−8" in changes["value"]


def test_pr_closed_unmerged(load_fixture):
    embed = format_event("pull_request", load_fixture("pr_closed_unmerged"))
    assert embed is not None
    assert embed["color"] == COLOR_PR_CLOSED
    assert embed["title"].startswith("🔴")
    assert "closed" in embed["title"]
    assert embed["description"] == "_No description provided._"


def test_ignored_actions_return_none(load_fixture):
    payload = load_fixture("issue_opened")
    payload["action"] = "edited"
    assert format_event("issues", payload) is None
    assert format_event("issue_comment", payload) is None
    assert format_event("push", {}) is None


def test_long_body_truncated(load_fixture):
    payload = load_fixture("issue_opened")
    payload["issue"]["body"] = "word " * 200
    embed = format_event("issues", payload)
    assert embed is not None
    assert embed["description"].endswith("…")
    assert len(embed["description"]) <= 281
