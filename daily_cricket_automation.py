import requests
import json
from datetime import datetime, date
import os

# ============================================================
# CONFIGURATION
# ============================================================
API_KEY = os.environ.get("CRICKETDATA_API_KEY")
BASE_URL = "https://api.cricapi.com/v1"

# ⚠️ TEST MODE: Set a specific date and/or match to fetch
# Change to None when going live!
TEST_DATE = "2026-02-15"  # Sunday 15th Feb
TEST_MATCH_NAME = "India vs Pakistan"  # Only fetch this specific match (case-insensitive)

# Matches already posted - add match IDs here to skip reposting
ALREADY_POSTED = []

# Validate API key
if not API_KEY:
    raise ValueError("❌ CRICKETDATA_API_KEY secret is missing!")


# ============================================================
# API FUNCTIONS
# ============================================================

def get_current_matches():
    """Fetch all current/recent matches"""
    url = f"{BASE_URL}/matches"
    params = {"apikey": API_KEY, "offset": 0}

    print("📡 Fetching matches from CricketData.org...")
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        hits_used = data.get('info', {}).get('hitsUsed', 'N/A')
        hits_limit = data.get('info', {}).get('hitsLimit', 'N/A')
        hits_today = data.get('info', {}).get('hitsToday', 'N/A')
        print(f"   📊 API Hits: {hits_today} used today / {hits_limit} daily limit")

        if data.get("status") != "success":
            print(f"❌ API Error: {data.get('reason', 'Unknown error')}")
            return []

        matches = data.get("data", [])
        print(f"✅ Total matches returned by API: {len(matches)}")
        return matches

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def get_match_scorecard(match_id, match_name):
    """Fetch full scorecard for a specific match"""
    url = f"{BASE_URL}/match_scorecard"
    params = {"apikey": API_KEY, "id": match_id}

    print(f"\n   📥 Fetching scorecard: {match_name}")
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        hits_today = data.get('info', {}).get('hitsToday', 'N/A')
        hits_limit = data.get('info', {}).get('hitsLimit', 'N/A')
        print(f"   📊 API Hits after this call: {hits_today}/{hits_limit}")

        if data.get("status") != "success":
            print(f"   ❌ Scorecard error: {data.get('reason', 'Unknown')}")
            return None

        scorecard = data.get("data", {})

        # Print raw response so we can see exact field names
        print(f"\n   🔍 RAW SCORECARD RESPONSE:")
        print(f"   Top-level keys: {list(scorecard.keys())}")
        print(json.dumps(scorecard, indent=2)[:3000])
        print("   ... (truncated if long)")

        return scorecard

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


# ============================================================
# FILTER FUNCTIONS
# ============================================================

def get_target_date():
    """Get the date we're fetching matches for"""
    if TEST_DATE:
        return datetime.strptime(TEST_DATE, "%Y-%m-%d").date()
    return date.today()


def is_main_t20_world_cup(match):
    """Check if match is a MAIN T20 WC match (excludes warm-ups)"""
    name = match.get("name", "").lower()
    series = match.get("series", "").lower()

    is_t20wc = (
        "t20 world cup" in series or
        "icc men's t20" in series or
        "icc t20 world cup" in series or
        "t20 world cup" in name
    )

    is_warmup = (
        "warm up" in name or
        "warm-up" in name or
        "warmup" in name or
        "practice" in name or
        "warm up" in series or
        "warm-up" in series
    )

    return is_t20wc and not is_warmup


def is_on_target_date(match):
    """Check if match is on the target date"""
    target = get_target_date()
    match_date_str = match.get("date", "")

    if not match_date_str:
        return False

    try:
        match_date = datetime.strptime(match_date_str, "%Y-%m-%d").date()
        return match_date == target
    except:
        return False


