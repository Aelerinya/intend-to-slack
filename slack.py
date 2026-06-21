"""Slack API integration for posting messages."""

import os

import httpx
from dotenv import load_dotenv


def get_slack_token() -> str:
    """Load Slack user token from environment.

    Raises:
        ValueError: If SLACK_USER_TOKEN is not set.
    """
    load_dotenv()
    token = os.getenv("SLACK_USER_TOKEN")
    if not token:
        raise ValueError("SLACK_USER_TOKEN environment variable is not set")
    return token


def get_slack_channel() -> str:
    """Load Slack channel from environment.

    Raises:
        ValueError: If SLACK_CHANNEL is not set.
    """
    load_dotenv()
    channel = os.getenv("SLACK_CHANNEL")
    if not channel:
        raise ValueError("SLACK_CHANNEL environment variable is not set")
    return channel


def post_message(text: str) -> None:
    """Post a message to Slack.

    Args:
        text: The message text (Slack mrkdwn format).

    Raises:
        ValueError: If Slack credentials are not configured.
        RuntimeError: If the Slack API returns an error.
    """
    token = get_slack_token()
    channel = get_slack_channel()

    # Add bot attribution note with a ping to verify the content.
    text_with_note = (
        f"{text}\n\n"
        "<@U07NF53BXK7> _Posted automatically via intend-to-slack — "
        "please verify the content and edit if needed._"
    )

    response = httpx.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "text": text_with_note},
    )

    data = response.json()
    if not data.get("ok"):
        error = data.get("error", "Unknown error")
        raise RuntimeError(f"Slack API error: {error}")

    print("Message sent to Slack successfully.")
