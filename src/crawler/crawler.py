from models.similarities import calculate_similarities, clean_words
import requests
from bs4 import BeautifulSoup
from models.topVals import TopValues
from urllib.parse import urljoin, urlparse
from multiprocessing import Pool
# from crawler.robots import RobotsHandler

class WebCrawler:
    def __init__(self, seed_urls, word, max_depth=2, max_horizon=100, user_agent="MyCrawler"):
        self.target_word = word
        self.max_horizon = max_horizon
        self.frontier = seed_urls  # List of URLs to crawl
        self.visited = set()  # Keep track of visited URLs
        self.max_depth = max_depth
        self.user_agent = user_agent
        # self.robots_handler = RobotsHandler()

    def fetch_page(self, url) -> None:
        """Fetch the HTML content of a page."""
        try:
            response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=10)
            if response.status_code == 200:
                return response.text
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
        return None

    def parse_links(self, html, base_url, context_range=100):
        """Extract all links from a web page."""
        soup = BeautifulSoup(html, 'html.parser')

        links = []
        for link in soup.find_all('a', href=True):
            url = urljoin(base_url, link['href'])  # Resolve relative URLs
            # Get the text content of the <a> tag
            link_text = link.get_text(strip=True)


            # Get the surrounding text
            preceding_text = link.find_previous(string=True)
            following_text = link.find_next(string=True).find_next(string=True)

            # Merge the context and split into words
            context = (
                (preceding_text or "").strip() + " " + link_text + " " + (following_text or "").strip()
            )
            context_words = context.split()
            
            # Limit to the specified number of context words
            start = max(0, len(context_words) // 2 - context_range)
            end = min(len(context_words), len(context_words) // 2 + context_range)
            context_snippet = " ".join(context_words[start:end])

            if (url.startswith("http") or url.startswith("https"))  and url not in self.visited:
                if len(context_snippet.split()) > 3:
                    links.append((url, context_snippet))
        
        return links

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

        # Todo: Need to store the HTML value somewhere so the web crawler is actually doing something

        # Get the links in the web page
        links = self.parse_links(html, url, 20)
        cleaned_links = clean_words(links)
        tasks = [(item, self.target_word) for item in cleaned_links]
        with Pool() as pool:
            results = pool.starmap(calculate_similarities, tasks)

        horizon = TopValues(self.max_horizon)
        for a_url, values in results:
            try:
                url_average = sum(values) / len(values)
            except ZeroDivisionError:
                url_average = float("-inf")
            horizon.add((a_url, url_average))
        
        while len(horizon.get_top_values()) > 0:  # If we can multiprocess this step we can visit more URLs faster 
            next_url = horizon.pop_highest()[1]
            print(f"Next target: {next_url} - referred by {url}")  # print statement here is doing dull duty to make sure we dont get stuck in infinite loop
            self.crawl(next_url, depth + 1)

    def start(self):
        """Start the crawling process."""
        for url in self.frontier:
            self.crawl(url)


# Example usage
if __name__ == "__main__":
    seed_urls = ["https://en.wikipedia.org/wiki/Web_crawler"]
    target_word = "crawler"
    crawler = WebCrawler(seed_urls, target_word, max_depth=2, max_horizon=3)
    crawler.start()
