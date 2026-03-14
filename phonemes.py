import pandas as pd
from nltk.corpus import cmudict
from functools import lru_cache

# Load data once
print("Loading PHOIBLE dataset...")
PHOIBLE = pd.read_csv('phoible.csv', low_memory=False)
CMU = cmudict.dict()

# English phoneme inventory from PHOIBLE
ENGLISH_PHONEMES = set(PHOIBLE[PHOIBLE['LanguageName'] == 'English']['Phoneme'].unique())


@lru_cache(maxsize=50)
def get_language_gaps(language_name: str):
    """Automatically compute which English phonemes are missing from a language/dialect"""
    lang_data = PHOIBLE[PHOIBLE['LanguageName'] == language_name]
    if lang_data.empty:
        return set()
    lang_phonemes = set(lang_data['Phoneme'].unique())
    return ENGLISH_PHONEMES - lang_phonemes


@lru_cache(maxsize=50)
def find_language(query: str):
    """Find closest language name in PHOIBLE"""
    query_lower = query.lower()
    matches = PHOIBLE[PHOIBLE['LanguageName'].str.lower().str.contains(query_lower, na=False)]
    if matches.empty:
        return None
    return matches['LanguageName'].iloc[0]


def get_dialects(language_query: str) -> list[str]:
    """
    Return all PHOIBLE dialect variants for a language.
    Filters out ALL-CAPS duplicates (those are just alternate dataset entries).
    Returns clean list, or empty list if only one variant exists.
    """
    query_lower = language_query.lower()
    matches = PHOIBLE[
        PHOIBLE['LanguageName'].str.lower().str.contains(query_lower, na=False)
    ]['LanguageName'].unique().tolist()

    # Filter out ALL-CAPS versions (e.g. 'ARABIC') — they're duplicates
    clean = [m for m in matches if not m.isupper()]

    # Only return dialects if there's more than one meaningful variant
    return sorted(clean) if len(clean) > 1 else []


def get_cmu_phonemes(word: str):
    """Get CMU phonemes for a word"""
    result = CMU.get(word.lower())
    return result[0] if result else []


def get_phrase_phonemes(phrase: str):
    """Get CMU phonemes for every word in phrase"""
    result = {}
    for word in phrase.lower().split():
        phonemes = get_cmu_phonemes(word)
        if phonemes:
            result[word] = phonemes
    return result


# CMU to IPA rough mapping for gap comparison
CMU_TO_IPA = {
    "P": "p", "B": "b", "T": "t", "D": "d",
    "K": "k", "G": "ɡ", "F": "f", "V": "v",
    "TH": "θ", "DH": "ð", "S": "s", "Z": "z",
    "SH": "ʃ", "ZH": "ʒ", "HH": "h", "M": "m",
    "N": "n", "NG": "ŋ", "L": "l", "R": "ɹ",
    "W": "w", "Y": "j", "CH": "t̠ʃ", "JH": "d̠ʒ",
    "IY": "iː", "IH": "ɪ", "EH": "e", "AE": "æ",
    "AA": "ɑː", "AO": "ɔ", "AH": "ə", "OW": "əʊ",
    "UH": "ʊ", "UW": "uː", "ER": "əː", "AY": "aɪ",
    "AW": "aʊ", "OY": "ɔɪ", "EY": "eɪ",
}


def find_problems_in_phrase(phrase: str, language_query: str):
    """Find which words in phrase contain sounds the speaker will struggle with"""
    language_name = find_language(language_query)
    if not language_name:
        return [], None

    gaps = get_language_gaps(language_name)
    phrase_phonemes = get_phrase_phonemes(phrase)

    problems = []
    for word, cmu_phonemes in phrase_phonemes.items():
        for cmu in cmu_phonemes:
            cmu_base = cmu.rstrip("012")
            ipa = CMU_TO_IPA.get(cmu_base)
            if ipa and ipa in gaps:
                problems.append({
                    "word": word,
                    "cmu": cmu_base,
                    "ipa": ipa,
                })

    return problems, language_name


def list_available_languages():
    """List all languages in PHOIBLE"""
    return sorted(PHOIBLE['LanguageName'].unique().tolist())