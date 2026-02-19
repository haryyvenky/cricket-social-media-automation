import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import sys

# T20 World Cup 2026 Series ID
T20_WC_SERIES_ID = "1502138"
T20_WC_SERIES_NAME = "icc-men-s-t20-world-cup-2025-26"

def get_t20wc_matches_on_date(target_date):
    """
    Find T20 World Cup matches on a specific date from ESPNcricinfo
    
    Args:
        target_date (str): Date in format "YYYY-MM-DD" or "Feb 15 2026"
    
    Returns:
        list: List of match URLs
    """
    print(f"🔍 Searching for T20 World Cup matches on {target_date}")
    
    # ESPNcricinfo T20 World Cup results page
    url = f"https://www.espncricinfo.com/series/{T20_WC_SERIES_NAME}-{T20_WC_SERIES_ID}/match-results"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all match links that contain the target date
        match_links = []
        
        # ESPNcricinfo uses format like "Feb 15 2026" in match URLs
        # Convert our target_date to this format
        if "-" in target_date:
            dt = datetime.strptime(target_date, "%Y-%m-%d")
            date_str = dt.strftime("%b %d %Y")  # "Feb 15 2026"
        else:
            date_str = target_date
        
        # Find all scorecard links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/full-scorecard' in href and T20_WC_SERIES_NAME in href:
                # Check if this match is on our target date
                # We'll verify date after fetching the scorecard
                match_links.append(href)
        
        print(f"✅ Found {len(match_links)} potential T20 World Cup match(es)")
        return match_links
        
    except Exception as e:
        print(f"❌ Error fetching matches: {e}")
        return []


