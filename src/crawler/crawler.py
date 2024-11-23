from ml.classifier import RelevanceClassifier
from ml.adaptive_model import AdaptiveModel
from crawler.robots import RobotsHandler
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class WebCrawler:
    def __init__(self, seed_urls, max_depth=2, user_agent="MyCrawler"):
        self.frontier = seed_urls  # List of URLs to crawl
        self.visited = set()  # Keep track of visited URLs
        self.classifier = RelevanceClassifier()
        self.adaptive_model = AdaptiveModel()
        self.max_depth = max_depth
        self.user_agent = user_agent
        self.robots_handler = RobotsHandler()

    def fetch_page(self, url):
        """Fetch the HTML content of a page."""
        try:
            response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=10)
            if response.status_code == 200:
                return response.text
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
        return None

    def parse_links(self, html, base_url):
        """Extract all links from a web page."""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(base_url, a_tag['href'])  # Resolve relative URLs
            if link.startswith("http") and link not in self.visited:
                links.add(link)
        return links

    def extract_features(self, url, html):
        """Extract features from the URL and HTML for relevance prediction."""
        return [len(url), html.lower().count('example')]  # Simplified for now

    def is_relevant(self, features):
        """Check if a URL or page is relevant using the classifier."""
        return self.classifier.predict(features)[0] == 1  # Assuming binary output

    def crawl(self, url, depth=0):
        """Crawl a single URL."""
        if depth > self.max_depth or url in self.visited:
            return

        # Parse the domain and check robots.txt
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if not self.robots_handler.can_fetch(base_url, self.user_agent, url):
            print(f"Blocked by robots.txt: {url}")
            return

        print(f"Crawling: {url} (Depth: {depth})")
        self.visited.add(url)

        # Fetch and process the page
        html = self.fetch_page(url)
        if not html:
            return

        # Check relevance and train the adaptive model
        features = self.extract_features(url, html)
        if self.is_relevant(features):
            print(f"Relevant page found: {url}")
            self.adaptive_model.train_on_new_data([features], [1])  # Label as relevant

        # Parse links and crawl them recursively
        links = self.parse_links(html, url)
        for link in links:
            self.crawl(link, depth + 1)

    def start(self):
        """Start the crawling process."""
        for url in self.frontier:
            self.crawl(url)


# Example usage
if __name__ == "__main__":
    seed_urls = ["https://en.wikipedia.org/wiki/Web_crawler"]
    crawler = WebCrawler(seed_urls, max_depth=1)
    crawler.start()
