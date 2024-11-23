from ml.classifier import RelevanceClassifier
from ml.adaptive_model import AdaptiveModel
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class WebCrawler:
    def __init__(self, seed_urls, max_depth=2):
        self.frontier = seed_urls  # List of URLs to crawl
        self.visited = set()  # Keep track of visited URLs
        self.classifier = RelevanceClassifier()
        self.adaptive_model = AdaptiveModel()
        self.max_depth = max_depth

    def fetch_page(self, url):
        """Fetch the HTML content of a page."""
        try:
            response = requests.get(url, timeout=10)
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

    def is_relevant(self, features):
        """Check if a URL or page is relevant using the classifier."""
        return self.classifier.predict(features)[0] == 1  # Assuming binary output

    def extract_features(self, url, html):
        """Extract features from the URL and HTML for relevance prediction."""
        # Example: Feature engineering based on URL length, keyword count, etc.
        return [len(url), html.lower().count('example')]  # Simplify for now

    def crawl(self, url, depth=0):
        """Crawl a single URL."""
        if depth > self.max_depth or url in self.visited:
            return
        print(f"Crawling: {url} (Depth: {depth})")
        self.visited.add(url)

        # Fetch the page content
        html = self.fetch_page(url)
        if not html:
            return

        # Extract features and check relevance
        features = self.extract_features(url, html)
        if self.is_relevant(features):
            print(f"Relevant page found: {url}")
            # Train the adaptive model with new data
            self.adaptive_model.train_on_new_data([features], [1])  # Label as relevant

        # Parse and prioritize links
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
