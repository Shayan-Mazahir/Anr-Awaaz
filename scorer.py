"""
scorer.py — Real phoneme-level scoring.

Instead of word matching ("did they say this word?"),
we compare phoneme sequences using the CMU dictionary.

Example: target "the" = [DH, AH], spoken "ze" = [Z, IY]
→ DH vs Z = mismatch (the /ð/ gap), AH vs IY = mismatch
→ score reflects actual pronunciation accuracy, not word presence
"""

from phonemes import get_phrase_phonemes, CMU_TO_IPA, get_language_gaps, find_language


# ──────────────────────────────────────────
# Phoneme similarity table
# Acoustically close pairs get partial credit
# ──────────────────────────────────────────

SIMILAR_PHONEMES = {
    frozenset(["p", "b"]): 0.5,
    frozenset(["t", "d"]): 0.5,
    frozenset(["k", "g"]): 0.5,
    frozenset(["f", "v"]): 0.5,
    frozenset(["s", "z"]): 0.5,
    frozenset(["θ", "s"]): 0.4,   # th→s (very common Arabic/Spanish substitution)
    frozenset(["θ", "t"]): 0.4,   # th→t
    frozenset(["ð", "d"]): 0.4,   # th→d
    frozenset(["ð", "z"]): 0.4,   # th→z
    frozenset(["ʃ", "s"]): 0.5,   # sh→s
    frozenset(["ʒ", "z"]): 0.5,
    frozenset(["ɹ", "l"]): 0.3,   # r/l confusion
    frozenset(["ŋ", "n"]): 0.6,   # ng→n
    frozenset(["æ", "e"]): 0.5,
    frozenset(["ɪ", "iː"]): 0.6,
    frozenset(["ʊ", "uː"]): 0.6,
    frozenset(["ə", "e"]): 0.6,
    frozenset(["ɑː", "a"]): 0.6,
}


def _phoneme_similarity(p1: str, p2: str) -> float:
    if p1 == p2:
        return 1.0
    return SIMILAR_PHONEMES.get(frozenset([p1, p2]), 0.0)


def _cmu_to_ipa_list(cmu_list: list) -> list:
    result = []
    for cmu in cmu_list:
        base = cmu.rstrip("012")
        ipa = CMU_TO_IPA.get(base)
        if ipa:
            result.append(ipa)
    return result


def _align_and_score(target_ipa: list, spoken_ipa: list) -> tuple:
    """
    Linear alignment of two phoneme sequences.
    Returns (score 0–1, alignments list)
    """
    if not target_ipa:
        return 1.0, []
    if not spoken_ipa:
        return 0.0, [(p, None, 0.0) for p in target_ipa]

    alignments = []
    for i, t_p in enumerate(target_ipa):
        if i < len(spoken_ipa):
            s_p = spoken_ipa[i]
            sim = _phoneme_similarity(t_p, s_p)
            alignments.append((t_p, s_p, sim))
        else:
            alignments.append((t_p, None, 0.0))

    insertion_penalty = max(0, len(spoken_ipa) - len(target_ipa)) * 0.1
    raw = sum(a[2] for a in alignments) / len(target_ipa)
    return max(0.0, raw - insertion_penalty), alignments


def _find_closest_spoken(target_ipa: list, spoken_phonemes: dict) -> list:
    """Find best phoneme match among spoken words when exact word not found."""
    best_score = 0.0
    best_ipa = []
    for s_cmu in spoken_phonemes.values():
        s_ipa = _cmu_to_ipa_list(s_cmu)
        score, _ = _align_and_score(target_ipa, s_ipa)
        if score > best_score and score > 0.4:
            best_score = score
            best_ipa = s_ipa
    return best_ipa


def score_attempt(target_phrase: str, spoken_phrase: str, language_query: str) -> dict:
    """
    Score pronunciation at the phoneme level.

    Returns:
    {
        "score": int (0–100),          # blended final score
        "phoneme_score": int,          # pure phoneme accuracy
        "word_score": int,             # word-level accuracy
        "matched_words": [...],
        "missed_words": [...],
        "phoneme_mismatches": [
            {
                "word": str,
                "target_ipa": str,
                "spoken_ipa": str | None,
                "similarity": float,
                "is_language_gap": bool,
                "cmu": str,            # legacy compat
                "ipa": str,            # legacy compat
            }
        ],
        "top_correction": {...} | None,
        "spoken": str,
        "target": str,
    }
    """
    target_words = target_phrase.lower().split()
    spoken_words = spoken_phrase.lower().split()
    target_set = set(target_words)
    spoken_set = set(spoken_words)
    matched = target_set & spoken_set
    missed = target_set - spoken_set

    word_score = len(matched) / len(target_set) * 100 if target_set else 0

    language_name = find_language(language_query) or language_query
    gaps = get_language_gaps(language_name)

    target_phonemes = get_phrase_phonemes(target_phrase)
    spoken_phonemes = get_phrase_phonemes(spoken_phrase)

    total_ph_score = 0.0
    total_scored = 0
    phoneme_mismatches = []

    for word in target_words:
        t_cmu = target_phonemes.get(word, [])
        if not t_cmu:
            continue
        t_ipa = _cmu_to_ipa_list(t_cmu)
        if not t_ipa:
            continue

        if word in spoken_phonemes:
            s_ipa = _cmu_to_ipa_list(spoken_phonemes[word])
        else:
            s_ipa = _find_closest_spoken(t_ipa, spoken_phonemes)

        word_ph_score, alignments = _align_and_score(t_ipa, s_ipa)
        total_ph_score += word_ph_score
        total_scored += 1

        for t_p, s_p, sim in alignments:
            if sim < 0.8:
                phoneme_mismatches.append({
                    "word": word,
                    "target_ipa": t_p,
                    "spoken_ipa": s_p,
                    "similarity": sim,
                    "is_language_gap": t_p in gaps,
                    "cmu": next((k for k, v in CMU_TO_IPA.items() if v == t_p), t_p),
                    "ipa": t_p,
                })

    phoneme_score = int((total_ph_score / total_scored * 100) if total_scored else 0)

    # Weighted blend: phoneme accuracy is primary signal
    final_score = min(100, int(phoneme_score * 0.7 + word_score * 0.3))

    # Sort: language gaps first, then worst similarity first
    phoneme_mismatches.sort(key=lambda x: (not x["is_language_gap"], x["similarity"]))

    return {
        "score": final_score,
        "phoneme_score": phoneme_score,
        "word_score": int(word_score),
        "matched_words": sorted(matched),
        "missed_words": sorted(missed),
        "phoneme_mismatches": phoneme_mismatches,
        "top_correction": phoneme_mismatches[0] if phoneme_mismatches else None,
        "spoken": spoken_phrase,
        "target": target_phrase,
    }


def score_to_stars(score: int) -> str:
    if score >= 90: return "★★★★★"
    elif score >= 75: return "★★★★☆"
    elif score >= 60: return "★★★☆☆"
    elif score >= 40: return "★★☆☆☆"
    else: return "★☆☆☆☆"