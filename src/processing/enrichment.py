import json
import os
import anthropic
from dotenv import load_dotenv
from loguru import logger

# Load ANTHROPIC_API_KEY from the .env file
load_dotenv()

# Initialise the Claude client once — reused for all calls in this session
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def enrich_trend(trend):
    """Send a single trend keyword to Claude and get back structured meaning.

    Claude returns a JSON object with:
    - category        : what type of topic this is (sports_event, news, entertainment, etc.)
    - summary         : why this is likely trending right now
    - creator_angles  : 3 content ideas for personal creators (TikTok, Instagram, YouTube)
    - business_angles : 3 content ideas for brands wanting to ride this trend
    - time_sensitivity: how long this will stay relevant (breaking, days, weeks, evergreen)

    Returns the original trend dict with 'enrichment' added, or None on failure.
    """
    keyword = trend["keyword"]

    prompt = f"""You are a trend analyst for a social media content generation platform.

A user has flagged this trending search term: "{keyword}"

Analyse this trend and return ONLY a JSON object — no explanation, no markdown, no extra text:
{{
  "category": "<one of: sports_event, entertainment, news, politics, tech, lifestyle, viral, celebrity, business, other>",
  "summary": "<1-2 sentences explaining why this is likely trending>",
  "creator_angles": [
    "<content idea for a personal social media creator>",
    "<content idea 2>",
    "<content idea 3>"
  ],
  "business_angles": [
    "<content idea for a brand or business riding this trend>",
    "<content idea 2>",
    "<content idea 3>"
  ],
  "time_sensitivity": "<one of: breaking, days, weeks, evergreen>"
}}

Definitions:
- creator_angles   : ideas for individuals posting for engagement on TikTok, Instagram, YouTube, etc.
- business_angles  : ideas for companies promoting a product or service alongside this trend
- time_sensitivity : breaking = hours, days = a few days, weeks = a few weeks, evergreen = stays relevant long-term"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        raw_text = response.content[0].text.strip()

        # Claude sometimes wraps JSON in a markdown code block like ```json ... ```
        # Strip those markers if present so json.loads() can parse it cleanly
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]          # remove opening ```json
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]                  # strip the word "json"
            raw_text = raw_text.strip()

        enrichment = json.loads(raw_text)

        logger.info(f"Enriched '{keyword}' → {enrichment.get('category')} | {enrichment.get('time_sensitivity')}")
        return {**trend, "enrichment": enrichment}

    except json.JSONDecodeError:
        logger.warning(f"Claude returned invalid JSON for '{keyword}' — skipping")
        logger.debug(f"Raw response was: {raw_text}")  # temporary — lets us see what Claude actually sent
        return None
    except Exception as e:
        logger.error(f"Enrichment API call failed for '{keyword}': {e}")
        return None


def enrich_trends(trends):
    """Enrich only trends that have not been enriched before.

    How we know a trend needs enriching:
    - Its 'enrichment' field is None (meaning the DB has no enrichment stored for it yet)

    Trends that already have enrichment are passed through untouched — no API call made.
    This keeps costs low: Claude is only called once per keyword, ever.
    """
    to_enrich = [t for t in trends if t.get("enrichment") is None]
    already_done = [t for t in trends if t.get("enrichment") is not None]

    if already_done:
        logger.info(f"{len(already_done)} trend(s) already enriched — skipping API call")

    if not to_enrich:
        logger.info("Nothing new to enrich")
        return trends  # return all trends (already enriched ones included)

    logger.info(f"Enriching {len(to_enrich)} new trend(s) via Claude...")

    newly_enriched = []
    for trend in to_enrich:
        result = enrich_trend(trend)
        if result:
            newly_enriched.append(result)

    logger.success(f"Enriched {len(newly_enriched)}/{len(to_enrich)} new trends successfully")

    # Return all trends: already-enriched ones + newly enriched ones
    return already_done + newly_enriched
