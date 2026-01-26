#!/usr/bin/env python3
"""Fetch today's CeSIA outcomes from Intend.do and Toggl time tracking."""

from datetime import date

from intend import (
    fetch_goals,
    fetch_intentions,
    filter_cesia_items,
    get_auth_token,
    get_cesia_goal_id,
)
from toggl import (
    calculate_hours_by_project,
    fetch_projects,
    fetch_time_entries,
    fetch_workspace_id,
    format_duration,
    get_target_project_ids,
    get_toggl_token,
)


def format_intend_markdown(items: list[dict], today: str) -> str:
    """Format Intend items as markdown."""
    done = [item.get("t", "").strip() for item in items if item.get("d")]
    not_done = [item.get("t", "").strip() for item in items if not item.get("d")]

    lines = [f"## CeSIA Work - {today}"]

    if done:
        lines.append("")
        lines.append("*Done:*")
        for task in done:
            lines.append(f"- {task}")

    if not_done:
        lines.append("")
        lines.append("*Not done:*")
        for task in not_done:
            lines.append(f"- {task}")

    if not done and not not_done:
        lines.append("")
        lines.append("_No CeSIA items today._")

    return "\n".join(lines)


def format_toggl_markdown(hours_by_project: dict[str, int], today: str) -> str:
    """Format Toggl time entries as markdown."""
    lines = [f"## Time Tracked"]
    lines.append("")

    has_time = False
    for project_name, seconds in sorted(hours_by_project.items()):
        if seconds > 0:
            has_time = True
            lines.append(f"- {project_name}: {format_duration(seconds)}")

    if not has_time:
        lines.append("_No time tracked today._")

    return "\n".join(lines)


def main():
    """Main entry point."""
    today_date = date.today()
    today_str = today_date.isoformat()

    # Fetch Intend.do data
    intend_token = get_auth_token()
    goal_map = fetch_goals(intend_token)
    cesia_goal_id = get_cesia_goal_id(goal_map)

    if not cesia_goal_id:
        print(f"Error: Could not find CeSIA goal")
        return

    intentions = fetch_intentions(intend_token, today_str)
    cesia_items = filter_cesia_items(intentions, cesia_goal_id)

    intend_markdown = format_intend_markdown(cesia_items, today_str)
    print(intend_markdown)

    # Fetch Toggl data
    try:
        toggl_token = get_toggl_token()
        workspace_id = fetch_workspace_id(toggl_token)
        projects = fetch_projects(toggl_token, workspace_id)
        target_project_ids = get_target_project_ids(projects)

        if target_project_ids:
            entries = fetch_time_entries(toggl_token, today_date)
            hours_by_project = calculate_hours_by_project(entries, target_project_ids)

            print()
            toggl_markdown = format_toggl_markdown(hours_by_project, today_str)
            print(toggl_markdown)
    except ValueError as e:
        # TOGGL_API_TOKEN not configured - skip Toggl section
        pass


if __name__ == "__main__":
    main()
