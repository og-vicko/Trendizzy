from loguru import logger

# How urgent/valuable each time_sensitivity value is for content generation.
# breaking = act now, days = still fresh, weeks = some runway, evergreen = not time-critical
TIME_WEIGHTS = {
    "breaking":  1.0,
    "days":      0.8,
    "weeks":     0.5,
    "evergreen": 0.3,
}

# How content-friendly each category is.
# High = lots of engagement potential, easy angles.
# Low = sensitive, niche, or hard to build content around.
CATEGORY_WEIGHTS = {
    "entertainment": 1.0,
    "viral":         1.0,
    "celebrity":     1.0,
    "sports_event":  0.9,
    "lifestyle":     0.8,
    "tech":          0.7,
    "business":      0.6,
    "other":         0.6,
    "news":          0.4,
    "politics":      0.3,
}


def score_trend(trend):
    """Calculate an actionability score for a single enriched trend.

    The score combines three signals:
    - trend_score    : how strongly this keyword is trending (0.0–1.0)
    - time_weight    : how urgent/fresh the trend is based on Claude's time_sensitivity
    - category_weight: how content-friendly the topic category is

    Final formula: trend_score * time_weight * category_weight
    Result is always between 0.0 and 1.0.

    If a trend hasn't been enriched, it scores 0.0 (we can't evaluate it properly).
    """
    enrichment = trend.get("enrichment")

    if not enrichment:
        logger.debug(f"  '{trend['keyword']}' has no enrichment — scoring 0.0")
        return 0.0

    trend_score = trend.get("score", 0.0)

    # Look up the weights from our tables, fall back to a neutral value if unknown
    time_weight     = TIME_WEIGHTS.get(enrichment.get("time_sensitivity", ""), 0.5)
    category_weight = CATEGORY_WEIGHTS.get(enrichment.get("category", ""), 0.5)

    return round(trend_score * time_weight * category_weight, 4)


def select_actionable_trends(trends, min_score=0.05, limit=10):
    """Rank enriched trends by actionability and return the best ones.

    Steps:
    1. Score every trend using score_trend()
    2. Drop any that fall below min_score (not worth acting on)
    3. Sort by score descending (best first)
    4. Return up to `limit` trends, each with an 'actionability_score' field added

    Args:
        trends     : list of enriched trend dicts (output of enrich_trends)
        min_score  : minimum actionability score to be included (default 0.05)
        limit      : max number of trends to return (default 10)

    Returns:
        list of trend dicts sorted by actionability_score descending
    """
    scored = []

    for trend in trends:
        action_score = score_trend(trend)
        scored.append({**trend, "actionability_score": action_score})

    # Drop anything below the threshold
    above_threshold = [t for t in scored if t["actionability_score"] >= min_score]
    below_threshold = [t for t in scored if t["actionability_score"] < min_score]

    if below_threshold:
        logger.debug(f"  Dropped {len(below_threshold)} trend(s) below min_score={min_score}:")
        for t in below_threshold:
            logger.debug(f"    '{t['keyword']}' — score {t['actionability_score']}")

    # Sort best first
    ranked = sorted(above_threshold, key=lambda t: t["actionability_score"], reverse=True)

    # Apply limit
    selected = ranked[:limit]

    logger.info(
        f"Selection: {len(selected)} actionable from {len(trends)} enriched "
        f"({len(below_threshold)} dropped below threshold)"
    )

    return selected
