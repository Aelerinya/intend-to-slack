"""Weekly recap script for CeSIA work summary."""

import argparse
from datetime import date, timedelta

from intend import (
    fetch_goals,
    fetch_weekly_remarks,
    get_auth_token,
    get_cesia_goal_id,
    get_goal_remarks,
    html_to_slack,
)
from toggl import (
    calculate_hours_by_project,
    fetch_projects,
    fetch_time_entries_range,
    fetch_workspace_id,
    format_duration,
    get_target_project_ids,
    get_toggl_token,
)


def get_previous_week_info(today: date | None = None) -> tuple[int, int, date, date]:
    """Calculate previous week's year, week number, and date range.

    Returns (year, week_number, start_date, end_date).
    Week starts on Monday, end_date is exclusive (following Sunday + 1 day).
    """
    if today is None:
        today = date.today()

    # Go back to previous week
    previous_week_date = today - timedelta(days=7)

    # Get ISO week info (year, week, weekday)
    year, week, _ = previous_week_date.isocalendar()

    # Calculate Monday of that week
    # isocalendar weekday: Monday=1, Sunday=7
    days_since_monday = previous_week_date.weekday()  # Monday=0, Sunday=6
    week_start = previous_week_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=7)  # Exclusive end (next Monday)

    return year, week, week_start, week_end


def format_date_range(start: date, end: date) -> str:
    """Format a date range as 'Mon DD - Mon DD' (end is exclusive, so subtract 1 day)."""
    actual_end = end - timedelta(days=1)  # Convert exclusive end to inclusive
    start_str = start.strftime("%b %d")
    end_str = actual_end.strftime("%b %d")
    return f"{start_str} - {end_str}"


def build_message() -> str:
    """Build the complete weekly recap message."""
    # Calculate previous week
    year, week, week_start, week_end = get_previous_week_info()
    date_range = format_date_range(week_start, week_end)

    parts = []

    # Header
    parts.append(f"*Weekly Recap - Week {week}, {year} ({date_range})*")

    # Fetch CeSIA remarks from Intend.do
    remarks_section = []
    try:
        intend_token = get_auth_token()
        goals = fetch_goals(intend_token)
        cesia_goal_id = get_cesia_goal_id(goals)

        if cesia_goal_id:
            remarks = fetch_weekly_remarks(intend_token, year, week)
            goal_remarks = get_goal_remarks(remarks, cesia_goal_id)
            if goal_remarks:
                remarks_section.append(html_to_slack(goal_remarks))
            else:
                remarks_section.append("_No review notes for this week._")
        else:
            remarks_section.append("_CeSIA goal not found._")
    except ValueError as e:
        remarks_section.append(f"_Error: {e}_")

    parts.append("\n".join(remarks_section))

    # Fetch Toggl hours
    toggl_lines = ["*Time Tracked*"]
    try:
        toggl_token = get_toggl_token()
        workspace_id = fetch_workspace_id(toggl_token)
        projects = fetch_projects(toggl_token, workspace_id)
        project_ids = get_target_project_ids(projects)

        if project_ids:
            entries = fetch_time_entries_range(toggl_token, week_start, week_end)
            hours_by_project = calculate_hours_by_project(entries, project_ids)

            total_seconds = 0
            for project_name, seconds in sorted(hours_by_project.items()):
                toggl_lines.append(f"• {project_name}: {format_duration(seconds)}")
                total_seconds += seconds

            toggl_lines.append(f"*Total: {format_duration(total_seconds)}*")
        else:
            toggl_lines.append("_No target projects found._")
    except ValueError as e:
        toggl_lines.append(f"_Error: {e}_")

    parts.append("\n".join(toggl_lines))

    return "\n\n".join(parts)


def main() -> None:
    """Generate weekly recap for CeSIA work (Slack mrkdwn format)."""
    parser = argparse.ArgumentParser(description="Weekly CeSIA work recap")
    parser.add_argument(
        "--slack", action="store_true", help="Post to Slack instead of stdout"
    )
    args = parser.parse_args()

    message = build_message()

    if args.slack:
        from slack import post_message

        post_message(message)
    else:
        print(message)


if __name__ == "__main__":
    main()
