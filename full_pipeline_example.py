#!/usr/bin/env python3
"""
full_pipeline_example.py

Demonstrates the complete workflow:
  Scrape → Analyze → Generate Editorial → Output Publishing Package

This script shows how to:
1. Use existing scraped match data (or run the scraper live)
2. Generate LinkedIn and Twitter posts for individual matches
3. Generate a tournament-level review
4. Bundle everything into a publishing-ready package
"""

import json
import os
from datetime import datetime

from match_editorial_generator import (
    generate_match_editorial,
    get_sample_match_data,
    print_editorial,
)
from editorial_writer import (
    generate_tournament_review,
    get_sample_tournament_matches,
    print_tournament_review,
)


# ============================================================
# PIPELINE STEPS
# ============================================================

def step1_load_match_data(json_path: str = None) -> list:
    """
    Step 1: Load match data.

    Loads scraped match data from a JSON file produced by scrape_espn_matches.py.
    Falls back to built-in sample data if no file is provided.

    Args:
        json_path: Path to a matches_YYYYMMDD.json file, or None for sample data.

    Returns:
        List of match data dicts.
    """
    if json_path and os.path.exists(json_path):
        print(f"📂 Loading match data from: {json_path}")
        with open(json_path, "r") as f:
            data = json.load(f)
        matches = data.get("matches", [])
        print(f"   ✅ Loaded {len(matches)} match(es)")
        return matches
    else:
        if json_path:
            print(f"⚠️  File not found: {json_path}. Using sample data.")
        else:
            print("📂 No file provided. Using built-in sample match data.")
        matches = get_sample_tournament_matches()
        print(f"   ✅ Sample data: {len(matches)} match(es)")
        return matches


def step2_generate_individual_editorials(matches: list) -> list:
    """
    Step 2: Generate LinkedIn + Twitter posts for each individual match.

    Args:
        matches: List of match data dicts.

    Returns:
        List of editorial dicts, one per match.
    """
    print(f"\n📝 Step 2: Generating individual match editorials...")
    editorials = []
    for i, match in enumerate(matches, 1):
        print(f"\n   [{i}/{len(matches)}] {match.get('title', 'Unknown Match')}")
        editorial = generate_match_editorial(match)
        editorials.append(editorial)
    print(f"\n   ✅ Generated {len(editorials)} match editorial(s)")
    return editorials


def step3_generate_tournament_review(
    matches: list,
    tournament_name: str = "ICC Men's T20 World Cup 2025-26",
) -> dict:
    """
    Step 3: Generate a comprehensive tournament-level review.

    Args:
        matches: List of match data dicts.
        tournament_name: Name of the tournament.

    Returns:
        Tournament review dict with LinkedIn and Twitter thread.
    """
    print(f"\n🏆 Step 3: Generating tournament review...")
    review = generate_tournament_review(matches, tournament_name)
    print(f"   ✅ Tournament review generated")
    return review


def step4_bundle_publishing_package(
    editorials: list,
    tournament_review: dict,
    date_str: str = None,
) -> dict:
    """
    Step 4: Bundle everything into a publishing-ready package.

    Args:
        editorials: List of individual match editorials.
        tournament_review: Tournament-level review dict.
        date_str: Date string for the output file name (YYYYMMDD).

    Returns:
        Complete publishing package dict.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    package = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": date_str,
        "tournament": tournament_review.get("tournament", ""),
        "match_count": len(editorials),
        "individual_match_editorials": editorials,
        "tournament_review": tournament_review,
    }

    output_file = f"publishing_package_{date_str}.json"
    with open(output_file, "w") as f:
        json.dump(package, f, indent=2)

    print(f"\n💾 Step 4: Publishing package saved to: {output_file}")
    return package


# ============================================================
# DISPLAY HELPERS
# ============================================================

def display_full_package(package: dict) -> None:
    """Display the complete publishing package in a readable format."""
    sep = "=" * 70

    print(f"\n{sep}")
    print("  📦 COMPLETE PUBLISHING PACKAGE")
    print(f"  Generated: {package['generated_at']}")
    print(f"  Tournament: {package['tournament']}")
    print(f"  Matches: {package['match_count']}")
    print(sep)

    # Individual match editorials
    print("\n" + "─" * 70)
    print("  INDIVIDUAL MATCH EDITORIALS")
    print("─" * 70)
    for editorial in package["individual_match_editorials"]:
        print_editorial(editorial)

    # Tournament review
    print("\n" + "─" * 70)
    print("  TOURNAMENT REVIEW")
    print("─" * 70)
    print_tournament_review(package["tournament_review"])


# ============================================================
# FULL PIPELINE
# ============================================================

def run_full_pipeline(
    matches_json_path: str = None,
    tournament_name: str = "ICC Men's T20 World Cup 2025-26",
    display_output: bool = True,
) -> dict:
    """
    Run the complete editorial generation pipeline.

    Args:
        matches_json_path: Path to scraped matches JSON file (None = use sample data).
        tournament_name: Tournament name for the review.
        display_output: Whether to print the output to stdout.

    Returns:
        Complete publishing package dict.
    """
    print("=" * 70)
    print("🏏 Full Pipeline: Scrape → Analyze → Editorial → Publish")
    print("=" * 70)

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Export it with: export ANTHROPIC_API_KEY=your_key_here"
        )

    # Step 1: Load data
    matches = step1_load_match_data(matches_json_path)

    # Step 2: Individual match editorials
    editorials = step2_generate_individual_editorials(matches)

    # Step 3: Tournament review
    tournament_review = step3_generate_tournament_review(matches, tournament_name)

    # Step 4: Bundle package
    date_str = datetime.now().strftime("%Y%m%d")
    package = step4_bundle_publishing_package(editorials, tournament_review, date_str)

    # Display
    if display_output:
        display_full_package(package)

    print("\n" + "=" * 70)
    print("✅ Pipeline complete!")
    print(f"   Matches processed: {len(matches)}")
    print(f"   Editorials generated: {len(editorials)}")
    print(f"   Output: publishing_package_{date_str}.json")
    print("=" * 70)

    return package


# ============================================================
# MAIN
# ============================================================

def main():
    """
    Demonstrate the full pipeline with sample data.

    To use real scraped data, pass the path to a matches JSON file:
        python full_pipeline_example.py matches_20260218.json
    """
    import sys

    json_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        package = run_full_pipeline(
            matches_json_path=json_path,
            tournament_name="ICC Men's T20 World Cup 2025-26",
            display_output=True,
        )
    except EnvironmentError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
