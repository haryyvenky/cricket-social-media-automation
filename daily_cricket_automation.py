import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class CricketAutomation:
    """Automated cricket data fetcher for daily posts"""
    
    BASE_URL = "https://hs-consumer-api.espncricinfo.com/v1/pages"
    
    def __init__(self, series_id: str):
        self.series_id = series_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
    
    def get_series_matches(self) -> List[Dict]:
        """Get all matches in the series"""
        url = f"{self.BASE_URL}/series/schedule"
        params = {
            'lang': 'en',
            'seriesId': self.series_id
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            matches = []
            if 'content' in data and 'matches' in data['content']:
                for match in data['content']['matches']:
                    matches.append({
                        'match_id': match.get('objectId'),
                        'title': match.get('title'),
                        'status': match.get('statusText'),
                        'start_time': match.get('startTime'),
                        'state': match.get('state'),
                    })
            
            return matches
            
        except Exception as e:
            print(f"Error fetching series matches: {e}")
            return []
    
    def get_todays_completed_matches(self) -> List[str]:
        """Get match IDs for today's completed matches"""
        all_matches = self.get_series_matches()
        today = datetime.now().date()
        
        completed_match_ids = []
        
        print(f"📅 Looking for matches on: {today}")
        print("-" * 60)
        
        for match in all_matches:
            if not match.get('start_time'):
                continue
            
            # Parse the match date
            try:
                match_date = datetime.fromisoformat(
                    match['start_time'].replace('Z', '+00:00')
                ).date()
            except:
                continue
            
            # Check if match is from today or yesterday (for late-finishing matches)
            is_recent = match_date == today or match_date == (today - timedelta(days=1))
            
            # Check if match is completed
            is_completed = (
                match.get('state') == 'complete' or 
                'won' in match.get('status', '').lower() or
                'abandoned' in match.get('status', '').lower()
            )
            
            if is_recent and is_completed:
                print(f"✓ Found: {match['title']}")
                print(f"  Status: {match['status']}")
                print(f"  Match ID: {match['match_id']}")
                completed_match_ids.append(match['match_id'])
        
        return completed_match_ids
    
    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get detailed match information and scores"""
        url = f"{self.BASE_URL}/match/home"
        params = {
            'lang': 'en',
            'matchId': match_id
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_match_data(data, match_id)
            
        except Exception as e:
            print(f"Error fetching match {match_id}: {e}")
            return None
    
    def _parse_match_data(self, data: Dict, match_id: str) -> Dict:
        """Parse the raw API response into a clean format"""
        
        match_info = None
        if 'match' in data:
            match_info = data['match']
        elif 'content' in data and 'match' in data['content']:
            match_info = data['content']['match']
        
        if not match_info:
            return {}
        
        # Extract basic match info
        parsed = {
            'match_id': match_id,
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
            'player_of_match': '',
            'match_number': match_info.get('matchNumber', ''),
            'series': match_info.get('series', {}).get('longName', '')
        }
        
        # Extract venue
        if 'ground' in match_info:
            ground = match_info['ground']
            parsed['venue'] = ground.get('longName', ground.get('name', ''))
            parsed['city'] = ground.get('town', ground.get('city', ''))
        
        # Extract toss
        if 'tossResults' in match_info:
            toss = match_info['tossResults']
            team_won = toss.get('winningTeam', {}).get('longName', '')
            decision = toss.get('decision', '')
            if team_won and decision:
                parsed['toss'] = f"{team_won} won the toss and chose to {decision}"
        
        # Extract teams
        if 'teams' in match_info:
            for team in match_info['teams']:
                team_data = team.get('team', {})
                parsed['teams'].append({
                    'name': team_data.get('longName', team_data.get('name', '')),
                    'short_name': team_data.get('abbreviation', ''),
                })
        
        # Extract innings
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
                
                if 'team' in inning:
                    team_info = inning['team']
                    inning_data['team'] = team_info.get('longName', team_info.get('name', ''))
                
                # Batting
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
                
                # Bowling
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
        
        # Player of the match
        if 'awards' in match_info:
            for award in match_info['awards']:
                if award.get('awardType') == 'player of the match':
                    player = award.get('player', {})
                    parsed['player_of_match'] = player.get('longName', player.get('name', ''))
        
        return parsed
    
    def fetch_todays_matches(self) -> List[Dict]:
        """Main function: fetch all of today's completed matches"""
        print("🏏 Cricket Automation - Daily Match Fetcher")
        print("=" * 70)
        
        # Get today's match IDs
        match_ids = self.get_todays_completed_matches()
        
        if not match_ids:
            print("\n⚠️ No completed matches found for today")
            return []
        
        print(f"\n✓ Found {len(match_ids)} completed match(es)")
        print("=" * 70)
        
        # Fetch details for each match
        all_matches = []
        for match_id in match_ids:
            print(f"\nFetching details for match {match_id}...")
            match_data = self.get_match_details(match_id)
            
            if match_data:
                all_matches.append(match_data)
                
                # Save individual match file
                filename = f"match_{match_id}_{datetime.now().strftime('%Y%m%d')}.json"
                with open(filename, 'w') as f:
                    json.dump(match_data, f, indent=2)
                print(f"✓ Saved to {filename}")
        
        # Save combined daily summary
        if all_matches:
            summary_file = f"daily_matches_{datetime.now().strftime('%Y%m%d')}.json"
            summary = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_matches': len(all_matches),
                'matches': all_matches
            }
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"\n✓ Daily summary saved to {summary_file}")
        
        return all_matches


def main():
    # T20 World Cup 2025-26 Series ID
    series_id = "1502138"
    
    automation = CricketAutomation(series_id)
    matches = automation.fetch_todays_matches()
    
    if matches:
        print("\n" + "=" * 70)
        print("📊 TODAY'S MATCHES SUMMARY")
        print("=" * 70)
        
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match['title']}")
            print(f"   {match['status']}")
            for inning in match['innings']:
                print(f"   {inning['team']}: {inning['runs']}/{inning['wickets']} ({inning['overs']} overs)")
        
        print("\n" + "=" * 70)
        print("✅ Ready for next steps:")
        print("   1. Generate editorial content (using LLM)")
        print("   2. Create scorecard images")
        print("   3. Post to LinkedIn and X")
        print("=" * 70)
    else:
        print("\n❌ No matches to process today")


if __name__ == "__main__":
    main()
