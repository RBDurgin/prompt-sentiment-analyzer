#!/usr/bin/env python3
"""
UserPromptSubmit hook for prompt-sentiment-analyzer plugin.
Captures each user prompt and analyzes its sentiment using Claude Haiku.
Results are appended to ~/.claude/sentiment-logs/<session_id>.jsonl.
Non-blocking: always exits 0. If frustration is very high, injects a systemMessage.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone


LOG_DIR = os.path.expanduser("~/.claude/sentiment-logs")


def analyze_sentiment(prompt_text: str) -> dict:
    """Call claude -p to analyze sentiment. Returns dict or None on failure."""
    analysis_prompt = (
        "Analyze the sentiment of this user prompt from a developer tool session. "
        "Return ONLY a valid JSON object with no markdown fences, no explanation — "
        "just the raw JSON object:\n"
        '{"valence": <float -1.0 to 1.0, negative to positive>, '
        '"urgency": <float 0.0 to 1.0>, '
        '"frustration": <float 0.0 to 1.0>, '
        '"confidence": <float 0.0 to 1.0>, '
        '"clarity": <float 0.0 to 1.0, how clear the request is>, '
        '"dominant_emotion": <one word: frustrated|curious|confident|urgent|neutral|excited|confused>, '
        '"intent_type": <one of: bug_fix|feature_request|question|exploration|other>}\n\n'
        f"User prompt:\n{prompt_text}"
    )

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
            timeout=25,
        )
        if result.returncode != 0:
            return None

        text = result.stdout.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        return json.loads(text)
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
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    # UserPromptSubmit provides the prompt in the "prompt" field
    prompt_text = input_data.get("prompt", "")
    cwd = input_data.get("cwd", os.getcwd())

    if not prompt_text.strip():
        sys.exit(0)

    sentiment = analyze_sentiment(prompt_text)

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{session_id}.jsonl")

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "event": "user_prompt",
        "cwd": cwd,
        "project_type": detect_project_type(cwd),
        "prompt_length": len(prompt_text),
        "prompt_preview": prompt_text[:200],
        "sentiment": sentiment,
    }

    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except IOError:
        pass  # Never block the user due to logging failure

    # If frustration is very high, inject a gentle nudge into Claude's context
    if sentiment and sentiment.get("frustration", 0) > 0.85:
        output = {
            "systemMessage": (
                "Note: The user appears to be experiencing high frustration. "
                "Consider acknowledging any difficulty, offering clearer explanations, "
                "or asking what is blocking them."
            )
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
