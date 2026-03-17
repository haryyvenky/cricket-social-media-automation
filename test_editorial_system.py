#!/usr/bin/env python3
"""
test_editorial_system.py

Test suite for the cricket editorial content generation system.

Run this script to verify everything works:

    python test_editorial_system.py              # offline unit tests only
    python test_editorial_system.py --all        # include AI generation tests (needs ANTHROPIC_API_KEY)

Tests are split into two groups:
  - Offline tests  : test data-extraction helpers, no API key needed, always run
  - AI tests       : test Claude-powered generation, require ANTHROPIC_API_KEY, run with --all
"""

import json
import os
import sys
import traceback
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

_passed = 0
_failed = 0
_skipped = 0


def _ok(name: str) -> None:
    global _passed
    _passed += 1
    print(f"  ✅ PASS  {name}")


def _fail(name: str, reason: str) -> None:
    global _failed
    _failed += 1
    print(f"  ❌ FAIL  {name}")
    print(f"           {reason}")


def _skip(name: str, reason: str) -> None:
    global _skipped
    _skipped += 1
    print(f"  ⏭️  SKIP  {name}  ({reason})")


def _section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def _summary() -> bool:
    total = _passed + _failed + _skipped
    print(f"\n{'=' * 60}")
    print(f"  Results: {_passed} passed, {_failed} failed, {_skipped} skipped  (total {total})")
    print(f"{'=' * 60}")
    return _failed == 0


# ─────────────────────────────────────────────────────────────
# OFFLINE TESTS — no network or API key needed
# ─────────────────────────────────────────────────────────────

def test_extract_key_batting_top3():
    name = "extract_key_batting returns top 3 by runs"
    try:
        from match_editorial_generator import extract_key_batting, get_sample_match_data
        match = get_sample_match_data()
        result = extract_key_batting(match["innings"], top_n=3)
        assert len(result) == 3, f"expected 3, got {len(result)}"
        # Should be sorted highest runs first
        assert result[0]["runs"] >= result[1]["runs"] >= result[2]["runs"], "not sorted"
        assert result[0]["name"] == "Rohit Sharma", f"unexpected top batsman: {result[0]['name']}"
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_extract_key_batting_strike_rate():
    name = "extract_key_batting computes strike rate correctly"
    try:
        from match_editorial_generator import extract_key_batting
        innings = [{"innings_number": 1, "team_score": "Test", "batting": [
            {"name": "Player A", "runs": "50", "balls": "25"},
        ], "bowling": []}]
        result = extract_key_batting(innings, top_n=1)
        assert result[0]["strike_rate"] == 200.0, f"SR should be 200.0, got {result[0]['strike_rate']}"
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_extract_key_batting_skips_invalid():
    name = "extract_key_batting skips rows with non-numeric runs/balls"
    try:
        from match_editorial_generator import extract_key_batting
        innings = [{"innings_number": 1, "team_score": "Test", "batting": [
            {"name": "Good Player", "runs": "40", "balls": "30"},
            {"name": "Bad Row",    "runs": "DNB", "balls": "-"},
        ], "bowling": []}]
        result = extract_key_batting(innings, top_n=5)
        assert len(result) == 1, f"should have 1 valid batsman, got {len(result)}"
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_extract_key_bowling_top2():
    name = "extract_key_bowling returns top 2 sorted by wickets then economy"
    try:
        from match_editorial_generator import extract_key_bowling, get_sample_match_data
        match = get_sample_match_data()
        result = extract_key_bowling(match["innings"], top_n=2)
        assert len(result) == 2, f"expected 2, got {len(result)}"
        # Bumrah: 3 wkts should be first
        assert result[0]["name"] == "Jasprit Bumrah", f"unexpected top bowler: {result[0]['name']}"
        assert result[0]["wickets"] >= result[1]["wickets"], "not sorted by wickets"
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_extract_key_bowling_economy():
    name = "extract_key_bowling computes economy correctly"
    try:
        from match_editorial_generator import extract_key_bowling
        innings = [{"innings_number": 1, "team_score": "Test", "batting": [], "bowling": [
            {"name": "Fast Bowler", "overs": "4", "runs": "28", "wickets": "2"},
        ]}]
        result = extract_key_bowling(innings, top_n=1)
        assert result[0]["economy"] == 7.0, f"economy should be 7.0, got {result[0]['economy']}"
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_build_match_context_contains_key_fields():
    name = "build_match_context includes title, result, venue, MoM, batting, bowling"
    try:
        from match_editorial_generator import build_match_context, get_sample_match_data
        match = get_sample_match_data()
        context = build_match_context(match)
        for keyword in ["India vs Netherlands", "India won by 9 wickets",
                        "Rohit Sharma", "Jasprit Bumrah", "Key Batting", "Key Bowling"]:
            assert keyword in context, f"'{keyword}' missing from context"
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_build_match_context_empty_innings():
    name = "build_match_context handles match with no innings gracefully"
    try:
        from match_editorial_generator import build_match_context
        match = {"title": "Test Match", "result": "No result", "innings": []}
        context = build_match_context(match)
        assert "Test Match" in context
        assert "No result" in context
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_summarise_matches_for_prompt():
    name = "summarise_matches_for_prompt includes all three match titles"
    try:
        from editorial_writer import summarise_matches_for_prompt, get_sample_tournament_matches
        matches = get_sample_tournament_matches()
        summary = summarise_matches_for_prompt(matches)
        assert "South Africa vs UAE" in summary
        assert "Namibia vs Pakistan" in summary
        assert "India vs Netherlands" in summary
        assert "Quinton de Kock" in summary   # top bat SA match
        assert "Kagiso Rabada" in summary     # top bowler SA match
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_pipeline_step1_sample_data():
    name = "step1_load_match_data returns 3-match sample when no file given"
    try:
        from full_pipeline_example import step1_load_match_data
        matches = step1_load_match_data(None)
        assert len(matches) == 3, f"expected 3, got {len(matches)}"
        titles = [m.get("title", "") for m in matches]
        assert any("South Africa" in t for t in titles)
        assert any("Pakistan" in t for t in titles)
        assert any("India" in t for t in titles)
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_pipeline_step1_loads_json_file(tmp_path=None):
    name = "step1_load_match_data reads a real JSON file correctly"
    try:
        from full_pipeline_example import step1_load_match_data

        # Write a minimal matches JSON to a temp file
        payload = {
            "date": "2026-02-18",
            "total_matches": 1,
            "matches": [{"title": "File Match", "result": "A won", "innings": []}],
        }
        tmp_file = "/tmp/test_matches_temp.json"
        with open(tmp_file, "w") as f:
            json.dump(payload, f)

        matches = step1_load_match_data(tmp_file)
        assert len(matches) == 1, f"expected 1, got {len(matches)}"
        assert matches[0]["title"] == "File Match"

        os.remove(tmp_file)
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_pipeline_step1_fallback_on_missing_file():
    name = "step1_load_match_data falls back to sample data if file missing"
    try:
        from full_pipeline_example import step1_load_match_data
        matches = step1_load_match_data("/tmp/does_not_exist_xyz.json")
        # Should return sample data (3 matches), not raise
        assert len(matches) == 3
        _ok(name)
    except Exception as e:
        _fail(name, str(e))


