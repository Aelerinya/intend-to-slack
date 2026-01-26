# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that fetches intentions from the Intend.do API for a specific goal (CeSIA, goal code "4") and outputs a markdown summary of completed and incomplete tasks.

## Commands

**Install dependencies:**
```bash
uv sync
```

**Run the tool:**
```bash
uv run intend-summary
```

## Configuration

The tool requires an `INTEND_AUTH_TOKEN` environment variable. Store it in a `.env` file at the project root (this file is gitignored).

## Architecture

Single-file application (`summary.py`) with this flow:
1. Loads auth token from `.env` via `python-dotenv`
2. Fetches active goals from Intend.do API to find the CeSIA goal ID
3. Fetches today's intentions from the timeline API
4. Filters intentions to only those tagged with the CeSIA goal
5. Outputs markdown with "Done" and "Not done" sections

## Intend.do API Reference

The `intend-api.txt` file contains the full Intend.do API v0.5 documentation. Key endpoints used:
- `GET /api/v0/u/me/goals/active.json` - get goals with their codes and IDs
- `GET /api/v0/u/me/timeline/entries.json` - get intentions/outcomes for a date range
