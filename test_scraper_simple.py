import requests
from bs4 import BeautifulSoup

class SimpleScraper:
    def __init__(self, url):
        self.url = url

    def fetch_data(self):
        response = requests.get(self.url)
        return response.text

    def parse_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        match_info = {}  

        # Extract scores
        match_info['scores'] = soup.find('div', class_='score').text.strip()

        # Extract wickets
        match_info['wickets'] = soup.find('div', class_='wickets').text.strip()

        # Extract winner
        match_info['winner'] = soup.find('div', class_='winner').text.strip()

        # Extract margin
        match_info['margin'] = soup.find('div', class_='margin').text.strip()

        # Extract key performances
        match_info['key_performances'] = {
            'batting': soup.find('div', class_='key-batting').text.strip(),
            'bowling': soup.find('div', class_='key-bowling').text.strip()
        }

        # Extract turning point
        match_info['turning_point'] = soup.find('div', class_='turning-point').text.strip()

        # Extract Man of the Match
        match_info['man_of_the_match'] = soup.find('div', class_='man-of-the-match').text.strip()

        return match_info

    def run(self):
        html = self.fetch_data()
        return self.parse_data(html)

# Usage
if __name__ == '__main__':
    url = 'URL_OF_THE_MATCH_PAGE'
    scraper = SimpleScraper(url)
    match_summary = scraper.run()
    print(match_summary)
