#!/usr/bin/env python3
"""Shared utilities for prompt-sentiment-analyzer hooks."""

import os


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
