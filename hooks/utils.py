#!/usr/bin/env python3
"""Shared utilities for prompt-sentiment-analyzer hooks."""

import os


def strip_fence(text: str) -> str:
    """Strip markdown code fences from LLM output.

    Handles plain ``` and annotated ```json / ```python etc.
    The first line (the opening fence) is always dropped; the trailing
    ``` is stripped only if present, so partial output still parses.
    """
    if not text.startswith("```"):
        return text
    lines = text.split("\n")
    body = "\n".join(lines[1:])
    if body.endswith("```"):
        body = body[:-3].rstrip()
    return body


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
