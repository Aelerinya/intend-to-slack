"""Toggl API functions for fetching time entries."""

import os
from datetime import date, datetime, timedelta

import httpx
from dotenv import load_dotenv

TOGGL_API_URL = "https://api.track.toggl.com/api/v9"
TARGET_PROJECTS = ["charbel admin", "cesia freelance"]


def get_toggl_token() -> str:
    """Load Toggl API token from environment."""
    load_dotenv()
    token = os.getenv("TOGGL_API_TOKEN")
    if not token:
        raise ValueError("TOGGL_API_TOKEN not found in .env file")
    return token


def _get_auth(token: str) -> tuple[str, str]:
    """Return basic auth tuple for Toggl API (token as username, 'api_token' as password)."""
    return (token, "api_token")


def fetch_workspace_id(token: str) -> int:
    """Fetch the default workspace ID for the user."""
    url = f"{TOGGL_API_URL}/me"
    response = httpx.get(url, auth=_get_auth(token))
    response.raise_for_status()
    data = response.json()
    return data["default_workspace_id"]


def fetch_projects(token: str, workspace_id: int) -> list[dict]:
    """Fetch all projects for a workspace."""
    url = f"{TOGGL_API_URL}/workspaces/{workspace_id}/projects"
    response = httpx.get(url, auth=_get_auth(token))
    response.raise_for_status()
    return response.json() or []


def fetch_time_entries(token: str, target_date: date) -> list[dict]:
    """Fetch time entries for a specific date."""
    # Toggl API uses ISO 8601 format with timezone
    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)

    url = f"{TOGGL_API_URL}/me/time_entries"
    params = {
        "start_date": start.isoformat() + "Z",
        "end_date": end.isoformat() + "Z",
    }

    response = httpx.get(url, auth=_get_auth(token), params=params)
    response.raise_for_status()
    return response.json() or []


def get_target_project_ids(projects: list[dict]) -> dict[int, str]:
    """Find project IDs for target projects (case-insensitive).

    Returns a mapping of project_id -> project_name for matched projects.
    """
    result = {}
    for project in projects:
        project_name = project.get("name", "")
        if project_name.lower() in [p.lower() for p in TARGET_PROJECTS]:
            result[project["id"]] = project_name
    return result


def calculate_hours_by_project(
    entries: list[dict], project_ids: dict[int, str]
) -> dict[str, int]:
    """Calculate total seconds per project for target projects.

    Returns a mapping of project_name -> total_seconds.
    """
    result = {name: 0 for name in project_ids.values()}

    for entry in entries:
        project_id = entry.get("project_id")
        if project_id in project_ids:
            duration = entry.get("duration", 0)
            # Negative duration means the timer is still running
            if duration > 0:
                result[project_ids[project_id]] += duration

    return result


def format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration (e.g., '2h 30m')."""
    if seconds == 0:
        return "0m"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else "0m"
