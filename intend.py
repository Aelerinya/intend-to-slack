"""Intend.do API functions for fetching intentions and goals."""

import os

import httpx
from dotenv import load_dotenv

BASE_URL = "https://intend.do/api/v0/u/me"
CESIA_GOAL_CODE = "4"


def get_auth_token() -> str:
    """Load auth token from environment."""
    load_dotenv()
    token = os.getenv("INTEND_AUTH_TOKEN")
    if not token:
        raise ValueError("INTEND_AUTH_TOKEN not found in .env file")
    return token


def fetch_goals(auth_token: str) -> dict[str, str]:
    """Fetch goals and return a mapping of goal ID to goal code."""
    url = f"{BASE_URL}/goals/active.json"
    params = {"auth_token": auth_token}

    response = httpx.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    goals = data.get("goals", [])

    return {goal["_id"]: goal["code"] for goal in goals}


def fetch_intentions(auth_token: str, ymd: str) -> list[dict]:
    """Fetch today's intentions from Intend.do API."""
    url = f"{BASE_URL}/timeline/entries.json"
    params = {
        "auth_token": auth_token,
        "select": "intentions",
        "startymd": ymd,
        "limit": 1,
    }

    response = httpx.get(url, params=params)
    response.raise_for_status()

    entries = response.json()
    if not entries:
        return []

    return entries[0].get("intentions", {}).get("list", [])


def get_cesia_goal_id(goal_map: dict[str, str]) -> str | None:
    """Find the goal ID for CeSIA (goal code 4)."""
    for goal_id, code in goal_map.items():
        if code == CESIA_GOAL_CODE:
            return goal_id
    return None


def filter_cesia_items(items: list[dict], cesia_goal_id: str) -> list[dict]:
    """Filter items to only CeSIA-related items."""
    return [item for item in items if cesia_goal_id in item.get("gids", [])]
