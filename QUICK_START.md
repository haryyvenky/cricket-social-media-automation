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

## Test 1: Individual Match Editorial

Generate a LinkedIn post and tweet for a single match using built-in sample data:

```bash
python match_editorial_generator.py
```

**Expected output:**
- A 150-250 word LinkedIn post
- A ≤280 character Twitter post
- Saved to `sample_editorial_output.json`

---

## Test 2: Tournament Review

Generate a LinkedIn tournament summary and Twitter thread:

```bash
python editorial_writer.py
```

**Expected output:**
- A 400-500 word LinkedIn tournament summary
- A 5-6 tweet Twitter thread
- Saved to `sample_tournament_review.json`

---

## Test 3: Full Pipeline

Run the complete workflow (scrape → analyze → editorial → package):

```bash
python full_pipeline_example.py
```

**Expected output:**
- Individual editorials for 3 sample matches
- Full tournament review
- Saved to `publishing_package_YYYYMMDD.json`

---

## Using Real Scraped Data

### Step 1: Scrape match data

```bash
# Scrape completed matches from Feb 18, 2026
python scrape_espn_matches.py 2026-02-18
# Output: matches_20260218.json
```

### Step 2: Generate editorials from scraped data

```bash
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
| Scraper returns empty data | ESPNcricinfo HTML may have changed; check match URL |
| Twitter post too long | Auto-truncated to 280 chars; review prompt if consistently long |
| No matches for date | Check that match URLs are configured in `scrape_espn_matches.py` |
