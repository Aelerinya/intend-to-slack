# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python CLI tools that fetch work data from Intend.do and Toggl APIs for the CeSIA goal (goal code "5") and output Slack-formatted summaries.

## Commands

```bash
uv sync                  # Install dependencies
uv run intend-summary    # Daily summary: today's tasks + time tracked
uv run weekly-recap      # Weekly summary: previous week's review notes + total hours
uv run daily-plan        # Daily plan: today's planned tasks
```

All commands support `--slack` flag to post directly to Slack instead of stdout:
```bash
uv run intend-summary --slack
uv run weekly-recap --slack
uv run daily-plan --slack
```

## Configuration

Store API tokens in `.env` at project root:
- `INTEND_AUTH_TOKEN` (required) - Intend.do API token
- `TOGGL_API_TOKEN` (optional) - Toggl time tracking token
- `SLACK_USER_TOKEN` (optional) - Slack user OAuth token (for `--slack` flag)
- `SLACK_CHANNEL` (optional) - Slack channel ID or name (for `--slack` flag)

### Setting up Slack integration

1. Create a Slack app using `slack-app-manifest.yaml`
2. Install the app to your workspace
3. Copy the User OAuth Token to `SLACK_USER_TOKEN` in `.env`
4. Set `SLACK_CHANNEL` to your target channel ID or name

## Architecture

Four modules with clear responsibilities:

- **intend.py** - Intend.do API: fetches goals, intentions, weekly remarks. Converts remarks HTML to Slack mrkdwn.
- **toggl.py** - Toggl API: fetches workspaces, projects, time entries. Filters for target projects ("charbel admin", "cesia freelance").
- **slack.py** - Slack API: posts messages using user token.
- **summary.py** - Daily report: combines today's Intend tasks with Toggl time.
- **weekly_recap.py** - Weekly report: previous week's review notes from Intend + total Toggl hours.
- **daily_plan.py** - Daily plan: today's planned tasks from Intend.

## Output Format

All output uses Slack mrkdwn (not standard markdown). See `slack-formatting.md` for reference. Key differences:
- Bold: `*text*` (not `**text**`)
- Italic: `_text_`
- No headers - use bold text instead
- Lists: literal bullet `•` or `-` characters

## API Reference

The `intend-api.txt` file contains full Intend.do API v0.5 documentation. Key endpoints:
- `GET /api/v0/u/me/goals/active.json` - goals with codes and IDs
- `GET /api/v0/u/me/today/core.json` - today's intentions
- `GET /api/v0/u/me/reviews/{year}/week/{week}/remarks.json` - weekly review notes
