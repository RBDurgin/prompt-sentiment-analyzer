---
description: Deep sentiment analysis and insights for Claude Code sessions
argument-hint: "[--session <id>] [--last <N>] [--all]"
allowed-tools: Bash, Read, Glob, Agent
---

Perform a deep narrative analysis of sentiment patterns across stored Claude Code session logs.

**Arguments:** $ARGUMENTS

## Steps

1. Use Bash to check that `~/.claude/sentiment-logs/` exists and has JSONL files:
   ```bash
   ls -t ~/.claude/sentiment-logs/*.jsonl 2>/dev/null | wc -l
   ```
   If no files found, tell the user to use Claude Code for a session first.

2. Determine scope:
   - `--all`: analyze every session file
   - `--last <N>`: analyze the N most recent sessions (default: 10)
   - `--session <id>`: analyze one specific session

3. Read the selected JSONL files and collect all session summaries and prompt records.

4. Launch the `sentiment-analyst` agent with the collected data to perform deep analysis.
   Pass the agent:
   - The list of session file paths to analyze
   - The argument scope (single session vs. multi-session)
   - Any specific question from the user's arguments (e.g., if the user typed `--session abc123 "Am I getting more frustrated?"`)

5. The sentiment-analyst agent will return a narrative report. Display it in full.
