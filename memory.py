"""
memory.py — Persistent cross-session learning memory.

Stores each user's phoneme history in a local JSON file.
No login needed — identified by language name.

File: memory/{language}.json
"""

import json
import os
from datetime import datetime

MEMORY_DIR = "memory"


def _path(language: str) -> str:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    # Sanitize language name for filename
    safe = language.replace(" ", "_").replace("/", "_")
    return os.path.join(MEMORY_DIR, f"{safe}.json")


def load_memory(language: str) -> dict:
    """
    Load a learner's memory profile.
    Returns a fresh profile if none exists yet.
    """
    path = _path(language)
    if not os.path.exists(path):
        return _fresh_profile(language)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _fresh_profile(language)


def save_memory(language: str, profile: dict):
    """Save a learner's memory profile to disk."""
    profile["last_session"] = datetime.now().isoformat()
    profile["total_sessions"] = profile.get("total_sessions", 0) + 1

    try:
        with open(_path(language), "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ⚠  Could not save memory: {e}")


def _fresh_profile(language: str) -> dict:
    return {
        "language": language,
        "total_sessions": 0,
        "last_session": None,
        "phonemes": {},
        # phonemes structure:
        # {
        #   "ð": {
        #     "attempts": 12,
        #     "correct": 8,
        #     "mastered": false,
        #     "last_seen": "2026-03-14T..."
        #   }
        # }
    }


def update_memory_from_tracker(profile: dict, tracker) -> dict:
    """
    Merge a session's PhonemeTracker results into the persistent profile.
    Called at end of each session.
    """
    for ipa, attempts in tracker.attempts.items():
        if ipa not in profile["phonemes"]:
            profile["phonemes"][ipa] = {
                "attempts": 0,
                "correct": 0,
                "mastered": False,
                "last_seen": None,
            }

        entry = profile["phonemes"][ipa]
        entry["attempts"] += attempts
        entry["correct"] += tracker.correct.get(ipa, 0)
        entry["mastered"] = ipa in tracker.mastered
        entry["last_seen"] = datetime.now().isoformat()

    return profile


def get_focus_sounds_from_memory(profile: dict, n: int = 6) -> list:
    """
    From persistent memory, return which sounds to focus on this session.

    Priority:
    1. Previously struggling sounds (low accuracy, seen before)
    2. Sounds never seen before
    3. Skip mastered sounds
    """
    phonemes = profile.get("phonemes", {})

    struggling = []
    unseen_hint = []  # we don't know unseen — handled by session tracker

    for ipa, data in phonemes.items():
        if data.get("mastered"):
            continue  # skip — they've got this

        attempts = data.get("attempts", 0)
        correct = data.get("correct", 0)
        acc = correct / attempts if attempts > 0 else None

        if acc is not None and acc < 0.6:
            struggling.append((ipa, acc))

    # Sort by worst accuracy first
    struggling.sort(key=lambda x: x[1])
    return [ipa for ipa, _ in struggling[:n]]


def print_memory_summary(profile: dict):
    """Print a returning user's history at session start."""
    sessions = profile.get("total_sessions", 0)
    if sessions == 0:
        return  # first time — no history to show

    phonemes = profile.get("phonemes", {})
    mastered = [p for p, d in phonemes.items() if d.get("mastered")]
    struggling = [
        p for p, d in phonemes.items()
        if not d.get("mastered") and d.get("attempts", 0) > 0
        and (d["correct"] / d["attempts"]) < 0.6
    ]

    last = profile.get("last_session", "")
    if last:
        try:
            last = datetime.fromisoformat(last).strftime("%B %d")
        except Exception:
            last = "recently"

    print(f"\n  ── Welcome back! ──")
    print(f"  Sessions completed: {sessions}")
    print(f"  Last practice: {last}")
    if mastered:
        print(f"  ✅ Sounds you've mastered: {' '.join('/' + p + '/' for p in mastered[:6])}")
    if struggling:
        print(f"  🎯 Still working on: {' '.join('/' + p + '/' for p in struggling[:4])}")
    print()