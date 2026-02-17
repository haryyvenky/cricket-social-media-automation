import requests
import json
from datetime import datetime
import os

# ============================================================
# CONFIGURATION
# ============================================================
API_KEY = os.environ.get("CRICKETDATA_API_KEY")
BASE_URL = "https://api.cricapi.com/v1"

# Matches already posted - add IDs here after each post to avoid reposting
ALREADY_POSTED = []

# Validate API key exists
if not API_KEY:
    raise ValueError("❌ CRICKETDATA_API_KEY secret is missing! Add it in GitHub Settings → Secrets.")


# ============================================================
# API FUNCTIONS
# ============================================================

def get_current_matches():
    """Fetch all current/recent matches from CricketData.org"""
    url = f"{BASE_URL}/matches"
    params = {
        "apikey": API_KEY,
        "offset": 0
    }

    print("📡 Fetching matches from CricketData.org...")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"   HTTP Status: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        print(f"   API Status: {data.get('status')}")

        if data.get("status") != "success":
            print(f"❌ API Error: {data.get('reason', 'Unknown error')}")
            return []

        matches = data.get("data", [])
        print(f"✅ Found {len(matches)} total matches")
        return matches

    except Exception as e:
        print(f"❌ Error fetching matches: {e}")
        return []


def get_match_scorecard(match_id):
    """Fetch full scorecard for a specific match"""
    url = f"{BASE_URL}/match_scorecard"
    params = {
        "apikey": API_KEY,
        "id": match_id
    }

    print(f"   Fetching scorecard for match ID: {match_id}")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            print(f"  ❌ Scorecard error: {data.get('reason', 'Unknown error')}")
            return None

        return data.get("data", {})

    except Exception as e:
        print(f"  ❌ Error fetching scorecard: {e}")
        return None


# ============================================================
# FILTER FUNCTIONS
# ============================================================

def is_t20_world_cup(match):
    """Check if match belongs to T20 World Cup"""
    series = match.get("series", "").lower()
    name = match.get("name", "").lower()

    return (
        "t20 world cup" in series or
        "icc men's t20" in series or
        "icc t20" in series or
        "t20 world cup" in name
    )


def is_completed(match):
    """Check if match is completed (not live, not upcoming)"""
    status = match.get("status", "").lower()
    match_ended = match.get("matchEnded", False)

    return (
        match_ended == True or
        "won" in status or
        "tied" in status or
        "abandoned" in status or
        "no result" in status
    )


def is_already_posted(match_id):
    """Check if we've already posted about this match"""
    return match_id in ALREADY_POSTED


# ============================================================
# PARSE FUNCTIONS
# ============================================================

def parse_match(match, scorecard):
    """Parse match and scorecard into clean structured data"""

    parsed = {
        "match_id": match.get("id", ""),
        "name": match.get("name", ""),
        "status": match.get("status", ""),
        "venue": match.get("venue", ""),
        "date": match.get("date", ""),
        "match_type": match.get("matchType", ""),
        "series": match.get("series", ""),
        "teams": match.get("teams", []),
        "toss": {},
        "innings": [],
        "player_of_match": ""
    }

    if not scorecard:
        return parsed

    # Extract toss info
    if "tossResults" in scorecard:
        toss = scorecard["tossResults"]
        parsed["toss"] = {
            "winner": toss.get("tossWinner", ""),
            "decision": toss.get("tossDecision", "")
        }

    # Extract player of match
    parsed["player_of_match"] = scorecard.get("playerOfMatch", "")

    # Extract innings
    scorecard_data = scorecard.get("scorecard", [])
    for inning in scorecard_data:
        inning_parsed = {
            "team": inning.get("inningsTeamName", ""),
            "runs": inning.get("inningsRuns", 0),
            "wickets": inning.get("inningsWickets", 0),
            "overs": inning.get("inningsOvers", 0),
            "batting": [],
            "bowling": []
        }

        # Top batsmen
        for batsman in inning.get("batting", []):
            if batsman.get("dismissal-wicket") == "DNB":
                continue
            inning_parsed["batting"].append({
                "name": batsman.get("batsmanName", ""),
                "runs": batsman.get("runs", 0),
                "balls": batsman.get("balls", 0),
                "fours": batsman.get("fours", 0),
                "sixes": batsman.get("sixes", 0),
                "strike_rate": batsman.get("strikeRate", 0),
                "dismissal": batsman.get("dismissal-wicket", "not out")
            })

        # Top bowlers
        for bowler in inning.get("bowling", []):
            inning_parsed["bowling"].append({
                "name": bowler.get("bowlerName", ""),
                "overs": bowler.get("overs", 0),
                "maidens": bowler.get("maidens", 0),
                "runs": bowler.get("runs", 0),
                "wickets": bowler.get("wickets", 0),
                "economy": bowler.get("economy", 0)
            })

        parsed["innings"].append(inning_parsed)

    return parsed


