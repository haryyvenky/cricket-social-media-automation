# Quick Start Guide

Get up and running with the Cricket Editorial Generator in 5 minutes.

## Setup

### 1. Clone and install

```bash
git clone https://github.com/haryyvenky/cricket-social-media-automation
cd cricket-social-media-automation
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

---

## How to Test

### Offline tests — no API key needed (always run these first)

```bash
python test_editorial_system.py
```

This runs 12 unit tests that verify the data-extraction helpers, context builders, and pipeline logic **without making any API calls**. All tests should show `✅ PASS`.

Expected output:
```
============================================================
  🏏 Cricket Editorial System — Test Suite
  Mode: Offline tests only
============================================================
  ✅ PASS  extract_key_batting returns top 3 by runs
  ✅ PASS  extract_key_batting computes strike rate correctly
  ...
  Results: 12 passed, 0 failed, 7 skipped
```

### AI generation tests — requires `ANTHROPIC_API_KEY`

```bash
export ANTHROPIC_API_KEY=your_key_here
python test_editorial_system.py --all
```

This runs all 19 tests including 7 tests that call Claude AI to generate real LinkedIn posts and tweets. Each AI test checks that:
- LinkedIn word counts are within spec (150-350 words for a match, 200-600 for a tournament)
- Twitter posts are ≤280 characters
- All required output keys are present

---

## Run Individual Scripts (Manual Testing)

### Test 1: Single match editorial

Generate a LinkedIn post and tweet for one match (uses built-in sample data):

```bash
python match_editorial_generator.py
# Saves: sample_editorial_output.json
```

### Test 2: Tournament review

Generate a LinkedIn tournament summary and Twitter thread:

```bash
python editorial_writer.py
# Saves: sample_tournament_review.json
```

### Test 3: Full pipeline

Run the complete scrape → analyze → editorial → package workflow:

```bash
python full_pipeline_example.py
# Saves: publishing_package_YYYYMMDD.json
```

### Test 4: Scraper only (no API key needed)

Fetch the 3 completed T20 WC matches from Feb 18, 2026:

```bash
python scrape_espn_matches.py 2026-02-18
# Saves: matches_20260218.json
```

---

## End-to-end: From scrape to editorial

```bash
# Step 1: Scrape match data
python scrape_espn_matches.py 2026-02-18

# Step 2: Generate editorial content from scraped data
python full_pipeline_example.py matches_20260218.json
```

---

## GitHub Actions (Automated Daily Run)

Add your API key as a repository secret:

1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: your Anthropic API key

The `test-editorial.yml` workflow runs automatically at 2 AM Singapore Time.

To run manually:
- Go to **Actions → Test Editorial Generation → Run workflow**

---

## Output Files

| File | Contents |
|------|---------|
| `sample_editorial_output.json` | Single match LinkedIn + Twitter |
| `sample_tournament_review.json` | Tournament LinkedIn + Twitter thread |
| `publishing_package_YYYYMMDD.json` | Complete day's content package |
| `matches_YYYYMMDD.json` | Raw scraped match data |

---

## What Each Script Does

```
test_editorial_system.py        → Unit + integration tests (run this to verify everything works)
scrape_espn_matches.py          → Fetches match data from ESPNcricinfo
match_editorial_generator.py   → LinkedIn + Twitter for one match
editorial_writer.py             → LinkedIn + Twitter thread for a tournament day
full_pipeline_example.py        → Combines all of the above
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ANTHROPIC_API_KEY not set` | `export ANTHROPIC_API_KEY=your_key` |
| Offline tests failing | Check you ran `pip install -r requirements.txt` |
| Scraper returns empty data | ESPNcricinfo HTML may have changed; check match URL |
| Twitter post too long | Auto-truncated to 280 chars; review prompt if consistently long |
| No matches for date | Check that match URLs are configured in `scrape_espn_matches.py` |
