---
description: View sentiment analysis dashboard for Claude Code sessions
argument-hint: "[--session <id>] [--last <N>]"
allowed-tools: Bash, Read, Glob
---

Display a sentiment analysis dashboard from stored session logs in `~/.claude/sentiment-logs/`.

**Arguments:** $ARGUMENTS

## Steps

1. Use Bash to list JSONL files in `~/.claude/sentiment-logs/` sorted by modification time (newest first):
   ```bash
   ls -t ~/.claude/sentiment-logs/*.jsonl 2>/dev/null
   ```
   If no files exist, inform the user that no sentiment data has been captured yet and that they need to use Claude Code with this plugin installed.

2. Determine which session files to display:
   - If `--session <id>` is provided, read only `~/.claude/sentiment-logs/<id>.jsonl`
   - If `--last <N>` is provided, read the N most recent files
   - Otherwise, default to the 5 most recent files

3. For each session file, parse every JSON line and extract:
   - The `session_start` record (if present) for context: `cwd`, `project_type`, `has_claude_md`
   - The `session_summary` record (if present) for aggregate stats
   - All `user_prompt` records for timeline view

4. Display a header:
   ```
   ╔══════════════════════════════════════════════════════════╗
   ║         CLAUDE CODE SESSION SENTIMENT DASHBOARD          ║
   ╚══════════════════════════════════════════════════════════╝
   ```

5. For each session, display a summary block:
   ```
   Session: <session_id> | <date from timestamp> | <project_type>
   Directory: <cwd>
   ─────────────────────────────────────────────────────────────
   Prompts:    <total_prompts>
   Valence:    [sentiment bar] <avg_valence> (😤 ← → 😊)
   Frustration: [bar] <avg_frustration>  Trajectory: <↑ increasing | → stable | ↓ decreasing>
   Urgency:    [bar] <avg_urgency>
   Confidence: [bar] <avg_confidence>
   Dominant:   <dominant_emotion>  |  Top intent: <most common intent_type>
   High-frustration prompts: <count>
   ```

   For bars, render a 10-character bar using █ and ░ characters based on the 0.0–1.0 score.
   For valence (which goes -1 to 1), center the scale: negative values fill left with red blocks (use ▓), positive fill right with █.

   Add a warning line if `avg_frustration > 0.6`: `⚠️  High frustration detected in this session`
   Add a note if `frustration_trajectory == "increasing"`: `📈 Frustration was increasing through the session`

6. If viewing a single session (`--session` flag), also show a prompt timeline:
   ```
   PROMPT TIMELINE
   ───────────────
   #1  [14:23:01]  bug_fix      frustrated  F:0.7 U:0.6  "How do I fix the TypeError in..."
   #2  [14:25:44]  question     curious     F:0.2 U:0.3  "What does this function actually..."
   ...
   ```
   Format: number, timestamp (time only), intent_type (padded), dominant_emotion (padded), F:<frustration> U:<urgency>, prompt_preview truncated to 50 chars.

7. Show intent type breakdown as a mini bar chart:
   ```
   INTENT TYPES
   bug_fix         ████████░░  8
   question        ██████░░░░  6
   feature_request ██░░░░░░░░  2
   ```

8. Print a footer summarizing across all displayed sessions:
   ```
   ─────────────────────────────────────────────────────────────
   SUMMARY ACROSS <N> SESSIONS
   Average frustration: <X>  |  Average valence: <X>
   Most frustrated session: <session_id> (<date>)
   ```
