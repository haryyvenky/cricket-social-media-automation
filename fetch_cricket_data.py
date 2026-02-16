import requests
import json
from datetime import datetime
from typing import Dict, Optional

class ESPNCricinfoScraper:
    """Fetch cricket match data from ESPNcricinfo's unofficial API"""
    
    BASE_URL = "https://hs-consumer-api.espncricinfo.com/v1/pages"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
    
    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get detailed match information and scores"""
        url = f"{self.BASE_URL}/match/home"
        params = {
            'lang': 'en',
            'matchId': match_id
        }
        
        print(f"Fetching data from: {url}")
        print(f"Match ID: {match_id}")
        print("-" * 60)
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Save raw response for inspection
            with open(f'raw_match_{match_id}.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Raw API response saved to: raw_match_{match_id}.json")
            
            return self._parse_match_data(data)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching match details: {e}")
            return None
    
    def _parse_match_data(self, data: Dict) -> Dict:
        """Parse the raw API response into a clean format"""
        
        # The API structure might have the match data nested differently
        # Let's check common paths
        match_info = None
        if 'match' in data:
            match_info = data['match']
        elif 'content' in data and 'match' in data['content']:
            match_info = data['content']['match']
        
        if not match_info:
            print("⚠️ Could not find match data in expected format")
            return {}
        
        # Extract basic match info
        parsed = {
            'match_id': match_info.get('objectId', match_info.get('id')),
            'title': match_info.get('title', ''),
            'subtitle': match_info.get('subTitle', ''),
            'status': match_info.get('statusText', ''),
            'state': match_info.get('state', ''),
            'venue': '',
            'city': '',
            'start_date': match_info.get('startDate', ''),
            'teams': [],
            'innings': [],
            'toss': '',
            'player_of_match': ''
        }
        
        # Extract venue information
        if 'ground' in match_info:
            ground = match_info['ground']
            parsed['venue'] = ground.get('longName', ground.get('name', ''))
            parsed['city'] = ground.get('town', ground.get('city', ''))
        
        # Extract toss information
        if 'tossResults' in match_info:
            toss = match_info['tossResults']
            team_won = toss.get('winningTeam', {}).get('longName', '')
            decision = toss.get('decision', '')
            if team_won and decision:
                parsed['toss'] = f"{team_won} won the toss and chose to {decision}"
        
        # Extract team information
        if 'teams' in match_info:
            for team in match_info['teams']:
                team_data = team.get('team', {})
                parsed['teams'].append({
                    'name': team_data.get('longName', team_data.get('name', '')),
                    'short_name': team_data.get('abbreviation', ''),
                })
        
        # Extract innings/scorecard data
        if 'innings' in match_info:
            for inning in match_info['innings']:
                inning_data = {
                    'team': '',
                    'runs': inning.get('runs', 0),
                    'wickets': inning.get('wickets', 0),
                    'overs': inning.get('overs', 0),
                    'run_rate': inning.get('runRate', 0),
                    'inning_number': inning.get('inningNumber', 0),
                    'batsmen': [],
                    'bowlers': []
                }
                
                # Get team name
                if 'team' in inning:
                    team_info = inning['team']
                    inning_data['team'] = team_info.get('longName', team_info.get('name', ''))
                
                # Get batting performances
                if 'batsmen' in inning:
                    for batsman in inning['batsmen']:
                        player = batsman.get('player', {})
                        inning_data['batsmen'].append({
                            'name': player.get('longName', player.get('name', '')),
                            'runs': batsman.get('runs', 0),
                            'balls': batsman.get('balls', 0),
                            'fours': batsman.get('fours', 0),
                            'sixes': batsman.get('sixes', 0),
                            'strike_rate': batsman.get('strikeRate', 0),
                            'dismissal': batsman.get('dismissalText', 'not out')
                        })
                
                # Get bowling performances
                if 'bowlers' in inning:
                    for bowler in inning['bowlers']:
                        player = bowler.get('player', {})
                        inning_data['bowlers'].append({
                            'name': player.get('longName', player.get('name', '')),
                            'overs': bowler.get('overs', 0),
                            'maidens': bowler.get('maidens', 0),
                            'runs': bowler.get('conceded', bowler.get('runs', 0)),
                            'wickets': bowler.get('wickets', 0),
                            'economy': bowler.get('economy', bowler.get('economyRate', 0))
                        })
                
                parsed['innings'].append(inning_data)
        
        # Extract player of the match
        if 'awards' in match_info:
            for award in match_info['awards']:
                if award.get('awardType') == 'player of the match':
                    player = award.get('player', {})
                    parsed['player_of_match'] = player.get('longName', player.get('name', ''))
        
        return parsed
    
    def display_match_summary(self, match_data: Dict):
        """Display a formatted match summary"""
        print("\n" + "=" * 70)
        print(f"  {match_data['title']}")
        print("=" * 70)
        
        if match_data.get('subtitle'):
            print(f"{match_data['subtitle']}")
        
        print(f"\n📍 Venue: {match_data['venue']}, {match_data['city']}")
        print(f"📅 Date: {match_data['start_date']}")
        
        if match_data.get('toss'):
            print(f"🪙 Toss: {match_data['toss']}")
        
        print(f"\n🏆 Result: {match_data['status']}")
        
        print("\n" + "-" * 70)
        print("SCORECARD")
        print("-" * 70)
        
        for inning in match_data['innings']:
            print(f"\n{inning['team']}: {inning['runs']}/{inning['wickets']} ({inning['overs']} overs)")
            print(f"Run Rate: {inning['run_rate']}")
            
            if inning['batsmen']:
                print("\n  Top Batsmen:")
                for i, batsman in enumerate(inning['batsmen'][:5], 1):
                    dismissal = f" ({batsman['dismissal']})" if batsman['dismissal'] != 'not out' else ' *'
                    print(f"    {i}. {batsman['name']}: {batsman['runs']}({batsman['balls']}) - "
                          f"{batsman['fours']}x4, {batsman['sixes']}x6, SR: {batsman['strike_rate']:.1f}{dismissal}")
            
            if inning['bowlers']:
                print("\n  Best Bowlers:")
                # Sort by wickets and economy
                sorted_bowlers = sorted(inning['bowlers'], 
                                       key=lambda x: (-x['wickets'], x['economy']))
                for i, bowler in enumerate(sorted_bowlers[:3], 1):
                    print(f"    {i}. {bowler['name']}: {bowler['wickets']}/{bowler['runs']} "
                          f"({bowler['overs']} overs, Econ: {bowler['economy']:.2f})")
        
        if match_data.get('player_of_match'):
            print(f"\n⭐ Player of the Match: {match_data['player_of_match']}")
        
        print("\n" + "=" * 70)


def main():
    # Your match details
    match_id = "1512746"
    series_id = "1502138"
    
    print("🏏 ESPNcricinfo Match Data Fetcher")
    print("=" * 70)
    print(f"Series: ICC Men's T20 World Cup 2025-26")
    print(f"Match: Afghanistan vs United Arab Emirates")
    print("=" * 70 + "\n")
    
    scraper = ESPNCricinfoScraper()
    
    # Fetch match details
    match_data = scraper.get_match_details(match_id)
    
    if match_data:
        # Save parsed data
        output_file = f'match_{match_id}_parsed.json'
        with open(output_file, 'w') as f:
            json.dump(match_data, f, indent=2)
        print(f"✓ Parsed match data saved to: {output_file}\n")
        
        # Display formatted summary
        scraper.display_match_summary(match_data)
        
        print(f"\n\n📁 Files created:")
        print(f"   1. raw_match_{match_id}.json - Raw API response")
        print(f"   2. {output_file} - Parsed and structured data")
        print(f"\nYou can use the parsed JSON file for:")
        print(f"   ✓ Generating editorial content with LLM")
        print(f"   ✓ Creating scorecard graphics")
        print(f"   ✓ Posting to social media")
    else:
        print("❌ Failed to fetch match data")


if __name__ == "__main__":
    main()