def test_twitter_truncation():
    name = "generate_twitter_post truncates output longer than 280 chars"
    try:
        from match_editorial_generator import generate_twitter_post

        # Monkey-patch the client to return a very long string
        class FakeMessage:
            class _Content:
                text = "X" * 300
            content = [_Content()]

        class FakeClient:
            def messages(self):
                pass
            class _Messages:
                @staticmethod
                def create(**kwargs):
                    return FakeMessage()
            messages = _Messages()

        match = {"title": "Test", "result": "A won", "innings": []}

        # Patch at module level temporarily
        import match_editorial_generator as meg
        original = meg.anthropic.Anthropic

        class MockAnthropic:
            def __init__(self, api_key=None):
                pass
            class messages:
                @staticmethod
                def create(**kwargs):
                    return FakeMessage()

        meg.anthropic.Anthropic = MockAnthropic
        try:
            client = MockAnthropic()
            tweet = generate_twitter_post(match, client)
            assert len(tweet) <= 280, f"tweet is {len(tweet)} chars"
        finally:
            meg.anthropic.Anthropic = original

        _ok(name)
    except Exception as e:
        _fail(name, str(e))


# ─────────────────────────────────────────────────────────────
# AI INTEGRATION TESTS — require ANTHROPIC_API_KEY
# ─────────────────────────────────────────────────────────────

def test_generate_match_editorial_linkedin_length():
    name = "generate_match_editorial: LinkedIn post is 100-350 words"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _skip(name, "ANTHROPIC_API_KEY not set")
        return
    try:
        from match_editorial_generator import generate_match_editorial, get_sample_match_data
        match = get_sample_match_data()
        editorial = generate_match_editorial(match)
        word_count = len(editorial["linkedin"].split())
        assert 100 <= word_count <= 350, f"word count {word_count} out of expected range 100-350"
        _ok(name)
    except Exception as e:
        _fail(name, traceback.format_exc())


def test_generate_match_editorial_twitter_length():
    name = "generate_match_editorial: Twitter post is ≤280 chars"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _skip(name, "ANTHROPIC_API_KEY not set")
        return
    try:
        from match_editorial_generator import generate_match_editorial, get_sample_match_data
        match = get_sample_match_data()
        editorial = generate_match_editorial(match)
        char_count = len(editorial["twitter"])
        assert char_count <= 280, f"tweet is {char_count} chars (must be ≤280)"
        _ok(name)
    except Exception as e:
        _fail(name, traceback.format_exc())


def test_generate_match_editorial_output_keys():
    name = "generate_match_editorial: output dict has required keys"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _skip(name, "ANTHROPIC_API_KEY not set")
        return
    try:
        from match_editorial_generator import generate_match_editorial, get_sample_match_data
        editorial = generate_match_editorial(get_sample_match_data())
        for key in ["match_title", "result", "linkedin", "twitter"]:
            assert key in editorial, f"missing key: {key}"
            assert editorial[key], f"empty value for key: {key}"
        _ok(name)
    except Exception as e:
        _fail(name, traceback.format_exc())


