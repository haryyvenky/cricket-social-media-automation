# Editorial Writer Guide

Complete documentation for the automated cricket editorial content generation system.

## Overview

This system uses Claude AI to generate professional social media content for cricket match reviews. It processes scraped match data and produces:

- **LinkedIn posts** – professional, analytical, with statistics and insights
- **Twitter/X posts** – concise, punchy, emoji-enhanced, within 280 characters

---

## Files

| File | Purpose |
|------|---------|
| `match_editorial_generator.py` | Generates LinkedIn + Twitter posts for a single match |
| `editorial_writer.py` | Generates tournament-level LinkedIn summary + Twitter thread |
| `full_pipeline_example.py` | Runs the complete pipeline end-to-end |
| `scrape_espn_matches.py` | Scrapes match data from ESPNcricinfo |

---

## Prerequisites

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Anthropic API key

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

---

## Usage

### Individual Match Editorial

Generate a LinkedIn post and tweet for a single match:

```python
from match_editorial_generator import generate_match_editorial, print_editorial

match_data = {
    "title": "India vs Pakistan, Group A",
    "result": "India won by 6 wickets",
    "man_of_match": "Virat Kohli",
    "innings": [
        {
            "innings_number": 1,
            "team_score": "Pakistan: 165/7 (20 overs)",
            "batting": [
                {"name": "Babar Azam", "runs": "72", "balls": "52"},
                {"name": "Mohammad Rizwan", "runs": "45", "balls": "38"},
            ],
            "bowling": [
                {"name": "Jasprit Bumrah", "overs": "4", "runs": "22", "wickets": "3"},
            ],
        },
        {
            "innings_number": 2,
            "team_score": "India: 166/4 (18.3 overs)",
            "batting": [
                {"name": "Virat Kohli", "runs": "82", "balls": "58"},
                {"name": "Rohit Sharma", "runs": "51", "balls": "35"},
            ],
            "bowling": [
                {"name": "Shaheen Afridi", "overs": "4", "runs": "31", "wickets": "2"},
            ],
        },
    ],
}

editorial = generate_match_editorial(match_data)
print_editorial(editorial)
```

**Output structure:**

```json
{
  "match_title": "India vs Pakistan, Group A",
  "result": "India won by 6 wickets",
  "linkedin": "...150-250 word professional post...",
  "twitter": "...≤280 character tweet..."
}
```

---

### Tournament Review

Generate a comprehensive tournament review covering multiple matches:

```python
from editorial_writer import generate_tournament_review, print_tournament_review

matches = [...]  # List of match data dicts

review = generate_tournament_review(
    matches=matches,
    tournament_name="ICC Men's T20 World Cup 2025-26"
)
print_tournament_review(review)
```

**Output structure:**

```json
{
  "tournament": "ICC Men's T20 World Cup 2025-26",
  "match_count": 3,
  "linkedin": "...400-500 word tournament summary...",
  "twitter_thread": [
    "1/ Hook tweet introducing the day's action...",
    "2/ Match 1 highlights...",
    "3/ Match 2 highlights...",
    "4/ Match 3 highlights...",
    "5/ Key stats and performers...",
    "6/ Outlook and CTA..."
  ]
}
```

---

### Full Pipeline

Run the complete workflow from scraped data to publishing package:

```python
from full_pipeline_example import run_full_pipeline

# Using scraped data file
package = run_full_pipeline(
    matches_json_path="matches_20260218.json",
    tournament_name="ICC Men's T20 World Cup 2025-26"
)

# Or using built-in sample data (for testing)
package = run_full_pipeline()
```

**Output:** A `publishing_package_YYYYMMDD.json` file containing all editorials.

---

### Load from Scraped File

If you already have a scraped JSON file from `scrape_espn_matches.py`:

```python
from editorial_writer import generate_review_from_file

review = generate_review_from_file("matches_20260218.json")
```

---

## Data Format

The editorial generators accept match data in the following format (matching `scrape_espn_matches.py` output):

```json
{
  "title": "Team A vs Team B, Match Number",
  "result": "Team A won by X runs/wickets",
  "venue": "Stadium Name",
  "date": "DD Mon YYYY",
  "man_of_match": "Player Name",
  "innings": [
    {
      "innings_number": 1,
      "team_score": "Team A: 180/6 (20 overs)",
      "batting": [
        {"name": "Batsman", "runs": "65", "balls": "42"}
      ],
      "bowling": [
        {"name": "Bowler", "overs": "4", "runs": "28", "wickets": "2"}
      ]
    }
  ]
}
```

---

## Content Quality

### LinkedIn Posts

- **Individual match:** 150-250 words
- **Tournament review:** 400-500 words
- Professional analytical tone
- Statistics embedded naturally
- Turning point identification
- Forward-looking insights
- 3-6 relevant hashtags

### Twitter/X Posts

- **Individual match:** ≤280 characters (strictly enforced)
- **Tournament thread:** 5-6 tweets, each ≤280 characters
- Emojis used sparingly (1-2 per tweet)
- 2-3 hashtags maximum
- Punchy, shareable language

---

## Scraper Integration

Run the scraper first to get match data, then generate editorials:

```bash
# 1. Scrape Feb 18, 2026 matches
python scrape_espn_matches.py 2026-02-18

# 2. Generate editorials from scraped data
python full_pipeline_example.py matches_20260218.json
```

---

## GitHub Actions

The `test-editorial.yml` workflow:

- Runs daily at 2 AM Singapore Time (6 PM UTC)
- Tests all three generation scripts
- Validates output format and character limits
- Uploads generated content as artifacts
- Requires `ANTHROPIC_API_KEY` in repository Secrets

---

## Troubleshooting

**`ANTHROPIC_API_KEY not set`**
→ Export the key: `export ANTHROPIC_API_KEY=your_key`

**Twitter post > 280 chars**
→ The generator automatically truncates to 280 chars if Claude exceeds the limit.

**No innings data extracted**
→ Check that the scraper extracted `batting` and `bowling` arrays in each innings. The editorial will still run with available data.

**API rate limits**
→ Each run makes 2 API calls per match (LinkedIn + Twitter) plus 2 for the tournament review. Budget ~10 API calls for a 3-match day.
