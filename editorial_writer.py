#!/usr/bin/env python3
"""
editorial_writer.py

Generates comprehensive tournament summaries and Twitter threads
for T20 World Cup reviews using Claude AI.

- LinkedIn tournament summary: 400-500 words
- Twitter thread: 5-6 tweets covering the tournament
"""

import anthropic
import json
import os
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
# DATA HELPERS
# ============================================================

def summarise_matches_for_prompt(matches: list) -> str:
    """
    Build a condensed text summary of all matches for use in a prompt.

    Args:
        matches: List of match dicts (from scraped JSON or parsed data).

    Returns:
        Formatted string summarising each match.
    """
    lines = []
    for i, match in enumerate(matches, 1):
        title = match.get("title", f"Match {i}")
        result = match.get("result", "N/A")
        mom = match.get("man_of_match", "")
        date = match.get("date", "")

        lines.append(f"Match {i}: {title}")
        if date:
            lines.append(f"  Date: {date}")
        lines.append(f"  Result: {result}")
        if mom:
            lines.append(f"  Man of the Match: {mom}")

        # Include team scores
        for innings in match.get("innings", []):
            score = innings.get("team_score", "")
            if score:
                lines.append(f"  Score: {score}")

        # Top batsman
        all_batting = []
        for innings in match.get("innings", []):
            for b in innings.get("batting", []):
                try:
                    all_batting.append((b["name"], int(b.get("runs", 0)), b.get("balls", "?")))
                except (ValueError, TypeError):
                    continue
        if all_batting:
            all_batting.sort(key=lambda x: x[1], reverse=True)
            top = all_batting[0]
            lines.append(f"  Top bat: {top[0]} ({top[1]} runs off {top[2]} balls)")

        # Top bowler
        all_bowling = []
        for innings in match.get("innings", []):
            for b in innings.get("bowling", []):
                try:
                    all_bowling.append((b["name"], int(b.get("wickets", 0)), b.get("runs", "?")))
                except (ValueError, TypeError):
                    continue
        if all_bowling:
            all_bowling.sort(key=lambda x: x[1], reverse=True)
            top = all_bowling[0]
            lines.append(f"  Top bowl: {top[0]} ({top[1]} wkts/{top[2]} runs)")

        lines.append("")

    return "\n".join(lines)


# ============================================================
# TOURNAMENT REVIEW GENERATION
# ============================================================

def generate_tournament_linkedin_summary(
    matches: list,
    tournament_name: str,
    client: anthropic.Anthropic,
) -> str:
    """
    Generate a comprehensive LinkedIn tournament summary (400-500 words).

    Args:
        matches: List of match data dicts.
        tournament_name: Name of the tournament (e.g., "ICC Men's T20 World Cup 2025-26").
        client: Anthropic API client.

    Returns:
        LinkedIn post text (400-500 words).
    """
    match_summary = summarise_matches_for_prompt(matches)
    num_matches = len(matches)

    prompt = f"""You are a professional cricket journalist writing a tournament review for LinkedIn.

Tournament: {tournament_name}
Number of matches covered: {num_matches}

Match-by-match data:
{match_summary}

Write a comprehensive LinkedIn tournament summary (400-500 words) that:
- Opens with a compelling headline or hook about the tournament
- Provides an overall narrative of what happened across the matches
- Highlights standout batting and bowling performances with specific statistics
- Discusses key moments or turning points that defined the tournament so far
- Mentions Player(s) of the Match and their contributions
- Includes a broader analytical insight (team form, tactical trends, emerging players)
- Ends with a forward-looking statement about what to expect next
- Uses proper paragraph structure with clear sections
- Includes 4-6 relevant cricket and tournament hashtags at the end
- Tone: authoritative, professional, analytical yet engaging

Write ONLY the post content. No preamble or meta-commentary."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_tournament_twitter_thread(
    matches: list,
    tournament_name: str,
    client: anthropic.Anthropic,
) -> list:
    """
    Generate a Twitter thread (5-6 tweets) covering the tournament.

    Args:
        matches: List of match data dicts.
        tournament_name: Name of the tournament.
        client: Anthropic API client.

    Returns:
        List of tweet strings, each ≤280 characters.
    """
    match_summary = summarise_matches_for_prompt(matches)
    num_matches = len(matches)

    prompt = f"""You are a cricket social media expert creating a Twitter/X thread.

