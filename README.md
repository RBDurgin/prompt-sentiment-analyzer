# Prompt Sentiment Analyzer

A Claude Code plugin that captures and analyzes the sentiment of your prompts in real-time, giving you insight into your emotional patterns when working with Claude Code.

## Installation

### From GitHub (recommended)

```bash
# 1. Add the marketplace from your GitHub repo
claude plugin marketplace add RBDurgin/prompt-sentiment-analyzer

# 2. Install the plugin
claude plugin install prompt-sentiment-analyzer
```

The marketplace add command accepts a GitHub repo in `owner/repo` format and fetches `.claude-plugin/marketplace.json` from it.

### For a single session only

To try the plugin without installing it permanently:

```bash
claude --plugin-dir /path/to/cloned/repo/plugins/prompt-sentiment-analyzer
```

## Uninstallation

```bash
# Uninstall the plugin
claude plugin uninstall prompt-sentiment-analyzer

# Optionally remove the marketplace if you no longer need other plugins from it
claude plugin marketplace remove RBDurgin/prompt-sentiment-analyzer
```

Uninstalling removes the hooks and commands but does **not** delete your existing session logs. To remove those:

```bash
rm -rf ~/.claude/sentiment-logs/
```

---

## ⚠️ Privacy Warning

This plugin logs data from your Claude Code sessions to `~/.claude/sentiment-logs/<session_id>.jsonl`, including:

- **The first 200 characters of every prompt you type** (stored as `prompt_preview`)
- **The first 500 characters of your `CLAUDE.md`** (stored as `claude_md_preview`)
- **Metadata about your system prompt** — presence, word count, and sentiment scores only; the system prompt text itself is sent to Claude for analysis at runtime but is **not** written to disk

Full prompt text and system prompt text are used for in-memory analysis only. However, if your prompts or `CLAUDE.md` contain sensitive information (API keys, PII, confidential business context), be aware that previews of that data will be written to disk in plaintext.

To stop logging, uninstall or disable this plugin.

---

## What It Does

Every prompt you submit is analyzed for:
- **Valence** (-1 to +1): Overall negative/positive tone
- **Frustration** (0–1): Level of frustration expressed
- **Urgency** (0–1): How time-pressured the request feels
- **Confidence** (0–1): How confident the user sounds
- **Clarity** (0–1): How clear and specific the request is
- **Dominant emotion**: frustrated / curious / confident / urgent / neutral / excited / confused
- **Intent type**: bug_fix / feature_request / question / exploration / other

At session start, it also analyzes your `CLAUDE.md` and any configured system prompts. At session end, it computes a summary with frustration trajectory (increasing/stable/decreasing).

Results are stored in `~/.claude/sentiment-logs/<session_id>.jsonl`.

## Commands

### `/prompt-sentiment-analyzer:view-sentiment`

Display a terminal dashboard of your recent sessions:

```
/prompt-sentiment-analyzer:view-sentiment
/prompt-sentiment-analyzer:view-sentiment --last 10
/prompt-sentiment-analyzer:view-sentiment --session <session_id>
```

Shows: session overview, sentiment bars, frustration trajectory, prompt timeline, and intent type breakdown.

**Example output:**

```
╔══════════════════════════════════════════════════════════╗
║         CLAUDE CODE SESSION SENTIMENT DASHBOARD          ║
╚══════════════════════════════════════════════════════════╝

Session: a3f9c2d1 | 2026-04-08 14:20 | python
Directory: ~/projects/my-api
─────────────────────────────────────────────────────────────
Prompts:     9
Valence:     ▓▓▓░░█████░  -0.12  (😤 ← → 😊)
Frustration: ████░░░░░░    0.41  → stable
Urgency:     █████░░░░░    0.52
Confidence:  ███████░░░    0.68
Dominant:    curious  |  Top intent: bug_fix
High-frustration prompts: 1
📈 Frustration was increasing through the session

PROMPT TIMELINE
───────────────
#1  [14:20:11]  question     curious     F:0.1 U:0.3  "How does the auth middleware han..."
#2  [14:23:44]  bug_fix      frustrated  F:0.7 U:0.8  "This keeps throwing a 401 even ..."
#3  [14:27:02]  bug_fix      curious     F:0.4 U:0.5  "Wait, is the token expiry set co..."
#4  [14:31:18]  question     confident   F:0.1 U:0.2  "Can you explain what this decode..."
#5  [14:35:50]  exploration  curious     F:0.2 U:0.3  "What would happen if we switched..."

INTENT TYPES
bug_fix         █████░░░░░  5
question        ████░░░░░░  3
exploration     █░░░░░░░░░  1
─────────────────────────────────────────────────────────────
SUMMARY ACROSS 1 SESSION
Average frustration: 0.41  |  Average valence: -0.12
```

### `/prompt-sentiment-analyzer:analyze-sentiment`

