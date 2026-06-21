#!/usr/bin/env python3
"""Fetch today's Lightcone outcomes from Intend.do."""

import argparse
from datetime import date

from intend import (
    fetch_goals,
    fetch_intentions,
    filter_lightcone_items,
    get_auth_token,
    get_lightcone_goal_ids,
)


def is_day_summary(item: dict) -> bool:
    """Check if item is a 'Day summary' entry to skip."""
    text = item.get("t", "").strip().lower()
    return text == "day summary"


def get_item_goal_name(item: dict, goal_ids: list[tuple[str, str]]) -> str | None:
    """Return the goal name an item belongs to, if any."""
    gids = set(item.get("gids", []))
    for goal_id, name in goal_ids:
        if goal_id in gids:
            return name
    return None


def format_intend_slack(
    items: list[dict], today: str, goal_ids: list[tuple[str, str]] | None = None
) -> str:
    """Format Intend items as Slack mrkdwn."""
    goal_ids = goal_ids or []
    filtered = [item for item in items if not is_day_summary(item)]
    done_items = [item for item in filtered if item.get("d")]
    done = [item.get("t", "").strip() for item in done_items]
    not_done = [item.get("t", "").strip() for item in filtered if not item.get("d")]

    lines = []

    if done:
        day_of_week = date.fromisoformat(today).strftime("%A")
        lines.append(f"*Done this {day_of_week}:*")

        # Group done items by goal
        by_goal: dict[str, list[str]] = {}
        for item in done_items:
            name = get_item_goal_name(item, goal_ids) or ""
            by_goal.setdefault(name, []).append(item.get("t", "").strip())

        if len([g for g in by_goal if g]) > 1:
            # Split into per-goal subsections, preserving goal order
            for _, name in goal_ids:
                tasks = by_goal.get(name)
                if not tasks:
                    continue
                lines.append(f"_{name}_")
                for task in tasks:
                    lines.append(f"• {task}")
            # Any done items without a matched goal
            for task in by_goal.get("", []):
                lines.append(f"• {task}")
        else:
            for task in done:
                lines.append(f"• {task}")

    if not_done:
        if done:
            lines.append("")
        lines.append("*Not done:*")
        for task in not_done:
            lines.append(f"• {task}")

    if not done and not not_done:
        lines.append("_No Lightcone items today._")

    return "\n".join(lines)


def build_message(target_date: date | None = None) -> str:
    """Build the complete daily summary message."""
    today_date = target_date or date.today()
    today_str = today_date.isoformat()

    intend_token = get_auth_token()
    goal_map = fetch_goals(intend_token)
    goal_ids = get_lightcone_goal_ids(goal_map)

    if not goal_ids:
        return "Error: Could not find Lightcone goals"

    intentions = fetch_intentions(intend_token, today_str)
    items = filter_lightcone_items(intentions, goal_ids)

    return format_intend_slack(items, today_str, goal_ids)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Daily Lightcone work summary")
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