Tournament: {tournament_name}
Number of matches covered: {num_matches}

Match-by-match data:
{match_summary}

Create a Twitter thread of exactly 5-6 tweets that:
- Tweet 1: Hook tweet introducing the tournament update with overall drama/context
- Tweet 2: Highlights from Match 1 (result, top performer, key stat)
- Tweet 3: Highlights from Match 2 (result, top performer, key stat) if applicable
- Tweet 4: Highlights from Match 3 (result, top performer, key stat) if applicable
- Tweet 5: Overall standout performer or key statistical insight
- Tweet 6: Closing tweet with outlook and call-to-action

Rules for each tweet:
- STRICTLY ≤280 characters each (including spaces, emojis, hashtags)
- Use relevant emojis (🏏🔥💥⚡🎯) sparingly
- Include 1-2 hashtags per tweet maximum
- Number each tweet: "1/" "2/" etc.
- Make each tweet standalone but connected to the thread

Output ONLY the numbered tweets, one per line, separated by a blank line."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Parse tweets from numbered list
    tweets = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Look for numbered tweets like "1/ ..." or "1. ..."
        if line and (line[0].isdigit() or line.startswith("Tweet")):
            tweet_text = line
            # Enforce 280 char limit
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            tweets.append(tweet_text)

    # Fallback: if parsing failed, split by blank lines
    if not tweets:
        chunks = [c.strip() for c in raw.split("\n\n") if c.strip()]
        for chunk in chunks:
            first_line = chunk.split("\n")[0].strip()
            if len(first_line) > 280:
                first_line = first_line[:277] + "..."
            tweets.append(first_line)

    return tweets[:6]  # Max 6 tweets


# ============================================================
# MAIN GENERATION FUNCTION
# ============================================================

def generate_tournament_review(
    matches: list,
    tournament_name: str = "ICC Men's T20 World Cup 2025-26",
) -> dict:
    """
    Generate a full tournament review (LinkedIn + Twitter thread).

    Args:
        matches: List of match data dicts from scraper.
        tournament_name: Name of the tournament.

    Returns:
        Dict with 'tournament', 'match_count', 'linkedin', 'twitter_thread'.
    """
    client = get_claude_client()

    print(f"\n📝 Generating tournament review for {len(matches)} match(es)...")
    print(f"   Tournament: {tournament_name}")

    linkedin = generate_tournament_linkedin_summary(matches, tournament_name, client)
    print("   ✅ LinkedIn tournament summary generated")

    twitter_thread = generate_tournament_twitter_thread(matches, tournament_name, client)
    print(f"   ✅ Twitter thread generated ({len(twitter_thread)} tweets)")

    return {
        "tournament": tournament_name,
        "match_count": len(matches),
        "linkedin": linkedin,
        "twitter_thread": twitter_thread,
    }


# ============================================================
# LOAD FROM FILE
# ============================================================

def generate_review_from_file(
    matches_json_path: str,
    tournament_name: str = "ICC Men's T20 World Cup 2025-26",
) -> dict:
    """
    Load scraped match data from a JSON file and generate a tournament review.

    Args:
        matches_json_path: Path to matches JSON file.
        tournament_name: Tournament name override.

    Returns:
        Tournament review dict.
    """
    with open(matches_json_path, "r") as f:
        data = json.load(f)

    matches = data.get("matches", [])
    if not matches:
        raise ValueError(f"No matches found in {matches_json_path}")

    return generate_tournament_review(matches, tournament_name)


def print_tournament_review(review: dict) -> None:
    """Pretty-print a tournament review."""
    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  TOURNAMENT REVIEW: {review['tournament']}")
    print(f"  Matches covered: {review['match_count']}")
    print(sep)

    print("\n📱 LINKEDIN TOURNAMENT SUMMARY")
    print("-" * 40)
    print(review["linkedin"])
    word_count = len(review["linkedin"].split())
    print(f"\n[Word count: {word_count}]")

    print("\n🐦 TWITTER THREAD")
    print("-" * 40)
    for tweet in review["twitter_thread"]:
        print(f"\n{tweet}")
        print(f"  [{len(tweet)} chars]")

    print(f"\n{sep}")


