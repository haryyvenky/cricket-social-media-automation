import requests
import json

# Your Sportmonks API token
API_TOKEN = "brVvonMxTmDuRdo3amoHdoWZw8uUq1RFrtkeJ7SnFOvzYTHUtpJtyR7sHwwp"
BASE_URL = "https://cricket.sportmonks.com/api/v2.0"

def test_api_connection():
    """Test if API token works and check what leagues you have access to"""
    print("🏏 Sportmonks Cricket API - Access Test")
    print("=" * 70)
    
    # Test 1: Get all leagues
    print("\n📋 TEST 1: Fetching all leagues...")
    print("-" * 70)
    
    url = f"{BASE_URL}/leagues"
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Save raw response
            with open("sportmonks_leagues_response.json", "w") as f:
                json.dump(data, f, indent=2)
            print("✅ API Token Works!")
            print(f"📁 Full response saved to: sportmonks_leagues_response.json")
            
            # Check if we have leagues data
            if "data" in data:
                leagues = data["data"]
                print(f"\n✅ You have access to {len(leagues)} league(s):")
                print("-" * 70)
                
                # Look for T20 World Cup
                t20_wc_found = False
                for league in leagues:
                    league_name = league.get("name", "N/A")
                    league_id = league.get("id", "N/A")
                    league_type = league.get("type", "N/A")
                    
                    print(f"  • {league_name}")
                    print(f"    ID: {league_id} | Type: {league_type}")
                    
                    # Check if this is T20 World Cup
                    if "world cup" in league_name.lower() and "t20" in league_name.lower():
                        t20_wc_found = True
                        print(f"    🎯 *** T20 WORLD CUP FOUND! ***")
                    print()
                
                if t20_wc_found:
                    print("\n🎉 SUCCESS! You have T20 World Cup access!")
                else:
                    print("\n⚠️  T20 World Cup NOT found in your league list")
                    print("    You might need to upgrade to a paid plan")
                    
            else:
                print("⚠️  No leagues data found in response")
                print(f"Response: {data}")
                
        elif response.status_code == 401:
            print("❌ Authentication Failed - API token might be invalid")
        elif response.status_code == 403:
            print("❌ Access Forbidden - You might need to activate your plan")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get current fixtures to see what's available
    print("\n\n📋 TEST 2: Fetching current fixtures...")
    print("-" * 70)
    
    url = f"{BASE_URL}/fixtures"
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Save raw response
            with open("sportmonks_fixtures_response.json", "w") as f:
                json.dump(data, f, indent=2)
            print("✅ Fixtures endpoint works!")
            print(f"📁 Full response saved to: sportmonks_fixtures_response.json")
            
            if "data" in data:
                fixtures = data["data"]
                print(f"\n✅ Found {len(fixtures)} fixture(s)")
                
                if fixtures:
                    print("\nSample fixtures:")
                    for fixture in fixtures[:5]:  # Show first 5
                        print(f"  • {fixture.get('localteam_id', '?')} vs {fixture.get('visitorteam_id', '?')}")
                        print(f"    League: {fixture.get('league_id', 'N/A')}")
                        print(f"    Date: {fixture.get('starting_at', 'N/A')}")
                        print()
            else:
                print("⚠️  No fixtures data found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Test Complete!")
    print("\nNext steps:")
    print("1. Check the JSON files to see full response structure")
    print("2. If T20 World Cup is available, we can proceed")
    print("3. If not, you'll need to upgrade your plan")


if __name__ == "__main__":
    test_api_connection()
