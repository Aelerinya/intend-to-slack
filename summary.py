#!/usr/bin/env python3
"""Fetch today's CeSIA outcomes from Intend.do and Toggl time tracking."""

import argparse
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


def is_day_summary(item: dict) -> bool:
    """Check if item is a 'Day summary' entry to skip."""
    text = item.get("t", "").strip().lower()
    return text == "day summary"


def format_intend_slack(items: list[dict], today: str) -> str:
    """Format Intend items as Slack mrkdwn."""
    filtered = [item for item in items if not is_day_summary(item)]
    done = [item.get("t", "").strip() for item in filtered if item.get("d")]
    not_done = [item.get("t", "").strip() for item in filtered if not item.get("d")]

    lines = [f"*CeSIA Work - {today}*"]

    if done:
        lines.append("")
        lines.append("*Done:*")
        for task in done:
            lines.append(f"• {task}")

    if not_done:
        lines.append("")
        lines.append("*Not done:*")
        for task in not_done:
            lines.append(f"• {task}")

    if not done and not not_done:
        lines.append("")
        lines.append("_No CeSIA items today._")

    return "\n".join(lines)


def format_toggl_slack(hours_by_project: dict[str, int]) -> str:
    """Format Toggl time entries as Slack mrkdwn."""
    lines = ["*Time Tracked*"]

    has_time = False
    for project_name, seconds in sorted(hours_by_project.items()):
        if seconds > 0:
            has_time = True
            lines.append(f"• {project_name}: {format_duration(seconds)}")

    if not has_time:
        lines.append("_No time tracked today._")

    return "\n".join(lines)


def build_message(target_date: date | None = None) -> str:
    """Build the complete daily summary message."""
    today_date = target_date or date.today()
    today_str = today_date.isoformat()

    parts = []

    # Fetch Intend.do data
    intend_token = get_auth_token()
    goal_map = fetch_goals(intend_token)
    cesia_goal_id = get_cesia_goal_id(goal_map)

    if not cesia_goal_id:
        return "Error: Could not find CeSIA goal"

    intentions = fetch_intentions(intend_token, today_str)
    cesia_items = filter_cesia_items(intentions, cesia_goal_id)

    parts.append(format_intend_slack(cesia_items, today_str))

    # Fetch Toggl data
    try:
        toggl_token = get_toggl_token()
        workspace_id = fetch_workspace_id(toggl_token)
        projects = fetch_projects(toggl_token, workspace_id)
        target_project_ids = get_target_project_ids(projects)

        if target_project_ids:
            entries = fetch_time_entries(toggl_token, today_date)
            hours_by_project = calculate_hours_by_project(entries, target_project_ids)
            parts.append(format_toggl_slack(hours_by_project))
    except ValueError:
        # TOGGL_API_TOKEN not configured - skip Toggl section
        pass

    return "\n\n".join(parts)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Daily CeSIA work summary")
    parser.add_argument(
        "--slack", action="store_true", help="Post to Slack instead of stdout"
    )
    parser.add_argument(
        "--date", type=date.fromisoformat, metavar="YYYY-MM-DD",
        help="Date to summarize (default: today)"
    )
    args = parser.parse_args()

    message = build_message(args.date)

    if args.slack:
        from slack import post_message

        post_message(message)
    else:
        print(message)


if __name__ == "__main__":
    main()