def scrape_match_scorecard(match_url):
    """
    Scrape detailed match data from ESPNcricinfo scorecard page
    
    Args:
        match_url (str): Full URL or path to scorecard page
    
    Returns:
        dict: Match data including scores, performances, etc.
    """
    # Ensure we have full URL
    if not match_url.startswith('http'):
        match_url = f"https://www.espncricinfo.com{match_url}"
    
    print(f"\n📥 Scraping: {match_url}")
    
    try:
        response = requests.get(match_url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        match_data = {
            "url": match_url,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Extract match title and result
        title = soup.find('h1')
        if title:
            match_data["title"] = title.text.strip()
            print(f"   Match: {match_data['title']}")
        
        # Extract result text (e.g., "India won by 61 runs")
        result_div = soup.find('div', class_='ds-text-tight-m')
        if result_div:
            match_data["result"] = result_div.text.strip()
            print(f"   Result: {match_data['result']}")
        
        # Extract venue and date from match details
        details_section = soup.find('div', string=re.compile('Ground'))
        if details_section:
            venue_link = details_section.find_next('a')
            if venue_link:
                match_data["venue"] = venue_link.text.strip()
                print(f"   Venue: {match_data['venue']}")
        
        # Extract match date
        date_section = soup.find('span', class_='ds-text-tight-s')
        if date_section:
            date_text = date_section.text.strip()
            match_data["date"] = date_text
            print(f"   Date: {date_text}")
        
        # Extract team names and scores from the scorecard tables
        match_data["innings"] = []
        
        # Find all innings tables
        innings_tables = soup.find_all('table', class_='ds-w-full')
        
        for idx, table in enumerate(innings_tables[:2]):  # Usually 2 innings in T20
            innings = {
                "innings_number": idx + 1,
                "batting": [],
                "bowling": []
            }
            
            # Get team name and score from table caption or header
            caption = table.find_previous('div', class_='ds-text-tight-m')
            if caption:
                innings["team_score"] = caption.text.strip()
                print(f"   Innings {idx+1}: {innings['team_score']}")
            
            # Extract batting performances
            tbody = table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 7:  # Batsman row has multiple columns
                        player_cell = cells[0]
                        player_name = player_cell.text.strip()
                        
                        # Skip "Extras" and "Total" rows
                        if 'Extras' in player_name or 'Total' in player_name or 'Did not bat' in player_name or 'Fall of wickets' in player_name:
                            continue
                        
                        try:
                            runs = cells[2].text.strip()
                            balls = cells[3].text.strip()
                            
                            batting_entry = {
                                "name": player_name,
                                "runs": runs,
                                "balls": balls
                            }
                            
                            # Only add if we have valid runs/balls data
                            if runs.isdigit() and balls.isdigit():
                                innings["batting"].append(batting_entry)
                        except:
                            continue
            
            match_data["innings"].append(innings)
        
        # Try to extract Man of the Match
        mom_section = soup.find(string=re.compile('Player Of The Match'))
        if mom_section:
            mom_div = mom_section.find_parent('div')
            if mom_div:
                mom_link = mom_div.find_next('a')
                if mom_link:
                    match_data["man_of_match"] = mom_link.text.strip()
                    print(f"   Man of Match: {match_data['man_of_match']}")
        
        print(f"✅ Successfully scraped match data")
        return match_data
        
    except Exception as e:
        print(f"❌ Error scraping match: {e}")
        return None


def main():
    """Main function to scrape T20 World Cup matches"""
    
    print("="*70)
    print("🏏 ESPNcricinfo T20 World Cup Match Scraper")
    print("="*70)
    
    # Get target date from command line or use default
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        # Default to India vs Pakistan match date for testing
        target_date = "2026-02-15"
    
    print(f"Target date: {target_date}")
    
    # Feb 18, 2026 - 3 T20 World Cup matches
    match_urls = {
        "2026-02-18": [
            "https://www.espncricinfo.com/series/icc-men-s-t20-world-cup-2025-26-1502138/south-africa-vs-united-arab-emirates-34th-match-group-d-1512752/full-scorecard",
            "https://www.espncricinfo.com/series/icc-men-s-t20-world-cup-2025-26-1502138/namibia-vs-pakistan-35th-match-group-a-1512753/full-scorecard",
            "https://www.espncricinfo.com/series/icc-men-s-t20-world-cup-2025-26-1502138/india-vs-netherlands-36th-match-group-a-1512754/full-scorecard"
        ],
        "2026-02-15": [
            "https://www.espncricinfo.com/series/icc-men-s-t20-world-cup-2025-26-1502138/india-vs-pakistan-27th-match-group-a-1512745/full-scorecard"
        ]
    }
    
    # Get matches for the target date
    urls_to_scrape = match_urls.get(target_date, [])
    
    if not urls_to_scrape:
        print(f"❌ No match URLs configured for date: {target_date}")
        print(f"Available dates: {list(match_urls.keys())}")
        return
    
    print(f"\n🎯 Found {len(urls_to_scrape)} match(es) for {target_date}")
    
    all_matches = []
    for idx, url in enumerate(urls_to_scrape, 1):
        print(f"\n{'='*70}")
        print(f"Match {idx}/{len(urls_to_scrape)}")
        print(f"{'='*70}")
        match_data = scrape_match_scorecard(url)
        
        if match_data:
            all_matches.append(match_data)
    
    if all_matches:
        # Save all matches to a single JSON file
        output_file = f"matches_{target_date.replace('-', '')}.json"
        output_data = {
            "date": target_date,
            "total_matches": len(all_matches),
            "matches": all_matches
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n💾 All match data saved to: {output_file}")
        
        # Display summary
        print("\n" + "="*70)
        print("📊 SCRAPED DATA SUMMARY")
        print("="*70)
        print(f"Date: {target_date}")
        print(f"Total Matches: {len(all_matches)}")
        
        for idx, match_data in enumerate(all_matches, 1):
            print(f"\n--- Match {idx} ---")
            print(f"Title: {match_data.get('title', 'N/A')}")
            print(f"Result: {match_data.get('result', 'N/A')}")
            print(f"Venue: {match_data.get('venue', 'N/A')}")
            print(f"Man of Match: {match_data.get('man_of_match', 'N/A')}")
            
            for innings in match_data.get('innings', []):
                print(f"  Innings {innings['innings_number']}: {innings.get('team_score', 'N/A')}")
                if innings['batting']:
                    print(f"    Top 3 batsmen:")
                    for batsman in innings['batting'][:3]:
                        print(f"      - {batsman['name']}: {batsman['runs']}({batsman['balls']})")
        
        print("="*70)
        print("✅ Scraping complete!")
    else:
        print("\n❌ No match data scraped successfully")


if __name__ == "__main__":
    main()