Deep narrative analysis using the `sentiment-analyst` agent:

```
/prompt-sentiment-analyzer:analyze-sentiment
/prompt-sentiment-analyzer:analyze-sentiment --last 20
/prompt-sentiment-analyzer:analyze-sentiment --session <id>
/prompt-sentiment-analyzer:analyze-sentiment --all
```

Produces a structured report with per-session breakdowns, cross-session trends, frustration triggers, and recommendations.

**Example output:**

```
## Session Sentiment Analysis

Analyzed: 3 sessions | 2026-04-06 → 2026-04-08

### Overview
Your recent sessions show a pattern of moderate frustration during debugging work that
resolves once the problem is identified. Confidence levels are generally high, suggesting
you have a clear sense of what you want — the friction is in execution, not direction.

### Per-Session Breakdown

- **2026-04-08 — python — ~/projects/my-api**
  - Prompts: 9 | Avg Frustration: 0.41 | Avg Valence: -0.12 | Trajectory: ↑ increasing
  - Dominant emotion: curious | Top intent: bug_fix
  - Frustration climbed steadily through the session, peaking around a 401 auth error.

- **2026-04-07 — nodejs — ~/projects/dashboard**
  - Prompts: 14 | Avg Frustration: 0.28 | Avg Valence: 0.31 | Trajectory: → stable
  - Dominant emotion: confident | Top intent: feature_request
  - Smooth session — mostly feature work with low friction.

- **2026-04-06 — python — ~/projects/my-api**
  - Prompts: 6 | Avg Frustration: 0.61 | Avg Valence: -0.44 | Trajectory: ↓ decreasing
  - Dominant emotion: frustrated | Top intent: bug_fix
  - ⚠️ High frustration session. Started rough but improved by the end.

### Key Insights
1. Bug-fix sessions average 0.51 frustration vs 0.22 for feature work — debugging is your main friction point.
2. Frustration consistently decreases once a root cause is identified (sessions end calmer than they start).
3. Your python project triggers more frustration than the nodejs one across both sessions.
4. Clarity scores are high (avg 0.74) — your prompts are well-formed even when frustrated.

### Frustration Triggers
The highest frustration prompts (F > 0.6) all involve authentication or unexpected errors
with little context. Prompts like "This keeps throwing a 401 even after..." suggest the
problem context isn't fully shared upfront.

### Recommendations
For **you**:
- When hitting a frustrating error, lead with the full error message and what you've
  already tried — this tends to get faster resolution and lower frustration scores.

For **Claude**:
- In bug_fix sessions where frustration is rising, proactively ask for error output
  and environment context rather than waiting to be asked.
```

## Hooks

The plugin registers three automatic hooks:

| Hook | Script | Purpose |
|------|--------|---------|
| `UserPromptSubmit` | `capture_prompt.py` | Analyze each prompt's sentiment |
| `SessionStart` | `capture_session_start.py` | Capture system context (CLAUDE.md, system prompt) |
| `SessionEnd` | `finalize_session.py` | Compute and store session summary |

All hooks are **non-blocking** — they always exit 0 and never delay your workflow.

One exception: if frustration exceeds 0.85, the `UserPromptSubmit` hook injects a gentle nudge into Claude's context suggesting it offer more help.

## Privacy

Only the first 200 characters of each prompt are stored (the `prompt_preview` field). The full prompt text is used for the in-memory sentiment analysis call but is never persisted to disk.

## Data Format

Session logs are JSONL files with three record types:

```jsonc
// session_start — one per session
{"event": "session_start", "session_id": "...", "timestamp": "...",
 "cwd": "...", "project_type": "nodejs|python|rust|...",
 "has_claude_md": true, "claude_md_preview": "...",
 "system_prompt_present": false, "system_prompt_sentiment": null}

// user_prompt — one per submitted prompt
{"event": "user_prompt", "session_id": "...", "timestamp": "...",
 "prompt_length": 87, "prompt_preview": "...",
 "sentiment": {"valence": -0.2, "urgency": 0.6, "frustration": 0.4,
   "confidence": 0.5, "clarity": 0.7,
   "dominant_emotion": "frustrated", "intent_type": "bug_fix"}}

// session_summary — one per session (appended at SessionEnd)
{"event": "session_summary", "session_id": "...", "timestamp": "...",
 "total_prompts": 12, "avg_valence": 0.15, "avg_frustration": 0.32,
 "avg_urgency": 0.48, "frustration_trajectory": "stable",
 "dominant_emotion": "curious",
 "intent_type_counts": {"bug_fix": 5, "question": 6, "other": 1},
 "high_frustration_prompts": 1}
```

## Requirements

- Claude Code CLI (`claude`) must be on your PATH (it is, since you're running Claude Code)
- Python 3.10+ (for the `str | None` type hints)
- No external Python packages required
