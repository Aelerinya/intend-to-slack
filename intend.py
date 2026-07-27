"""Intend.do API functions for fetching intentions and goals."""

import os
import re
from datetime import date, timedelta

import httpx
from dotenv import load_dotenv

BASE_URL = "https://intend.do/api/v0/u/me"
LIGHTCONE_GOAL_NAMES = ["Lightcone"]


def get_auth_token() -> str:
    """Load auth token from environment."""
    load_dotenv()
    token = os.getenv("INTEND_AUTH_TOKEN")
    if not token:
        raise ValueError("INTEND_AUTH_TOKEN not found in .env file")
    return token


def fetch_goals(auth_token: str) -> dict[str, str]:
    """Fetch goals and return a mapping of goal ID to goal name."""
    url = f"{BASE_URL}/goals/active.json"
    params = {"auth_token": auth_token}

    response = httpx.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    goals = data.get("goals", [])

    return {goal["_id"]: goal["name"] for goal in goals}


def fetch_today_core(auth_token: str) -> dict:
    """Fetch the today page's core object (current day's merged item list).

    The `ymd` field is Intend's notion of "today", which follows the user's
    dayStartTime and can differ from the local calendar date (e.g. after
    midnight but before the day rolls over).
    """
    url = f"{BASE_URL}/today/core.json"
    params = {"auth_token": auth_token}

    response = httpx.get(url, params=params)
    response.raise_for_status()

    return response.json()


def fetch_timeline_entry(auth_token: str, ymd: str) -> dict | None:
    """Fetch a single past day's timeline entry, or None if there is no data."""
    next_day = (date.fromisoformat(ymd) + timedelta(days=1)).isoformat()
    url = f"{BASE_URL}/timeline/entries.json"
    # No `select`: its "+"-separated syntax gets percent-encoded and the API
    # then returns a stub entry. The default selection already covers what we
    # need (intentions and outcomes).
    params = {
        "auth_token": auth_token,
        "startymd": ymd,
        "endymd": next_day,  # endymd is exclusive
    }

    response = httpx.get(url, params=params)
    response.raise_for_status()

    for entry in response.json():
        if entry.get("ymd") == ymd:
            return entry
    return None


def merge_day_items(intentions: list[dict], outcomes: list[dict]) -> list[dict]:
    """Merge a past day's intentions and outcomes into one list, keyed by zid.

    A past day's outcomes carry the final done/not-done state and repeat the
    items that were planned, so outcomes win on conflict. Plan order is kept
    first, with items only recorded as outcomes appended after.
    """
    merged: dict[str, dict] = {}
    for item in [*intentions, *outcomes]:
        zid = item.get("zid") or item.get("_id", "")
        if zid in merged:
            merged[zid].update(item)
        else:
            merged[zid] = dict(item)
    return list(merged.values())


def fetch_day_items(auth_token: str, ymd: str | None = None) -> tuple[str, list[dict]]:
    """Fetch one day's items (intentions plus outcomes) from Intend.do.

    Pass `ymd` as YYYY-MM-DD for a specific day, or None for Intend's current
    day. Returns (ymd, items) so callers label the report with the date the
    data actually came from.

    The today page and the timeline are separate stores: the current day only
    exists on the today page, and past days are only complete in the timeline.
    """
    core = fetch_today_core(auth_token)
    current_ymd = core.get("ymd", "")

    if ymd is None or ymd == current_ymd:
        return current_ymd, _drop_blank(core.get("list", []))

    entry = fetch_timeline_entry(auth_token, ymd)
    if entry is None:
        return ymd, []

    items = merge_day_items(
        entry.get("intentions", {}).get("list", []) or [],
        entry.get("outcomes", {}).get("list", []) or [],
    )
    return ymd, _drop_blank(items)


def _drop_blank(items: list[dict]) -> list[dict]:
    """Drop the empty placeholder rows the timeline returns (blank text)."""
    return [item for item in items if item.get("t", "").strip()]


def get_lightcone_goal_ids(goal_map: dict[str, str]) -> list[tuple[str, str]]:
    """Find goal IDs for Lightcone goals by name.

    Returns a list of (goal_id, goal_name) tuples for matching goals.
    """
    return [
        (goal_id, name)
        for goal_id, name in goal_map.items()
        if name in LIGHTCONE_GOAL_NAMES
    ]


def filter_lightcone_items(items: list[dict], goal_ids: list[tuple[str, str]]) -> list[dict]:
    """Filter items to only Lightcone-related items (matching any goal ID)."""
    id_set = {goal_id for goal_id, _ in goal_ids}
    return [item for item in items if id_set.intersection(item.get("gids", []))]


def fetch_weekly_remarks(auth_token: str, year: int, week: int) -> dict:
    """Fetch weekly review remarks from Intend.do API.

    Returns the remarks data for the specified week, or empty dict if not found.
    """
    url = f"{BASE_URL}/reviews/{year}/week/{week}/remarks.json"
    params = {"auth_token": auth_token}

    response = httpx.get(url, params=params)
    if response.status_code == 404:
        return {}
    response.raise_for_status()

    return response.json()


def get_goal_remarks(remarks: dict, goal_id: str) -> str | None:
    """Extract remarks HTML for a specific goal from weekly review data."""
    remarks_list = remarks.get("remarks", [])
    for remark in remarks_list:
        if remark.get("tag") == goal_id:
            return remark.get("html")
    return None


def html_to_slack(html: str) -> str:
    """Convert Intend.do remarks HTML to Slack mrkdwn format."""
    lines = []

    # Extract h4 headers and make them bold
    # Pattern: <h4...>text</h4> followed by content until next h4 or end
    parts = re.split(r'<h4[^>]*>(.*?)</h4>', html)

    # parts[0] is before first h4 (usually empty)
    # parts[1] is first header, parts[2] is content after it, etc.
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""

        # Clean up the content
        # Replace <div><br></div> or <br> with newlines
        content = re.sub(r'<div><br\s*/?></div>', '\n', content)
        content = re.sub(r'<br\s*/?>', '\n', content)
        # Replace </div><div> with newline
        content = re.sub(r'</div>\s*<div>', '\n', content)
        # Remove remaining div tags
        content = re.sub(r'</?div>', '', content)
        # Clean up &nbsp;
        content = content.replace('&nbsp;', ' ')
        # Strip and skip if empty
        content = content.strip()

        if content:
            lines.append(f"*{header}*")
            lines.append(content)
            lines.append("")  # blank line between sections

    return "\n".join(lines).strip()
