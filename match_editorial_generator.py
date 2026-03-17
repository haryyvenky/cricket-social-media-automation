#!/usr/bin/env python3
"""
match_editorial_generator.py

Generates professional LinkedIn posts and catchy Twitter posts
for individual cricket match reviews using Claude AI.
"""

import anthropic
import json
import os
import re
from typing import Optional


# ============================================================
# CLAUDE AI CLIENT
# ============================================================

def get_claude_client() -> anthropic.Anthropic:
    """Create and return an Anthropic client using the API key from environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
    return anthropic.Anthropic(api_key=api_key)


# ============================================================
# DATA EXTRACTION HELPERS
# ============================================================

def extract_key_batting(innings_list: list, top_n: int = 3) -> list:
    """
    Extract top batsmen across all innings sorted by runs scored.

    Args:
        innings_list: List of innings dicts from scraped match data.
        top_n: Number of top batsmen to return.

    Returns:
        List of dicts with name, runs, balls, team_score context.
    """
    all_batsmen = []
    for innings in innings_list:
        team_label = innings.get("team_score", f"Innings {innings.get('innings_number', '')}")
        for b in innings.get("batting", []):
            try:
                runs = int(b.get("runs", 0))
                balls = int(b.get("balls", 1))
                sr = round((runs / balls) * 100, 1) if balls > 0 else 0.0
                all_batsmen.append({
                    "name": b.get("name", "Unknown"),
                    "runs": runs,
                    "balls": balls,
                    "strike_rate": sr,
                    "team": team_label,
                })
            except (ValueError, TypeError):
                continue

    # Sort by runs descending
    all_batsmen.sort(key=lambda x: x["runs"], reverse=True)
    return all_batsmen[:top_n]


def extract_key_bowling(innings_list: list, top_n: int = 2) -> list:
    """
    Extract top bowlers across all innings sorted by wickets then economy.

    Args:
        innings_list: List of innings dicts from scraped match data.
        top_n: Number of top bowlers to return.

    Returns:
        List of dicts with name, overs, runs, wickets, economy.
    """
    all_bowlers = []
    for innings in innings_list:
        for b in innings.get("bowling", []):
            try:
                wickets = int(b.get("wickets", 0))
                runs = int(b.get("runs", 0))
                overs_raw = b.get("overs", "0")
                # overs can be "4.0" or 4 or "4"
                overs = float(overs_raw)
                economy = round(runs / overs, 2) if overs > 0 else 0.0
                all_bowlers.append({
                    "name": b.get("name", "Unknown"),
                    "overs": overs_raw,
                    "runs": runs,
                    "wickets": wickets,
                    "economy": economy,
                })
            except (ValueError, TypeError):
                continue

    # Sort by wickets desc, then economy asc
    all_bowlers.sort(key=lambda x: (-x["wickets"], x["economy"]))
    return all_bowlers[:top_n]


def build_match_context(match_data: dict) -> str:
    """
    Build a structured text context string from match data for the AI prompt.

    Args:
        match_data: Dict produced by scrape_espn_matches.py scrape_match_scorecard().

    Returns:
        A formatted string summarising the match for the AI.
    """
    lines = []

    title = match_data.get("title", "Cricket Match")
    result = match_data.get("result", "Result not available")
    venue = match_data.get("venue", "")
    date = match_data.get("date", "")
    mom = match_data.get("man_of_match", "")

    lines.append(f"Match: {title}")
    if date:
        lines.append(f"Date: {date}")
    if venue:
        lines.append(f"Venue: {venue}")
    lines.append(f"Result: {result}")

    innings_list = match_data.get("innings", [])
    for innings in innings_list:
        score = innings.get("team_score", "")
        if score:
            lines.append(f"Score - {score}")

    batting = extract_key_batting(innings_list, top_n=3)
    if batting:
        lines.append("\nKey Batting Performances:")
        for b in batting:
            lines.append(
                f"  {b['name']}: {b['runs']} runs off {b['balls']} balls (SR: {b['strike_rate']})"
            )

    bowling = extract_key_bowling(innings_list, top_n=2)
    if bowling:
        lines.append("\nKey Bowling Performances:")
        for b in bowling:
            lines.append(
                f"  {b['name']}: {b['wickets']}/{b['runs']} in {b['overs']} overs"
            )

    if mom:
        lines.append(f"\nMan of the Match: {mom}")

    return "\n".join(lines)


# ============================================================
# EDITORIAL GENERATION
# ============================================================

def generate_linkedin_post(match_data: dict, client: anthropic.Anthropic) -> str:
    """
    Generate a professional LinkedIn post (150-250 words) for a cricket match.

    Args:
        match_data: Dict from scrape_espn_matches.py.
        client: Anthropic API client.

    Returns:
        LinkedIn post text.
    """
    context = build_match_context(match_data)

    prompt = f"""You are a professional cricket analyst writing for LinkedIn.

Here is the match data:

{context}

Write a professional LinkedIn post (150-250 words) that:
- Opens with an engaging hook about the match result
- Highlights the key batting and bowling performances with statistics
- Identifies ONE major turning point that changed the game
- Mentions the Man of the Match and why they deserved it
- Ends with a forward-looking insight about what this result means for the tournament
- Uses proper paragraph breaks for readability
- Includes 3-5 relevant cricket/tournament hashtags at the end
- Tone: professional, analytical, insightful