def test_generate_tournament_review_linkedin_length():
    name = "generate_tournament_review: LinkedIn summary is 200-600 words"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _skip(name, "ANTHROPIC_API_KEY not set")
        return
    try:
        from editorial_writer import generate_tournament_review, get_sample_tournament_matches
        review = generate_tournament_review(get_sample_tournament_matches())
        word_count = len(review["linkedin"].split())
        assert 200 <= word_count <= 600, f"word count {word_count} out of expected range 200-600"
        _ok(name)
    except Exception as e:
        _fail(name, traceback.format_exc())


def test_generate_tournament_review_thread_count():
    name = "generate_tournament_review: Twitter thread has 3-6 tweets"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _skip(name, "ANTHROPIC_API_KEY not set")
        return
    try:
        from editorial_writer import generate_tournament_review, get_sample_tournament_matches
        review = generate_tournament_review(get_sample_tournament_matches())
        count = len(review["twitter_thread"])
        assert 3 <= count <= 6, f"thread has {count} tweets (expected 3-6)"
        _ok(name)
    except Exception as e:
        _fail(name, traceback.format_exc())


def test_generate_tournament_review_tweet_lengths():
    name = "generate_tournament_review: each tweet is ≤280 chars"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _skip(name, "ANTHROPIC_API_KEY not set")
        return
    try:
        from editorial_writer import generate_tournament_review, get_sample_tournament_matches
        review = generate_tournament_review(get_sample_tournament_matches())
        for i, tweet in enumerate(review["twitter_thread"]):
            assert len(tweet) <= 280, f"tweet {i+1} is {len(tweet)} chars (must be ≤280)"
        _ok(name)
    except Exception as e:
        _fail(name, traceback.format_exc())


def test_full_pipeline_produces_package_file():
    name = "run_full_pipeline: creates publishing_package_*.json"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _skip(name, "ANTHROPIC_API_KEY not set")
        return
    try:
        from full_pipeline_example import run_full_pipeline
        package = run_full_pipeline(display_output=False)

        date_str = datetime.now().strftime("%Y%m%d")
        expected_file = f"publishing_package_{date_str}.json"
        assert os.path.exists(expected_file), f"output file not found: {expected_file}"

        with open(expected_file) as f:
            data = json.load(f)
        assert data["match_count"] == 3
        assert len(data["individual_match_editorials"]) == 3
        assert "linkedin" in data["tournament_review"]
        assert "twitter_thread" in data["tournament_review"]

        os.remove(expected_file)
        _ok(name)
    except Exception as e:
        _fail(name, traceback.format_exc())


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    run_ai_tests = "--all" in sys.argv

    print("=" * 60)
    print("  🏏 Cricket Editorial System — Test Suite")
    if run_ai_tests:
        print("  Mode: ALL tests (offline + AI generation)")
    else:
        print("  Mode: Offline tests only")
        print("  Tip : Run with --all to include AI generation tests")
    print("=" * 60)

    # ── Offline tests ──────────────────────────────────────────
    _section("Offline: data extraction helpers")
    test_extract_key_batting_top3()
    test_extract_key_batting_strike_rate()
    test_extract_key_batting_skips_invalid()
    test_extract_key_bowling_top2()
    test_extract_key_bowling_economy()

    _section("Offline: context builders")
    test_build_match_context_contains_key_fields()
    test_build_match_context_empty_innings()
    test_summarise_matches_for_prompt()

    _section("Offline: pipeline data-loading")
    test_pipeline_step1_sample_data()
    test_pipeline_step1_loads_json_file()
    test_pipeline_step1_fallback_on_missing_file()

    _section("Offline: character-limit enforcement")
    test_twitter_truncation()

    # ── AI integration tests ───────────────────────────────────
    if run_ai_tests:
        _section("AI: individual match editorial (calls Claude API)")
        test_generate_match_editorial_output_keys()
        test_generate_match_editorial_linkedin_length()
        test_generate_match_editorial_twitter_length()

        _section("AI: tournament review (calls Claude API)")
        test_generate_tournament_review_linkedin_length()
        test_generate_tournament_review_thread_count()
        test_generate_tournament_review_tweet_lengths()

        _section("AI: full pipeline (calls Claude API)")
        test_full_pipeline_produces_package_file()
    else:
        _section("AI tests skipped (run with --all to enable)")
        ai_tests = [
            "generate_match_editorial: output dict has required keys",
            "generate_match_editorial: LinkedIn post is 100-350 words",
            "generate_match_editorial: Twitter post is ≤280 chars",
            "generate_tournament_review: LinkedIn summary is 200-600 words",
            "generate_tournament_review: Twitter thread has 3-6 tweets",
            "generate_tournament_review: each tweet is ≤280 chars",
            "run_full_pipeline: creates publishing_package_*.json",
        ]
        for t in ai_tests:
            _skip(t, "pass --all flag to run AI tests")

    ok = _summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
