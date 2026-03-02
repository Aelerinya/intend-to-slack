"""Daily plan script for CeSIA work."""

import argparse
from datetime import date

from intend import (
    fetch_goals,
    fetch_intentions,
    filter_cesia_items,
    get_auth_token,
    get_cesia_goal_id,
)


def is_day_summary(item: dict) -> bool:
    """Check if item is a 'Day summary' entry to skip."""
    text = item.get("t", "").strip().lower()
    return text == "day summary"


def format_daily_plan_slack(items: list[dict], today: str) -> str:
    """Format intentions as Slack mrkdwn daily plan."""
    filtered = [item for item in items if not is_day_summary(item)]
    tasks = [item.get("t", "").strip() for item in filtered]

    lines = [f"*CeSIA Plan - {today}*"]

    if tasks:
        lines.append("")
        for task in tasks:
            lines.append(f"• {task}")
    else:
        lines.append("")
        lines.append("_No CeSIA items planned for today._")

    return "\n".join(lines)


def build_message() -> str:
    """Build the complete daily plan message."""
    today_date = date.today()
    today_str = today_date.isoformat()

    intend_token = get_auth_token()
    goal_map = fetch_goals(intend_token)
    cesia_goal_id = get_cesia_goal_id(goal_map)

    if not cesia_goal_id:
        return "Error: Could not find CeSIA goal"

    intentions = fetch_intentions(intend_token, today_str)
    cesia_items = filter_cesia_items(intentions, cesia_goal_id)

    return format_daily_plan_slack(cesia_items, today_str)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Daily CeSIA work plan")
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
