"""
session.py — Phoneme difficulty tracking + adaptive difficulty.

Tracks which sounds the user struggles with across an entire session.
Drives adaptive phrase selection — mastered sounds get dropped,
struggling sounds get more drilling.

Stored in memory during a session. Can be persisted to JSON for cross-session memory.
"""

import json
import os
from collections import defaultdict
from phonemes import get_language_gaps, find_language, CMU_TO_IPA


class PhonemeTracker:
    """
    Tracks per-phoneme performance across a session.

    For each IPA phoneme, stores:
    - attempts: how many times it appeared in a target phrase
    - correct: how many times the user got it right (similarity >= 0.8)
    - recent: last 3 results (True/False) for streak detection
    """

    def __init__(self, language_name: str):
        self.language_name = language_name
        self.gaps = get_language_gaps(language_name)  # sounds hard for this language
        self.attempts = defaultdict(int)
        self.correct = defaultdict(int)
        self.recent = defaultdict(list)   # last N results per phoneme
        self.mastered = set()             # phonemes with 3+ correct in a row
        self.struggling = set()           # phonemes failed 2+ times in a row

    def record(self, phoneme_mismatches: list, target_phrase: str):
        """
        Update tracker from one phrase attempt.
        phoneme_mismatches: list of {ipa, similarity, is_language_gap} dicts from scorer.
        target_phrase: the phrase they were trying to say (to count all phonemes attempted).
        """
        from phonemes import get_phrase_phonemes, CMU_TO_IPA as C2I

        # All phonemes in the target phrase — count as attempted
        phrase_phonemes = get_phrase_phonemes(target_phrase)
        attempted_ipa = set()
        for cmu_list in phrase_phonemes.values():
            for cmu in cmu_list:
                base = cmu.rstrip("012")
                ipa = C2I.get(base)
                if ipa:
                    attempted_ipa.add(ipa)

        # Map mismatches by phoneme for quick lookup
        mismatch_map = {m["target_ipa"]: m["similarity"] for m in phoneme_mismatches}

        for ipa in attempted_ipa:
            self.attempts[ipa] += 1
            sim = mismatch_map.get(ipa, 1.0)  # if not in mismatches, it was correct
            got_it = sim >= 0.8

            self.recent[ipa].append(got_it)
            self.recent[ipa] = self.recent[ipa][-5:]  # keep last 5

            if got_it:
                self.correct[ipa] += 1

            # Update mastery / struggling status
            recent = self.recent[ipa]
            if len(recent) >= 3 and all(recent[-3:]):
                self.mastered.add(ipa)
                self.struggling.discard(ipa)
            elif len(recent) >= 2 and not any(recent[-2:]):
                self.struggling.add(ipa)
                self.mastered.discard(ipa)

    def accuracy(self, ipa: str) -> float:
        """Return accuracy 0–1 for a phoneme."""
        a = self.attempts[ipa]
        if a == 0:
            return None  # not yet seen
        return self.correct[ipa] / a

    def priority_gaps(self) -> list:
        """
        Return language gap phonemes sorted by priority for drilling.
        Priority: struggling > low accuracy > not yet seen > mastered (excluded)
        """
        result = []
        for ipa in self.gaps:
            if ipa in self.mastered:
                continue  # skip — they've got this
            acc = self.accuracy(ipa)
            result.append({
                "ipa": ipa,
                "accuracy": acc,
                "is_struggling": ipa in self.struggling,
                "attempts": self.attempts[ipa],
            })

        # Sort: struggling first, then low accuracy, then unseen
        result.sort(key=lambda x: (
            not x["is_struggling"],
            x["accuracy"] if x["accuracy"] is not None else 0.5,
            -x["attempts"],
        ))
        return result

    def heatmap(self) -> dict:
        """
        Return a heatmap summary for end-of-session display.
        Groups phonemes into: mastered / improving / struggling / not seen
        """
        mastered = []
        improving = []
        struggling = []
        not_seen = []

        for ipa in sorted(self.gaps):
            acc = self.accuracy(ipa)
            if ipa in self.mastered or (acc is not None and acc >= 0.8):
                mastered.append(ipa)
            elif ipa in self.struggling or (acc is not None and acc < 0.4):
                struggling.append(ipa)
            elif acc is not None:
                improving.append(ipa)
            else:
                not_seen.append(ipa)

        return {
            "mastered": mastered,
            "improving": improving,
            "struggling": struggling,
            "not_seen": not_seen,
        }

    def top_struggles(self, n: int = 3) -> list:
        """Return the n phonemes the user struggles with most."""
        ranked = [
            (ipa, self.accuracy(ipa))
            for ipa in self.gaps
            if self.attempts[ipa] > 0 and ipa not in self.mastered
        ]
        ranked.sort(key=lambda x: (x[1] if x[1] is not None else 1.0))
        return [ipa for ipa, _ in ranked[:n]]

    def practice_words_for(self, ipa: str) -> list:
        """Return 3 simple English words that contain this phoneme."""
        PRACTICE_WORDS = {
            "θ": ["think", "thank", "three"],
            "ð": ["the", "this", "that"],
            "ɹ": ["red", "run", "right"],
            "v": ["very", "voice", "visit"],
            "p": ["people", "paper", "please"],
            "æ": ["cat", "bad", "and"],
            "ɪ": ["it", "big", "this"],
            "ŋ": ["sing", "think", "ring"],
            "ʃ": ["she", "shop", "show"],
            "ʒ": ["vision", "measure", "usual"],
            "dʒ": ["job", "just", "age"],
            "w": ["water", "with", "well"],
            "ʤ": ["job", "jump", "enjoy"],
        }
        return PRACTICE_WORDS.get(ipa, [])


def print_session_heatmap(tracker: PhonemeTracker):
    """Print a visual phoneme heatmap to the terminal."""
    heatmap = tracker.heatmap()

    print("\n  ══ Phoneme Heatmap ══\n")

    if heatmap["mastered"]:
        print(f"  ✅ Mastered:   {' '.join('/' + p + '/' for p in heatmap['mastered'])}")

    if heatmap["improving"]:
        print(f"  📈 Improving:  {' '.join('/' + p + '/' for p in heatmap['improving'])}")

    if heatmap["struggling"]:
        print(f"  ⚠  Struggling: {' '.join('/' + p + '/' for p in heatmap['struggling'])}")

    if heatmap["not_seen"]:
        print(f"  ○  Not yet practiced: {' '.join('/' + p + '/' for p in heatmap['not_seen'][:8])}")

    # Top struggles with practice words
    top = tracker.top_struggles(3)
    if top:
        print(f"\n  📝 Practice tonight:")
        for ipa in top:
            words = tracker.practice_words_for(ipa)
            acc = tracker.accuracy(ipa)
            acc_str = f"{int(acc*100)}%" if acc is not None else "not seen"
            word_str = f"  →  try: {', '.join(words)}" if words else ""
            print(f"     /{ipa}/  ({acc_str} accuracy){word_str}")

    print()


def get_adaptive_focus(tracker: PhonemeTracker, num_sounds: int = 5) -> list:
    """
    Return the top N phonemes to focus on for the next phrase batch.
    Used by lessons.py to tell Claude which sounds to prioritize.
    """
    priority = tracker.priority_gaps()
    return [p["ipa"] for p in priority[:num_sounds]]