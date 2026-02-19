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
    
    # Add realistic user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Execute CDP commands to mask automation
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def scrape_match_with_selenium(driver, match_url):
    """
    Scrape match data using Selenium
    
    Args:
        driver: Selenium WebDriver instance
        match_url (str): URL to the match scorecard
    
    Returns:
        dict: Match data
    """
    print(f"\n📥 Scraping: {match_url}")
    
    try:
        # Load the page
        driver.get(match_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Wait for scorecard to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        # Get page source after JavaScript execution
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        match_data = {
            "url": match_url,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Extract match title
        title = soup.find('h1')
        if title:
            match_data["title"] = title.text.strip()
            print(f"   ✅ Match: {match_data['title']}")
        
        # Extract result
        result_elements = soup.find_all('div', class_='ds-text-tight-m')
        for elem in result_elements:
            text = elem.text.strip()
            if 'won by' in text.lower() or 'tied' in text.lower():
                match_data["result"] = text
                print(f"   ✅ Result: {text}")
                break
        
        # Extract venue
        venue_elements = soup.find_all('a')
        for elem in venue_elements:
            href = elem.get('href', '')
            if '/cricket-grounds/' in href:
                match_data["venue"] = elem.text.strip()
                print(f"   ✅ Venue: {match_data['venue']}")
                break
        
        # Extract Man of the Match
        mom_text = soup.find(string=lambda text: text and 'Player Of The Match' in text)
        if mom_text:
            mom_parent = mom_text.find_parent()
            if mom_parent:
                mom_link = mom_parent.find_next('a')
                if mom_link:
                    match_data["man_of_match"] = mom_link.text.strip()
                    print(f"   ✅ Man of Match: {match_data['man_of_match']}")
        
        # Extract innings data
        match_data["innings"] = []
        tables = soup.find_all('table', class_='ds-w-full')
        
        for idx, table in enumerate(tables[:2]):
            innings = {
                "innings_number": idx + 1,
                "batting": []
            }
            
            # Get team name and score from preceding text
            prev_div = table.find_previous('div', class_='ds-text-tight-m')
            if prev_div:
                innings["team_score"] = prev_div.text.strip()
                print(f"   ✅ Innings {idx+1}: {innings['team_score']}")
            
            # Extract batting data
            tbody = table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 7:
                        player_name = cells[0].text.strip()
                        
                        # Skip non-player rows
                        if any(skip in player_name for skip in ['Extras', 'Total', 'Did not bat', 'Fall of wickets']):
                            continue
                        
                        try:
                            runs = cells[2].text.strip()
                            balls = cells[3].text.strip()
                            
                            if runs.isdigit() and balls.isdigit():
                                innings["batting"].append({
                                    "name": player_name,
                                    "runs": runs,
                                    "balls": balls
                                })
                        except:
                            continue
            
            if innings["batting"]:
                print(f"      📊 Batsmen scraped: {len(innings['batting'])}")
            
            match_data["innings"].append(innings)
        
        print(f"   ✅ Successfully scraped match data")
        return match_data
        
    except Exception as e:
        print(f"   ❌ Error scraping match: {e}")
        return None


def main():
    """Main function"""
    print("="*70)
    print("🏏 ESPNcricinfo Scraper (Selenium)")
    print("="*70)
    
    # Get target date
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = "2026-02-18"
    
    print(f"Target date: {target_date}")
    
    # Match URLs for Feb 18
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
        print(f"❌ No match URLs for date: {target_date}")
        return
    
    print(f"\n🎯 Found {len(urls_to_scrape)} match(es) for {target_date}")
    
    # Setup Selenium driver
    print("\n🌐 Setting up Chrome browser...")
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
            
            # Brief pause between matches
            if idx < len(urls_to_scrape):
                time.sleep(2)
        
        if all_matches:
            # Save to JSON
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
            
            for idx, match in enumerate(all_matches, 1):
                print(f"\n--- Match {idx} ---")
                print(f"Title: {match.get('title', 'N/A')}")
                print(f"Result: {match.get('result', 'N/A')}")
                print(f"Venue: {match.get('venue', 'N/A')}")
                print(f"Man of Match: {match.get('man_of_match', 'N/A')}")
                
                for innings in match.get('innings', []):
                    print(f"  {innings.get('team_score', 'N/A')}")
                    if innings['batting']:
                        print(f"    Top 3:")
                        for batsman in innings['batting'][:3]:
                            print(f"      - {batsman['name']}: {batsman['runs']}({batsman['balls']})")
            
            print("="*70)
            print("✅ Scraping complete!")
        else:
            print("\n❌ No matches scraped successfully")
    
    finally:
        # Close the browser
        driver.quit()
        print("\n🌐 Browser closed")


if __name__ == "__main__":
    main()