def is_target_match(match):
    """Check if this is the specific match we want to test"""
    if not TEST_MATCH_NAME:
        return True  # No specific match filter, include all
    
    match_name = match.get("name", "").lower()
    target_name = TEST_MATCH_NAME.lower()
    
    # Check if both team names are in the match name
    # e.g., "India vs Pakistan" should match "India vs Pakistan, 5th Match..."
    return target_name in match_name


def is_completed(match):
    """Check if match is completed"""
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
    return match_id in ALREADY_POSTED


# ============================================================
# PARSE FUNCTIONS (will update once we see real field names)
# ============================================================

def parse_scorecard(scorecard):
    """Parse scorecard innings data"""
    innings_list = []
    if not scorecard:
        return innings_list

    raw_innings = (
        scorecard.get("scorecard") or
        scorecard.get("innings") or
        scorecard.get("score") or
        []
    )

    for inning in raw_innings:
        inning_parsed = {
            "team": (
                inning.get("inningsTeamName") or
                inning.get("teamName") or
                inning.get("team") or ""
            ),
            "runs": inning.get("inningsRuns") or inning.get("runs") or 0,
            "wickets": inning.get("inningsWickets") or inning.get("wickets") or 0,
            "overs": inning.get("inningsOvers") or inning.get("overs") or 0,
            "extras": inning.get("extras") or inning.get("inningsExtras") or 0,
            "batting": [],
            "bowling": [],
            "fall_of_wickets": inning.get("fow") or inning.get("fallOfWickets") or []
        }

        # Batting
        for b in (inning.get("batting") or inning.get("batsmen") or []):
            name = b.get("batsmanName") or b.get("name") or b.get("batsman") or ""
            if not name.strip():
                continue
            inning_parsed["batting"].append({
                "name": name,
                "runs": b.get("runs", 0),
                "balls": b.get("balls", 0),
                "fours": b.get("fours") or b.get("4s") or 0,
                "sixes": b.get("sixes") or b.get("6s") or 0,
                "strike_rate": b.get("strikeRate") or b.get("sr") or 0,
                "dismissal": (
                    b.get("dismissal-wicket") or
                    b.get("wicket") or
                    b.get("dismissal") or
                    "not out"
                )
            })

        # Bowling
        for b in (inning.get("bowling") or inning.get("bowlers") or []):
            name = b.get("bowlerName") or b.get("name") or b.get("bowler") or ""
            if not name.strip():
                continue
            inning_parsed["bowling"].append({
                "name": name,
                "overs": b.get("overs", 0),
                "maidens": b.get("maidens") or b.get("m") or 0,
                "runs": b.get("runs") or b.get("r") or 0,
                "wickets": b.get("wickets") or b.get("w") or 0,
                "economy": b.get("economy") or b.get("eco") or 0
            })

        innings_list.append(inning_parsed)

    return innings_list


def parse_match(match, scorecard):
    """Parse match + scorecard into clean structured data"""
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

    if scorecard:
        toss = scorecard.get("tossResults", {})
        if toss:
            parsed["toss"] = {
                "winner": toss.get("tossWinner", ""),
                "decision": toss.get("tossDecision", "")
            }
        parsed["player_of_match"] = (
            scorecard.get("playerOfMatch") or
            scorecard.get("player_of_match") or
            scorecard.get("mom") or ""
        )
        parsed["innings"] = parse_scorecard(scorecard)

    return parsed


