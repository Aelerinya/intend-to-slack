"""Weekly recap script for Lightcone work summary."""

import argparse
from datetime import date, timedelta

from intend import (
    fetch_goals,
    fetch_weekly_remarks,
    get_auth_token,
    get_goal_remarks,
    get_lightcone_goal_ids,
    html_to_slack,
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

    # Fetch Lightcone remarks from Intend.do
    remarks_parts = []
    try:
        intend_token = get_auth_token()
        goals = fetch_goals(intend_token)
        goal_ids = get_lightcone_goal_ids(goals)

        if goal_ids:
            remarks = fetch_weekly_remarks(intend_token, year, week)
            for goal_id, goal_name in goal_ids:
                goal_remarks = get_goal_remarks(remarks, goal_id)
                if goal_remarks:
                    content = html_to_slack(goal_remarks)
                    if len(goal_ids) > 1:
                        remarks_parts.append(f"*{goal_name}*\n{content}")
                    else:
                        remarks_parts.append(content)

            if not remarks_parts:
                remarks_parts.append("_No review notes for this week._")
        else:
            remarks_parts.append("_Lightcone goals not found._")
    except ValueError as e:
        remarks_parts.append(f"_Error: {e}_")

    parts.append("\n\n".join(remarks_parts))

    return "\n\n".join(parts)


def main() -> None:
    """Generate weekly recap for Lightcone work (Slack mrkdwn format)."""
    parser = argparse.ArgumentParser(description="Weekly Lightcone work recap")
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
