from loguru import logger

# Keywords that are navigational or too generic to generate content from.
# These are things people search to get somewhere, not topics worth covering.
BLOCKLIST = {
    "login", "sign in", "near me", "weather", "forecast", "news", "today",
    "tonight", "tomorrow", "map", "maps", "directions", "how to", "what is",
    "who is", "google", "facebook", "youtube", "twitter", "instagram", "tiktok",
    "bbc", "nhs", "gov", "amazon", "ebay"
}


def is_too_short(keyword, min_length=3):
    """Drop keywords that are too short to mean anything useful.

    'ps' or 'uk' alone give us nothing to work with content-wise.
    Note: 'ps5' is 3 characters and passes — short but specific.
    """
    return len(keyword.strip()) < min_length


def is_navigational(keyword):
    """Drop keywords that are clearly just people trying to get somewhere.

    We check if any word in the blocklist appears inside the keyword.
    For example 'bbc weather london' contains 'weather' → blocked.
    """
    keyword_lower = keyword.lower()
    return any(blocked in keyword_lower for blocked in BLOCKLIST)


def filter_trends(trends):
    """Run all filters on a list of trend dicts. Return only actionable ones.

    Each trend dict is expected to have at least a 'keyword' key.
    Logs how many were dropped and why.
    """
    actionable = []
    dropped = []

    for trend in trends:
        keyword = trend.get("keyword", "")

        if is_too_short(keyword):
            dropped.append((keyword, "too short"))
        elif is_navigational(keyword):
            dropped.append((keyword, "navigational/generic"))
        else:
            actionable.append(trend)

    # Log a summary so we can see what got dropped and why
    logger.info(f"Filter results: {len(actionable)} actionable, {len(dropped)} dropped")
    for keyword, reason in dropped:
        logger.debug(f"  Dropped '{keyword}' — {reason}")

    return actionable