# ============================================================
# SAMPLE DATA FOR TESTING
# ============================================================

def get_sample_tournament_matches() -> list:
    """Return sample multi-match data for testing."""
    return [
        {
            "title": "South Africa vs UAE, 34th Match, Group D",
            "result": "South Africa won by 104 runs",
            "date": "18 Feb 2026",
            "man_of_match": "Quinton de Kock",
            "innings": [
                {
                    "innings_number": 1,
                    "team_score": "South Africa: 201/4 (20 overs)",
                    "batting": [
                        {"name": "Quinton de Kock", "runs": "89", "balls": "52"},
                        {"name": "Reeza Hendricks", "runs": "55", "balls": "38"},
                    ],
                    "bowling": [
                        {"name": "Zahoor Khan", "overs": "4", "runs": "42", "wickets": "2"},
                    ],
                },
                {
                    "innings_number": 2,
                    "team_score": "UAE: 97/10 (17.3 overs)",
                    "batting": [
                        {"name": "Muhammad Waseem", "runs": "31", "balls": "28"},
                    ],
                    "bowling": [
                        {"name": "Kagiso Rabada", "overs": "3.3", "runs": "14", "wickets": "4"},
                        {"name": "Marco Jansen", "overs": "4", "runs": "19", "wickets": "3"},
                    ],
                },
            ],
        },
        {
            "title": "Namibia vs Pakistan, 35th Match, Group A",
            "result": "Pakistan won by 7 wickets",
            "date": "18 Feb 2026",
            "man_of_match": "Babar Azam",
            "innings": [
                {
                    "innings_number": 1,
                    "team_score": "Namibia: 118/8 (20 overs)",
                    "batting": [
                        {"name": "Jan Nicol Loftie-Eaton", "runs": "44", "balls": "36"},
                    ],
                    "bowling": [
                        {"name": "Shaheen Afridi", "overs": "4", "runs": "22", "wickets": "3"},
                        {"name": "Naseem Shah", "overs": "4", "runs": "20", "wickets": "2"},
                    ],
                },
                {
                    "innings_number": 2,
                    "team_score": "Pakistan: 121/3 (15.1 overs)",
                    "batting": [
                        {"name": "Babar Azam", "runs": "62", "balls": "44"},
                        {"name": "Mohammad Rizwan", "runs": "38", "balls": "30"},
                    ],
                    "bowling": [
                        {"name": "Ruben Trumpelmann", "overs": "3", "runs": "28", "wickets": "2"},
                    ],
                },
            ],
        },
        {
            "title": "India vs Netherlands, 36th Match, Group A",
            "result": "India won by 9 wickets",
            "date": "18 Feb 2026",
            "man_of_match": "Rohit Sharma",
            "innings": [
                {
                    "innings_number": 1,
                    "team_score": "Netherlands: 130/8 (20 overs)",
                    "batting": [
                        {"name": "Max O'Dowd", "runs": "42", "balls": "35"},
                        {"name": "Vikramjit Singh", "runs": "28", "balls": "22"},
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
                    ],
                    "bowling": [
                        {"name": "Bas de Leede", "overs": "3", "runs": "28", "wickets": "1"},
                    ],
                },
            ],
        },
    ]


# ============================================================
# MAIN
# ============================================================

def main():
    """Run a test tournament review generation with sample data."""
    print("=" * 70)
    print("🏏 Editorial Writer - Tournament Review Test")
    print("=" * 70)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set. Please export it before running.")
        return

    matches = get_sample_tournament_matches()
    review = generate_tournament_review(matches)
    print_tournament_review(review)

    output_file = "sample_tournament_review.json"
    with open(output_file, "w") as f:
        json.dump(review, f, indent=2)
    print(f"\n💾 Review saved to: {output_file}")


if __name__ == "__main__":
    main()