def display_match_summary(match_data):
    """Display a formatted match summary in the console"""
    print("\n" + "=" * 70)
    print(f"  {match_data['name']}")
    print("=" * 70)
    print(f"📍 Venue:  {match_data['venue']}")
    print(f"📅 Date:   {match_data['date']}")
    print(f"🏆 Result: {match_data['status']}")

    if match_data["toss"]:
        toss = match_data["toss"]
        print(f"🪙 Toss:   {toss.get('winner', '')} won, chose to {toss.get('decision', '')}")

    print("\n📊 SCORECARD:")
    print("-" * 70)

    for inning in match_data["innings"]:
        print(f"\n🏏 {inning['team']}: {inning['runs']}/{inning['wickets']} ({inning['overs']} overs)")

        if inning["batting"]:
            print("\n  Top Batsmen:")
            for b in inning["batting"][:5]:
                print(f"    {b['name']}: {b['runs']}({b['balls']}) "
                      f"4s:{b['fours']} 6s:{b['sixes']} SR:{b['strike_rate']}")

        if inning["bowling"]:
            print("\n  Bowling:")
            sorted_bowlers = sorted(inning["bowling"], key=lambda x: -x["wickets"])
            for b in sorted_bowlers[:4]:
                print(f"    {b['name']}: {b['wickets']}/{b['runs']} "
                      f"({b['overs']} ov) Econ:{b['economy']}")

    if match_data["player_of_match"]:
        print(f"\n⭐ Player of the Match: {match_data['player_of_match']}")

    print("=" * 70)


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    print("🏏 Cricket Social Media Automation")
    print("=" * 70)
    print(f"📅 Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"🎯 Looking for: Completed T20 World Cup matches")
    print("=" * 70)

    # Step 1: Get all matches
    all_matches = get_current_matches()

    if not all_matches:
        print("⚠️  No matches returned from API")
        return

    # Step 2: Print all matches found (for debugging)
    print(f"\n📋 All matches returned by API:")
    for m in all_matches:
        print(f"   - {m.get('name')} | Series: {m.get('series','N/A')} | Status: {m.get('status','N/A')} | Ended: {m.get('matchEnded','N/A')}")

    # Step 3: Filter T20 World Cup completed matches
    print(f"\n🔍 Filtering for completed T20 World Cup matches...")
    t20_wc_matches = []

    for match in all_matches:
        match_name = match.get("name", "")
        match_id = match.get("id", "")
        status = match.get("status", "")

        if not is_t20_world_cup(match):
            continue

        if not is_completed(match):
            print(f"  ⏳ Skipping (not completed): {match_name} - {status}")
            continue

        if is_already_posted(match_id):
            print(f"  ✅ Skipping (already posted): {match_name}")
            continue

        print(f"  ✅ New completed match: {match_name}")
        t20_wc_matches.append(match)

    if not t20_wc_matches:
        print("\n⚠️  No new completed T20 World Cup matches found")
        return

    print(f"\n🎯 Processing {len(t20_wc_matches)} match(es)...")

    # Step 4: Fetch scorecard and save each match
    all_match_data = []
    today = datetime.now().strftime("%Y%m%d")

    for match in t20_wc_matches:
        match_id = match.get("id")
        match_name = match.get("name")

        print(f"\n📥 Fetching scorecard: {match_name}")
        scorecard = get_match_scorecard(match_id)
        match_data = parse_match(match, scorecard)

        display_match_summary(match_data)

        filename = f"match_{match_id}_{today}.json"
        with open(filename, "w") as f:
            json.dump(match_data, f, indent=2)
        print(f"\n💾 Saved: {filename}")

        all_match_data.append(match_data)

    # Step 5: Save combined daily summary
    if all_match_data:
        summary_file = f"daily_matches_{today}.json"
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_matches": len(all_match_data),
            "matches": all_match_data
        }
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n✅ Daily summary saved: {summary_file}")
        print(f"✅ Total matches processed: {len(all_match_data)}")


if __name__ == "__main__":
    main()
