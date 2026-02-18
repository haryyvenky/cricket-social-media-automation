import requests
import json

# Your Sportmonks API token
API_TOKEN = "brVvonMxTmDuRdo3amoHdoWZw8uUq1RFrtkeJ7SnFOvzYTHUtpJtyR7sHwwp"
BASE_URL = "https://cricket.sportmonks.com/api/v2.0"

def test_scorecard_fetch():
    """
    Fetch a complete scorecard from a T20I match to see data quality.
    Using match ID 10776 - England vs New Zealand 5th T20I (Super Over thriller!)
    """
    
    print("🏏 Sportmonks Scorecard Test")
    print("=" * 70)
    print("Testing match: England vs New Zealand 5th T20I")
    print("(Match tied - England won in super over)")
    print("=" * 70)
    
    match_id = 10776
    
    # Fetch fixture with all includes to get full scorecard
    url = f"{BASE_URL}/fixtures/{match_id}"
    
    # Request all the detailed data
    params = {
        "api_token": API_TOKEN,
        "include": "runs,batting,bowling,lineup,scoreboards,venue,league,stage,localteam,visitorteam"
    }
    
    print(f"\n📥 Fetching fixture ID: {match_id}")
    print(f"URL: {url}")
    print(f"Includes: {params['include']}")
    print("-" * 70)
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Save full response
            with open("sportmonks_full_scorecard.json", "w") as f:
                json.dump(data, f, indent=2)
            print("✅ Full scorecard fetched successfully!")
            print(f"📁 Saved to: sportmonks_full_scorecard.json")
            
            # Parse and display key information
            if "data" in data:
                fixture = data["data"]
                
                print("\n" + "=" * 70)
                print("MATCH SUMMARY")
                print("=" * 70)
                
                # Basic info
                print(f"Match Type: {fixture.get('type', 'N/A')}")
                print(f"Status: {fixture.get('status', 'N/A')}")
                print(f"Result: {fixture.get('note', 'N/A')}")
                print(f"Man of Match: Player ID {fixture.get('man_of_match_id', 'N/A')}")
                print(f"Super Over: {fixture.get('super_over', False)}")
                
                # Teams
                if 'localteam' in fixture:
                    print(f"\nLocal Team: {fixture['localteam'].get('name', 'N/A')}")
                if 'visitorteam' in fixture:
                    print(f"Visitor Team: {fixture['visitorteam'].get('name', 'N/A')}")
                
                # Check what data we got
                print("\n" + "-" * 70)
                print("AVAILABLE DATA SECTIONS:")
                print("-" * 70)
                
                available_sections = []
                for key in ['runs', 'batting', 'bowling', 'scoreboards', 'lineup']:
                    if key in fixture:
                        count = len(fixture[key]) if isinstance(fixture[key], list) else 1
                        print(f"✅ {key}: {count} record(s)")
                        available_sections.append(key)
                    else:
                        print(f"❌ {key}: Not available")
                
                # Show scoreboards if available
                if 'scoreboards' in fixture and fixture['scoreboards']:
                    print("\n" + "=" * 70)
                    print("SCORECARD")
                    print("=" * 70)
                    
                    for board in fixture['scoreboards']:
                        team = board.get('team', 'Unknown')
                        total = board.get('total', 0)
                        wickets = board.get('wickets', 0)
                        overs = board.get('overs', 0)
                        print(f"\n{team}: {total}/{wickets} ({overs} overs)")
                
                # Show batting if available
                if 'batting' in fixture and fixture['batting']:
                    print("\n" + "-" * 70)
                    print("BATTING DETAILS:")
                    print("-" * 70)
                    
                    for innings in fixture['batting'][:10]:  # First 10 batsmen
                        player_name = innings.get('player_name', 'Unknown')
                        score = innings.get('score', 0)
                        ball = innings.get('ball', 0)
                        fours = innings.get('four_x', 0)
                        sixes = innings.get('six_x', 0)
                        sr = innings.get('rate', 0)
                        
                        print(f"  {player_name}: {score}({ball}) - 4s:{fours} 6s:{sixes} SR:{sr}")
                
                # Show bowling if available
                if 'bowling' in fixture and fixture['bowling']:
                    print("\n" + "-" * 70)
                    print("BOWLING DETAILS:")
                    print("-" * 70)
                    
                    for spell in fixture['bowling'][:10]:  # First 10 bowlers
                        bowler_name = spell.get('player_name', 'Unknown')
                        overs = spell.get('overs', 0)
                        maidens = spell.get('medians', 0)
                        runs = spell.get('runs', 0)
                        wickets = spell.get('wickets', 0)
                        econ = spell.get('rate', 0)
                        
                        print(f"  {bowler_name}: {wickets}/{runs} ({overs} ov) M:{maidens} Econ:{econ}")
                
                print("\n" + "=" * 70)
                print("✅ TEST COMPLETE!")
                print("=" * 70)
                print("\nKey Findings:")
                print(f"  • Data sections available: {', '.join(available_sections)}")
                print(f"  • Full JSON saved for detailed inspection")
                print("\nNext: Review the JSON file to see complete data structure")
                
        elif response.status_code == 401:
            print("❌ Authentication Failed")
        elif response.status_code == 403:
            print("❌ Access Forbidden - You might not have access to detailed data")
        elif response.status_code == 404:
            print("❌ Match not found")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_scorecard_fetch()