Write ONLY the post content. Do not include any preamble or explanation."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_twitter_post(match_data: dict, client: anthropic.Anthropic) -> str:
    """
    Generate a catchy Twitter/X post (≤280 characters) for a cricket match.

    Args:
        match_data: Dict from scrape_espn_matches.py.
        client: Anthropic API client.

    Returns:
        Twitter post text (≤280 chars).
    """
    context = build_match_context(match_data)

    prompt = f"""You are a cricket social media expert writing for Twitter/X.

Here is the match data:

{context}

Write ONE tweet (strictly ≤280 characters total including spaces) that:
- Captures the drama and result of the match
- Includes the key performer or Man of the Match
- Uses 1-2 emojis for engagement
- Includes 2-3 relevant hashtags (counted in the character limit)
- Is punchy, exciting, and shareable

Write ONLY the tweet text. No preamble or explanation. Must be ≤280 characters."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    tweet = message.content[0].text.strip()

    # Enforce character limit — truncate cleanly if needed
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."

    return tweet


def generate_match_editorial(match_data: dict) -> dict:
    """
    Generate both LinkedIn and Twitter posts for a single match.

    Args:
        match_data: Dict produced by scrape_espn_matches.py scrape_match_scorecard().

    Returns:
        Dict with keys 'linkedin', 'twitter', 'match_title', 'result'.
    """
    client = get_claude_client()

    title = match_data.get("title", "Cricket Match")
    result = match_data.get("result", "")

    print(f"\n📝 Generating editorial for: {title}")
    print(f"   Result: {result}")

    linkedin_post = generate_linkedin_post(match_data, client)
    print("   ✅ LinkedIn post generated")

    twitter_post = generate_twitter_post(match_data, client)
    print(f"   ✅ Twitter post generated ({len(twitter_post)} chars)")

    return {
        "match_title": title,
        "result": result,
        "linkedin": linkedin_post,
        "twitter": twitter_post,
    }


# ============================================================
# PUBLISHING PACKAGE
# ============================================================

def create_publishing_package(matches_json_path: str) -> list:
    """
    Load scraped match data and generate editorial content for all matches.

    Args:
        matches_json_path: Path to JSON file produced by scrape_espn_matches.py.

    Returns:
        List of editorial dicts, one per match.
    """
    with open(matches_json_path, "r") as f:
        data = json.load(f)

    matches = data.get("matches", [])
    if not matches:
        print("⚠️  No matches found in the JSON file.")
        return []

    print(f"📦 Creating publishing package for {len(matches)} match(es)...")

    package = []
    for match in matches:
        editorial = generate_match_editorial(match)
        package.append(editorial)

    return package


def print_editorial(editorial: dict) -> None:
    """Pretty-print an editorial dict."""
    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  {editorial['match_title']}")
    print(f"  Result: {editorial['result']}")
    print(sep)

    print("\n📱 LINKEDIN POST")
    print("-" * 40)
    print(editorial["linkedin"])

    print(f"\n🐦 TWITTER POST  ({len(editorial['twitter'])} chars)")
    print("-" * 40)
    print(editorial["twitter"])
    print(sep)


# ============================================================
# TEST HELPERS
# ============================================================

def get_sample_match_data() -> dict:
    """Return sample match data for testing without needing a live scrape."""
    return {
        "url": "https://www.espncricinfo.com/sample",
        "scraped_at": "2026-02-18 22:00:00",
        "title": "India vs Netherlands, 36th Match, Group A, ICC Men's T20 World Cup 2025-26",
        "result": "India won by 9 wickets",
        "venue": "Nassau County International Cricket Stadium, New York",
        "date": "18 Feb 2026",
        "man_of_match": "Rohit Sharma",
        "innings": [
            {
                "innings_number": 1,
                "team_score": "Netherlands: 130/8 (20 overs)",
                "batting": [
                    {"name": "Max O'Dowd", "runs": "42", "balls": "35"},
                    {"name": "Vikramjit Singh", "runs": "28", "balls": "22"},
                    {"name": "Scott Edwards", "runs": "21", "balls": "18"},
                ],
                "bowling": [
                    {"name": "Jasprit Bumrah", "overs": "4", "runs": "18", "wickets": "3"},
                    {"name": "Arshdeep Singh", "overs": "4", "runs": "27", "wickets": "2"},
                ],
            },
            {
                "innings_number": 2,
                "team_score": "India: 131/1 (14.2 overs)",
                "batting": [
                    {"name": "Rohit Sharma", "runs": "68", "balls": "40"},
                    {"name": "Virat Kohli", "runs": "45", "balls": "32"},
                    {"name": "Shubman Gill", "runs": "18", "balls": "15"},
                ],
                "bowling": [
                    {"name": "Bas de Leede", "overs": "3", "runs": "28", "wickets": "1"},
                    {"name": "Aryan Dutt", "overs": "3", "runs": "35", "wickets": "0"},
                ],
            },
        ],
    }


# ============================================================
# MAIN
# ============================================================

def main():
    """Run a test editorial generation with sample data."""
    print("=" * 70)
    print("🏏 Match Editorial Generator - Test Run")
    print("=" * 70)

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set. Please export it before running.")
        return

    # Use sample data for demonstration
    sample_match = get_sample_match_data()
    editorial = generate_match_editorial(sample_match)
    print_editorial(editorial)

    # Save to JSON
    output_file = "sample_editorial_output.json"
    with open(output_file, "w") as f:
        json.dump(editorial, f, indent=2)
    print(f"\n💾 Editorial saved to: {output_file}")


if __name__ == "__main__":
    main()
