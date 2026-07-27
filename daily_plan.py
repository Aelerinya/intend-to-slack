"""Daily plan script for Lightcone work."""

import argparse
from datetime import date

from intend import (
    fetch_day_items,
    fetch_goals,
    filter_lightcone_items,
    get_auth_token,
    get_lightcone_goal_ids,
)


def is_day_summary(item: dict) -> bool:
    """Check if item is a 'Day summary' entry to skip."""
    text = item.get("t", "").strip().lower()
    return text == "day summary"


def format_daily_plan_slack(items: list[dict], today: str) -> str:
    """Format intentions as Slack mrkdwn daily plan."""
    filtered = [item for item in items if not is_day_summary(item)]
    tasks = [item.get("t", "").strip() for item in filtered]

    lines = [f"*Lightcone Plan - {today}*"]

    if tasks:
        lines.append("")
        for task in tasks:
            lines.append(f"• {task}")
    else:
        lines.append("")
        lines.append("_No Lightcone items planned for today._")

    return "\n".join(lines)


def build_message(target_date: date | None = None) -> str:
    """Build the complete daily plan message.

    With no target date, uses Intend's current day rather than the local
    calendar date, since Intend's day rolls over at the user's dayStartTime.
    """
    intend_token = get_auth_token()
    goal_map = fetch_goals(intend_token)
    goal_ids = get_lightcone_goal_ids(goal_map)

    if not goal_ids:
        return "Error: Could not find Lightcone goals"

    ymd, day_items = fetch_day_items(
        intend_token, target_date.isoformat() if target_date else None
    )
    items = filter_lightcone_items(day_items, goal_ids)

    return format_daily_plan_slack(items, ymd)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Daily Lightcone work plan")
    parser.add_argument(
        "--slack", action="store_true", help="Post to Slack instead of stdout"
    )
    parser.add_argument(
        "--date", type=date.fromisoformat, metavar="YYYY-MM-DD",
        help="Date to plan for (default: today)"
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
