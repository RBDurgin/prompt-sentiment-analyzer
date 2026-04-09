#!/usr/bin/env python3
"""
SessionEnd hook for prompt-sentiment-analyzer plugin.
Reads all user_prompt records from the session JSONL file and appends a summary.
Non-blocking: always exits 0.
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone


LOG_DIR = os.path.expanduser("~/.claude/sentiment-logs")


def compute_trajectory(values: list[float]) -> str:
    """Compare first half vs second half to determine trend direction.

    Requires at least 4 data points to split into two meaningful halves;
    shorter sessions are reported as stable rather than guessing from
    insufficient data. A 0.15 delta threshold avoids calling noise a trend.
    """
    if len(values) < 4:
        return "stable"
    mid = len(values) // 2
    first_half_avg = sum(values[:mid]) / mid
    second_half_avg = sum(values[mid:]) / (len(values) - mid)
    diff = second_half_avg - first_half_avg
    if diff > 0.15:
        return "increasing"
    if diff < -0.15:
        return "decreasing"
    return "stable"


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    log_path = os.path.join(LOG_DIR, f"{session_id}.jsonl")

    if not os.path.exists(log_path):
        sys.exit(0)

    prompt_records = []
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("event") == "user_prompt" and record.get("sentiment"):
                        prompt_records.append(record)
                except json.JSONDecodeError:
                    pass
    except IOError:
        sys.exit(0)

    if not prompt_records:
        sys.exit(0)

    sentiments = [r["sentiment"] for r in prompt_records]

    def avg_field(field: str) -> float:
        values = [s[field] for s in sentiments if isinstance(s.get(field), (int, float))]
        return round(sum(values) / len(values), 3) if values else 0.0

    frustration_values = [s.get("frustration", 0) for s in sentiments]
    high_frustration_count = sum(1 for v in frustration_values if v > 0.6)

    dominant_emotions = Counter(
        s["dominant_emotion"] for s in sentiments if s.get("dominant_emotion")
    )
    intent_type_counts = dict(
        Counter(s["intent_type"] for s in sentiments if s.get("intent_type"))
    )

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "event": "session_summary",
        "total_prompts": len(prompt_records),
        "avg_valence": avg_field("valence"),
        "avg_frustration": avg_field("frustration"),
        "avg_urgency": avg_field("urgency"),
        "avg_confidence": avg_field("confidence"),
        "avg_clarity": avg_field("clarity"),
        "frustration_trajectory": compute_trajectory(frustration_values),
        "dominant_emotion": dominant_emotions.most_common(1)[0][0] if dominant_emotions else "neutral",
        "intent_type_counts": intent_type_counts,
        "high_frustration_prompts": high_frustration_count,
    }

    try:
        with open(log_path, "a", opener=lambda p, f: os.open(p, f, 0o600)) as f:
            f.write(json.dumps(summary) + "\n")
    except IOError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
