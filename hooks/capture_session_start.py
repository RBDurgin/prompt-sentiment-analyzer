#!/usr/bin/env python3
"""
SessionStart hook for prompt-sentiment-analyzer plugin.
Captures system context: CLAUDE.md content, project type, system prompt from settings.
Non-blocking: always exits 0.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone


LOG_DIR = os.path.expanduser("~/.claude/sentiment-logs")
_SENTINEL_ENV = "CLAUDE_SENTIMENT_ANALYZING"


def find_claude_md(cwd: str) -> str | None:
    """Walk up directory tree from cwd to find CLAUDE.md."""
    path = os.path.abspath(cwd)
    while True:
        candidate = os.path.join(path, "CLAUDE.md")
        if os.path.exists(candidate):
            try:
                with open(candidate) as f:
                    return f.read()
            except IOError:
                return None
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    # Also check global ~/.claude/CLAUDE.md
    global_candidate = os.path.expanduser("~/.claude/CLAUDE.md")
    if os.path.exists(global_candidate):
        try:
            with open(global_candidate) as f:
                return f.read()
        except IOError:
            pass
    return None


def get_system_prompt(cwd: str) -> str | None:
    """Read system prompt from settings files (project-level takes precedence)."""
    candidates = [
        os.path.join(cwd, ".claude", "settings.json"),
        os.path.expanduser("~/.claude/settings.json"),
    ]
    for settings_path in candidates:
        if os.path.exists(settings_path):
            try:
                with open(settings_path) as f:
                    settings = json.load(f)
                system_prompt = settings.get("systemPrompt")
                if system_prompt:
                    return system_prompt
            except (json.JSONDecodeError, IOError):
                pass
    return None


def analyze_system_prompt_sentiment(text: str) -> dict | None:
    """Analyze sentiment of a system prompt using claude -p."""
    analysis_prompt = (
        "Analyze the tone and sentiment of this system prompt for an AI coding assistant. "
        "Return ONLY a valid JSON object with no markdown fences:\n"
        '{"valence": <float -1.0 to 1.0>, '
        '"formality": <float 0.0 to 1.0>, '
        '"restrictiveness": <float 0.0 to 1.0, how many constraints are imposed>, '
        '"dominant_tone": <one word: professional|casual|strict|permissive|educational|neutral>, '
        '"primary_purpose": <one of: security|style|workflow|context|other>}\n\n'
        f"System prompt:\n{text[:2000]}"
    )
    env = {**os.environ, _SENTINEL_ENV: "1"}
    try:
        result = subprocess.run(
            [
                "claude",
                "-p",
                analysis_prompt,
                "--model",
                "claude-haiku-4-5-20251001",
                "--output-format",
                "text",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
        if result.returncode != 0:
            return None
        text_out = result.stdout.strip()
        if text_out.startswith("```"):
            lines = text_out.split("\n")
            text_out = "\n".join(lines[1:-1]) if len(lines) > 2 else text_out
        return json.loads(text_out)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def detect_project_type(cwd: str) -> str:
    markers = {
        "nodejs": ["package.json"],
        "python": ["pyproject.toml", "setup.py", "requirements.txt"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod"],
        "java": ["pom.xml", "build.gradle"],
        "ruby": ["Gemfile"],
    }
    for project_type, files in markers.items():
        for f in files:
            if os.path.exists(os.path.join(cwd, f)):
                return project_type
    return "unknown"


def main():
    # Prevent infinite recursion: this hook calls `claude -p`, which is itself a
    # Claude Code session and would re-fire SessionStart. Bail out if we're
    # already inside a sentiment analysis subprocess.
    if os.environ.get(_SENTINEL_ENV):
        sys.exit(0)

    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    cwd = input_data.get("cwd", os.getcwd())

    claude_md_content = find_claude_md(cwd)
    system_prompt = get_system_prompt(cwd)
    system_prompt_sentiment = None
    if system_prompt:
        system_prompt_sentiment = analyze_system_prompt_sentiment(system_prompt)

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{session_id}.jsonl")

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "event": "session_start",
        "cwd": cwd,
        "project_type": detect_project_type(cwd),
        "has_claude_md": claude_md_content is not None,
        "claude_md_word_count": len(claude_md_content.split()) if claude_md_content else 0,
        "claude_md_preview": claude_md_content[:500] if claude_md_content else None,
        "system_prompt_present": system_prompt is not None,
        "system_prompt_word_count": len(system_prompt.split()) if system_prompt else 0,
        "system_prompt_sentiment": system_prompt_sentiment,
    }

    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except IOError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