def display_match_summary(match_data):
    """Display formatted match summary"""
    print("\n" + "=" * 70)
    print(f"  {match_data['name']}")
    print("=" * 70)
    print(f"📍 Venue:  {match_data['venue']}")
    print(f"📅 Date:   {match_data['date']}")
    print(f"🏆 Result: {match_data['status']}")
    if match_data["toss"]:
        t = match_data["toss"]
        print(f"🪙 Toss:   {t.get('winner','')} won, chose to {t.get('decision','')}")
    for inning in match_data["innings"]:
        print(f"\n🏏 {inning['team']}: {inning['runs']}/{inning['wickets']} ({inning['overs']} overs)")
        if inning.get("extras"):
            print(f"   Extras: {inning['extras']}")
        if inning["batting"]:
            print("  Batting:")
            for b in inning["batting"]:
                print(f"    {b['name']}: {b['runs']}({b['balls']}) 4s:{b['fours']} 6s:{b['sixes']} SR:{b['strike_rate']} | {b['dismissal']}")
        if inning["bowling"]:
            print("  Bowling:")
            for b in sorted(inning["bowling"], key=lambda x: -x["wickets"]):
                print(f"    {b['name']}: {b['wickets']}/{b['runs']} ({b['overs']} ov) M:{b['maidens']} Econ:{b['economy']}")
        if inning.get("fall_of_wickets"):
            print(f"  Fall of Wickets: {inning['fall_of_wickets']}")
    if match_data["player_of_match"]:
        print(f"\n⭐ Player of the Match: {match_data['player_of_match']}")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():
    target_date = get_target_date()
    mode = f"TEST MODE - {target_date}"
    if TEST_MATCH_NAME:
        mode += f" - {TEST_MATCH_NAME} only"
    if not TEST_DATE:
        mode = f"LIVE MODE - {target_date}"

    print("🏏 Cricket Social Media Automation")
    print("=" * 70)
    print(f"📅 Run time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"🎯 Mode:      {mode}")
    print(f"🔍 Looking for: Main T20 WC completed matches")
    if TEST_MATCH_NAME:
        print(f"              Only: {TEST_MATCH_NAME}")
    print("=" * 70)

    # Fetch all matches
    all_matches = get_current_matches()
    if not all_matches:
        print("⚠️  No matches returned from API")
        return

    # Show full filter breakdown
    print(f"\n📋 Filter breakdown for all {len(all_matches)} matches:")
    print("-" * 70)
    for m in all_matches:
        main_wc = is_main_t20_world_cup(m)
        on_date = is_on_target_date(m)
        target_match = is_target_match(m)
        completed = is_completed(m)
        selected = main_wc and on_date and target_match and completed
        print(f"  {'✅' if selected else '❌'} {m.get('name', '')}")
        print(f"      Date:{m.get('date','')} | T20WC:{main_wc} | OnDate:{on_date} | TargetMatch:{target_match} | Done:{completed}")

    # Apply all filters
    target_matches = [
        m for m in all_matches
        if is_main_t20_world_cup(m)
        and is_on_target_date(m)
        and is_target_match(m)
        and is_completed(m)
        and not is_already_posted(m.get("id", ""))
    ]

    if not target_matches:
        print(f"\n⚠️  No main T20 WC matches found for {target_date}")
        return

    print(f"\n🎯 Processing {len(target_matches)} match(es) for {target_date}:")
    for m in target_matches:
        print(f"   - {m.get('name')}")

    # Fetch scorecard for each match
    all_match_data = []
    today = datetime.now().strftime("%Y%m%d")

    for match in target_matches:
        scorecard = get_match_scorecard(match.get("id"), match.get("name"))
        match_data = parse_match(match, scorecard)
        display_match_summary(match_data)

        filename = f"match_{match['id']}_{today}.json"
        with open(filename, "w") as f:
            json.dump(match_data, f, indent=2)
        print(f"💾 Saved: {filename}")
        all_match_data.append(match_data)

    if all_match_data:
        summary_file = f"daily_matches_{today}.json"
        with open(summary_file, "w") as f:
            json.dump({
                "date": str(target_date),
                "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": mode,
                "total_matches": len(all_match_data),
                "matches": all_match_data
            }, f, indent=2)
        print(f"\n✅ Daily summary saved: {summary_file}")
        print(f"✅ Total matches processed: {len(all_match_data)}")
        print(f"\n📊 API hits used this run: ~{len(target_matches) + 1}")


if __name__ == "__main__":
    main()
