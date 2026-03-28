# Trendizzy
An AI-powered trend intelligence and content generation system. Ingests trending data from multiple sources, filters and enriches it using Claude AI, and will generate platform-specific content for personal creators and businesses.

**Pipeline:**
```
Data Source → Ingestion → Storage → Filter → AI Enrichment → (coming: Content Generation)
```

---

### Design Decisions

**Ingestion**
- Initially attempted `pytrends`, migrated to `trendspy` due to maintenance and compatibility issues
- Google Trends objects are normalised into primitive JSON-safe types at the ingestion boundary to keep raw storage simple and debuggable
- Raw JSON is saved to disk before DB insert — supports offline mode during development to avoid rate limits

**Storage (SQLite)**
- Two-table design: `trends` (concept layer) and `trend_signals` (signal layer)
- `trends` stores the keyword once with a UUID — deduplicated via `UNIQUE` constraint on `keyword`
- `trend_signals` stores one row per pipeline run — intentional history, enables future trend velocity tracking
- `get_top_trends()` always joins the latest signal per trend (by MAX id) to avoid duplicate results
- Enrichment stored as a JSON blob directly on the `trends` table — one enrichment per keyword, never re-enriched

**Filtering**
- Junk filter runs after DB query, not before saving — all raw data is preserved in the DB, only the working set is cleaned
- Rule-based for now (too short, navigational queries, generic terms) — sufficient at low scale
- Will be replaced or supplemented by AI classification as source volume grows

**AI Enrichment (Claude API)**
- Uses `claude-haiku-4-5` — fast and cost-effective for classification tasks at pipeline scale
- Enrichment is skipped for any trend already enriched in the DB — Claude is called once per keyword, ever
- Only actionable trends (post-filter) are sent for enrichment — junk never reaches the API
- Claude returns: category, summary, creator content angles, business content angles, time sensitivity
- Markdown code block stripping applied to Claude responses before JSON parsing