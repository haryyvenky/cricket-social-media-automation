from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import sys
import re

def setup_driver():
    """Setup headless Chrome driver for scraping"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def extract_team_from_title(title):
    """Extract team names from match title"""
    # Example: "India vs Netherlands, 36th Match, Group A at Ahmedabad"
    match = re.search(r'(.+?)\s+vs\s+(.+?),', title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def extract_scores_from_page(soup):
    """
    Extract team scores from the scorecard page
    This looks for the team name + score displays at the top
    """
    scores = []
    
    # Method 1: Look for score displays with specific patterns
    # ESPNcricinfo typically shows: "India 193/6" and "Netherlands 176/7"
    all_text = soup.get_text()
    
    # Find patterns like "TeamName XXX/X" or "TeamName XXX"
    score_pattern = r'([A-Z][a-zA-Z\s\.]+?)\s+(\d{2,3}(?:/\d{1,2})?)'
    matches = re.findall(score_pattern, all_text[:5000])  # Search in first part of page
    
    # Filter to get likely team scores (scores between 50-400)
    for team, score in matches:
        team = team.strip()
        # Skip if it's just numbers or very short
        if len(team) < 3 or team.isdigit():
            continue
        # Check if score looks valid
        if '/' in score:
            runs = int(score.split('/')[0])
        else:
            runs = int(score)
        
        if 50 <= runs <= 400 and team not in [s[0] for s in scores]:
            scores.append((team, score))
            if len(scores) == 2:
                break
    
    return scores


def scrape_match_with_selenium(driver, match_url):
    """
    Scrape match data using Selenium with improved parsing
    """
    print(f"\n📥 Scraping: {match_url}")
    
    try:
        driver.get(match_url)
        time.sleep(4)  # Wait for page to fully load
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        match_data = {
            "url": match_url,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Extract title
        title_elem = soup.find('h1')
        if title_elem:
            match_data["title"] = title_elem.text.strip()
            print(f"   Match: {match_data['title']}")
        
        # Extract team names from title
        team1, team2 = extract_team_from_title(match_data.get("title", ""))
        
        # Extract result - look for clean result text
        # Result is usually in a prominent div near the top
        result_text = None
        for elem in soup.find_all(['div', 'p', 'span']):
            text = elem.get_text(strip=True)
            # Look for clean "X won by Y" pattern
            if re.match(r'^[A-Z][a-zA-Z\s\.]+ won by \d+', text):
                result_text = text
                break
        
        if result_text:
            match_data["result"] = result_text
            print(f"   ✅ Result: {result_text}")
        else:
            print(f"   ⚠️  Result not found clearly")
        
        # Extract venue
        venue_found = False
        for link in soup.find_all('a', href=True):
            if '/cricket-grounds/' in link['href']:
                match_data["venue"] = link.text.strip()
                print(f"   ✅ Venue: {match_data['venue']}")
                venue_found = True
                break
        
        # Extract Man of the Match
        page_text = soup.get_text()
        mom_match = re.search(r'Player Of The Match.*?([A-Z][a-zA-Z\s]+)', page_text, re.DOTALL)
        if mom_match:
            # Clean up the name
            mom_name = mom_match.group(1).strip()
            # Take only the first reasonable name (stop at numbers or special chars)
            mom_name = re.split(r'\d|Innings|Match|Score', mom_name)[0].strip()
            if len(mom_name) < 50:  # Sanity check
                match_data["man_of_match"] = mom_name
                print(f"   ✅ Man of Match: {mom_name}")
        
        # Extract team scores from page
        team_scores = extract_scores_from_page(soup)
        if team_scores:
            print(f"   ✅ Scores found: {team_scores}")
        
        # Extract innings data
        match_data["innings"] = []
        
        # Find all tables (batting and bowling alternate)
        all_tables = soup.find_all('table', class_='ci-scorecard-table')
        if not all_tables:
            all_tables = soup.find_all('table')
        
        print(f"   Found {len(all_tables)} tables")
        
        # Process innings (typically 4 tables: bat1, bowl1, bat2, bowl2)
        innings_count = 0
        
        for table_idx in range(0, len(all_tables), 2):  # Step by 2 (batting, bowling pairs)
            if innings_count >= 2:
                break
            
            innings = {
                "innings_number": innings_count + 1,
                "batting": [],
                "bowling": []
            }
            
            # Assign team score if available
            if innings_count < len(team_scores):
                team_name, score = team_scores[innings_count]
                innings["team_name"] = team_name
                innings["team_score"] = score
                print(f"   Innings {innings_count + 1}: {team_name} {score}")
            
            # Process batting table
            if table_idx < len(all_tables):
                batting_table = all_tables[table_idx]
                tbody = batting_table.find('tbody')
                
                if tbody:
                    for row in tbody.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            # First cell is player name
                            player_cell = cells[0]
                            player_name = player_cell.get_text(strip=True)
                            
                            # Skip non-player rows
                            if any(skip in player_name.lower() for skip in 
                                   ['extra', 'total', 'did not bat', 'fall of wicket', 'yet to bat']):
                                continue
                            
                            # Clean player name (remove symbols like †, (c), etc.)
                            player_name = re.sub(r'[†\(\)c]', '', player_name).strip()
                            
                            try:
                                # Runs and balls are typically in cells 2 and 3
                                runs = cells[2].get_text(strip=True) if len(cells) > 2 else "0"
                                balls = cells[3].get_text(strip=True) if len(cells) > 3 else "0"
                                
                                # Validate numeric
                                if runs.isdigit() and balls.isdigit():
                                    innings["batting"].append({
                                        "name": player_name,
                                        "runs": runs,
                                        "balls": balls
                                    })
                            except:
                                continue
            
            # Process bowling table (next table after batting)
            if table_idx + 1 < len(all_tables):
                bowling_table = all_tables[table_idx + 1]
                tbody = bowling_table.find('tbody')
                
                if tbody:
                    for row in tbody.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) >= 5:
                            bowler_name = cells[0].get_text(strip=True)
                            
                            # Skip non-bowler rows
                            if any(skip in bowler_name.lower() for skip in 
                                   ['bowler', 'total', 'extra']):
                                continue
                            
                            # Clean bowler name
                            bowler_name = re.sub(r'[†\(\)c]', '', bowler_name).strip()
                            
                            try:
                                # Wickets column (usually 4th or 5th column)
                                wickets = cells[4].get_text(strip=True) if len(cells) > 4 else "0"
                                
                                if wickets.isdigit() and int(wickets) > 0:
                                    innings["bowling"].append({
                                        "name": bowler_name,
                                        "wickets": wickets
                                    })
                            except:
                                continue
            
            if innings["batting"]:
                print(f"      📊 Batsmen: {len(innings['batting'])}")
            if innings["bowling"]:
                print(f"      🎯 Bowlers: {len(innings['bowling'])}")
            
            match_data["innings"].append(innings)
            innings_count += 1
        
        print(f"   ✅ Match data scraped")
        return match_data
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    print("="*70)
    print("🏏 ESPNcricinfo Scraper v2 (Improved)")
    print("="*70)
    
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = "2026-02-18"
    
    print(f"Target date: {target_date}")
    
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
    
    urls_to_scrape = match_urls.get(target_date, [])
    
    if not urls_to_scrape:
        print(f"❌ No URLs for date: {target_date}")
        return
    
    print(f"\n🎯 Found {len(urls_to_scrape)} match(es)")
    print("\n🌐 Starting browser...")
    
    driver = setup_driver()
    
    try:
        all_matches = []
        
        for idx, url in enumerate(urls_to_scrape, 1):
            print(f"\n{'='*70}")
            print(f"Match {idx}/{len(urls_to_scrape)}")
            print(f"{'='*70}")
            
            match_data = scrape_match_with_selenium(driver, url)
            
            if match_data:
                all_matches.append(match_data)
            
            if idx < len(urls_to_scrape):
                time.sleep(3)
        
        if all_matches:
            output_file = f"matches_{target_date.replace('-', '')}.json"
            output_data = {
                "date": target_date,
                "total_matches": len(all_matches),
                "matches": all_matches
            }
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\n💾 Saved to: {output_file}")
            
            print("\n" + "="*70)
            print("📊 SUMMARY")
            print("="*70)
            
            for idx, match in enumerate(all_matches, 1):
                print(f"\n--- Match {idx} ---")
                print(f"Title: {match.get('title', 'N/A')}")
                print(f"Result: {match.get('result', 'N/A')}")
                print(f"Venue: {match.get('venue', 'N/A')}")
                print(f"Man of Match: {match.get('man_of_match', 'N/A')}")
                
                for innings in match.get('innings', []):
                    team = innings.get('team_name', f"Innings {innings['innings_number']}")
                    score = innings.get('team_score', 'N/A')
                    print(f"\n  {team}: {score}")
                    
                    if innings['batting']:
                        print(f"    Top batsmen:")
                        for bat in innings['batting'][:3]:
                            print(f"      {bat['name']}: {bat['runs']}({bat['balls']})")
                    
                    if innings.get('bowling'):
                        print(f"    Top bowlers:")
                        sorted_bowl = sorted(innings['bowling'], 
                                           key=lambda x: int(x['wickets']), 
                                           reverse=True)
                        for bowl in sorted_bowl[:2]:
                            print(f"      {bowl['name']}: {bowl['wickets']} wickets")
            
            print("\n" + "="*70)
            print("✅ Complete!")
        else:
            print("\n❌ No matches scraped")
    
    finally:
        driver.quit()
        print("\n🌐 Browser closed")


if __name__ == "__main__":
    main()
