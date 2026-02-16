import requests
import json
from datetime import datetime

class CricketTest:
    """Test script to fetch a specific match"""
    
    BASE_URL = "https://hs-consumer-api.espncricinfo.com/v1/pages"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
    
    def get_match_details(self, match_id: str):
        """Get detailed match information"""
        url = f"{self.BASE_URL}/match/home"
        params = {
            'lang': 'en',
            'matchId': match_id
        }
        
        print(f"Fetching match {match_id}...")
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Save raw response
            with open(f'test_match_{match_id}.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Raw data saved to test_match_{match_id}.json")
            
            # Check match status
            if 'match' in data:
                match = data['match']
                print(f"\nMatch: {match.get('title', 'N/A')}")
                print(f"Status: {match.get('statusText', 'N/A')}")
                print(f"State: {match.get('state', 'N/A')}")
                print(f"Start Date: {match.get('startDate', 'N/A')}")
                
                if 'innings' in match:
                    print(f"\nInnings found: {len(match['innings'])}")
                    for inning in match['innings']:
                        team = inning.get('team', {}).get('longName', 'N/A')
                        runs = inning.get('runs', 0)
                        wickets = inning.get('wickets', 0)
                        overs = inning.get('overs', 0)
                        print(f"  {team}: {runs}/{wickets} ({overs} overs)")
            
            return data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_series_schedule(self, series_id: str):
        """Get all matches in series to see what's available"""
        url = f"{self.BASE_URL}/series/schedule"
        params = {
            'lang': 'en',
            'seriesId': series_id
        }
        
        print(f"Fetching series schedule...")
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Save raw response
            with open('test_series_schedule.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Series schedule saved to test_series_schedule.json")
            
            # List recent matches
            if 'content' in data and 'matches' in data['content']:
                print(f"\n📅 Recent matches in series:")
                print("=" * 80)
                
                today = datetime.now().date()
                
                for match in data['content']['matches'][:10]:  # Show first 10
                    match_id = match.get('objectId')
                    title = match.get('title', 'N/A')
                    status = match.get('statusText', 'N/A')
                    state = match.get('state', 'N/A')
                    start_time = match.get('startTime', '')
                    
                    # Parse date
                    match_date = "N/A"
                    if start_time:
                        try:
                            match_date = datetime.fromisoformat(start_time.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        except:
                            pass
                    
                    print(f"\nMatch ID: {match_id}")
                    print(f"  {title}")
                    print(f"  Date: {match_date}")
                    print(f"  Status: {status}")
                    print(f"  State: {state}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


def main():
    print("🏏 Cricket Match Test Script")
    print("=" * 80)
    
    tester = CricketTest()
    
    # Test 1: Get series schedule to see all matches
    print("\n📋 TEST 1: Fetching series schedule...")
    print("-" * 80)
    series_id = "1502138"  # T20 World Cup 2025-26
    tester.get_series_schedule(series_id)
    
    # Test 2: Fetch specific match (Afghanistan vs UAE from earlier)
    print("\n\n📋 TEST 2: Fetching specific match...")
    print("-" * 80)
    match_id = "1512746"  # Afghanistan vs UAE
    tester.get_match_details(match_id)
    
    print("\n\n" + "=" * 80)
    print("✅ Test complete!")
    print("\nFiles created:")
    print("  - test_series_schedule.json (all matches in series)")
    print("  - test_match_1512746.json (specific match details)")
    print("\nCheck these files to see what data is available!")


if __name__ == "__main__":
    main()
