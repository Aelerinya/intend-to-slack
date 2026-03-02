"""Intend.do API functions for fetching intentions and goals."""

import os
import re

import httpx
from dotenv import load_dotenv

BASE_URL = "https://intend.do/api/v0/u/me"
CESIA_GOAL_NAME = "CeSIA"


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


def fetch_intentions(auth_token: str, ymd: str) -> list[dict]:
    """Fetch today's intentions from Intend.do API (including extra outcomes)."""
    url = f"{BASE_URL}/today/core.json"
    params = {"auth_token": auth_token}

    response = httpx.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    return data.get("list", [])


def get_cesia_goal_id(goal_map: dict[str, str]) -> str | None:
    """Find the goal ID for CeSIA by name."""
    for goal_id, name in goal_map.items():
        if name == CESIA_GOAL_NAME:
            return goal_id
    return None


def filter_cesia_items(items: list[dict], cesia_goal_id: str) -> list[dict]:
    """Filter items to only CeSIA-related items."""
    return [item for item in items if cesia_goal_id in item.get("gids", [])]


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
