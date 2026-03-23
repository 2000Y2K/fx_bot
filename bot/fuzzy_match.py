"""
Fuzzy asset matching using Levenshtein distance.
Finds the best matching asset name from a search term, with configurable confidence thresholds.
"""

import re


def levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    # Use two-row DP to save memory
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            curr[j] = min(
                prev[j] + 1,        # deletion
                curr[j - 1] + 1,    # insertion
                prev[j - 1] + (0 if ca == cb else 1),  # substitution
            )
        prev = curr
    return prev[-1]


def similarity(a: str, b: str) -> float:
    """
    Normalized similarity score between 0 and 1.
    1.0 = identical, 0.0 = completely different.
    """
    dist = levenshtein(a, b)
    max_len = max(len(a), len(b), 1)
    return 1.0 - dist / max_len


def tokenize(text: str) -> list[str]:
    """Split on non-alphanumeric chars, remove empty tokens."""
    return [t for t in re.split(r'[\s\-_./\\]+', text.lower()) if t]


def score_asset(query: str, asset_name: str) -> float:
    """
    Multi-strategy scoring — returns best score across strategies:
    1. Exact substring match (highest confidence)
    2. All query tokens found in asset name tokens
    3. Best single-token Levenshtein similarity
    4. Full string similarity
    """
    q = query.lower().strip()
    name = asset_name.lower().strip()

    # Strategy 1: exact substring
    if q in name:
        return 1.0

    q_tokens    = tokenize(q)
    name_tokens = tokenize(name)

    if not q_tokens:
        return 0.0

    # Strategy 2: all query tokens present in asset tokens (substring per token)
    token_hits = sum(
        1 for qt in q_tokens
        if any(qt in nt or nt in qt for nt in name_tokens)
    )
    token_score = token_hits / len(q_tokens)
    if token_score == 1.0:
        return 0.95  # all tokens matched

    # Strategy 3: best per-token Levenshtein match
    token_similarities = [
        max(similarity(qt, nt) for nt in name_tokens)
        for qt in q_tokens
    ]
    avg_token_sim = sum(token_similarities) / len(token_similarities)

    # Strategy 4: full string similarity
    full_sim = similarity(q, name)

    return max(token_score * 0.9, avg_token_sim * 0.85, full_sim)


# ─── Confidence thresholds ────────────────────────────────────────────────
# Tune these if results are too aggressive or too conservative
HIGH_CONFIDENCE   = 0.75   # show directly as best match
MEDIUM_CONFIDENCE = 0.45   # show as suggestion, ask for confirmation
MIN_CONFIDENCE    = 0.25   # below this, ignore completely


def find_best_assets(query: str, assets: list[dict], top_n: int = 3) -> list[dict]:
    """
    Score all assets against query and return top matches above MIN_CONFIDENCE.
    Each result gets a 'score' and 'confidence' field added.
    """
    if not query or not assets:
        return []

    scored = []
    for asset in assets:
        sc = score_asset(query, asset["name"])
        if sc >= MIN_CONFIDENCE:
            scored.append({**asset, "_score": sc})

    scored.sort(key=lambda a: a["_score"], reverse=True)
    return scored[:top_n]


def classify_match(assets_scored: list[dict]) -> tuple[str, list[dict]]:
    """
    Given scored assets, return (confidence_level, assets).
    confidence_level: "high" | "medium" | "none"
    """
    if not assets_scored:
        return "none", []

    best = assets_scored[0]["_score"]

    if best >= HIGH_CONFIDENCE:
        # High confidence: return just the top result
        return "high", [assets_scored[0]]

    if best >= MEDIUM_CONFIDENCE:
        # Medium: return top matches for user to choose
        return "medium", assets_scored

    return "none", []
