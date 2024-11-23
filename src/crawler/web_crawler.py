import requests
from bs4 import BeautifulSoup

# Starting off with a simple web crawler
class WebCrawler:
    def __init__(self, seed_urls):
        self.frontier = seed_urls  # URLs to crawl

    def fetch_page(self, url):
        try:
            response = requests.get(url)
            return response.text
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def parse_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return [a['href'] for a in soup.find_all('a', href=True)]
