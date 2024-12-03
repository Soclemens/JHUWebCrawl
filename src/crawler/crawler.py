import csv
import time
import os
import sys
import time
import sqlite3
from subprocess import Popen
from celery import Celery, group, signals
from src.models.similarities import calculate_similarities, clean_words, clean_html
from src.models.topVals import TopValues
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
from multiprocessing import Pool
import logging
from robotexclusionrulesparser import RobotExclusionRulesParser


# Configure Celery with RabbitMQ as broker and SQLite as backend
app = Celery(
    "crawler",
    broker="pyamqp://guest@localhost//",
    backend="db+sqlite:///results.sqlite3"
)

# Tell Celery not to hijack the root logger
app.conf.update(
    worker_hijack_root_logger=False,
    # Optionally, prevent Celery from redirecting stdout and stderr
    worker_redirect_stdouts=False,
)

# Logging configuration
logging.basicConfig(
    filename="crawler.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
# Worker-specific start time
WORKER_START_TIME = None

@signals.worker_init.connect
def set_worker_start_time(**kwargs):
    global WORKER_START_TIME
    WORKER_START_TIME = time.time()
    logging.info(f"Worker initialized at {WORKER_START_TIME}")

# SQLite Database Setup
def initialize_database():
    conn = sqlite3.connect("results.sqlite3")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS CrawlResults (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL,
                        depth INTEGER NOT NULL,
                        links_found INTEGER NOT NULL,
                        relevance_score REAL NOT NULL,
                        context_snippet TEXT NOT NULL,
                        duration_sec REAL NOT NULL,
                        total_duration_sec REAL NOT NULL
                      )''')
    conn.commit()
    conn.close()


def insert_crawl_result(url, depth, links_found, relevance_score, context_snippet, duration_sec, total_duration_sec):
    conn = sqlite3.connect("results.sqlite3")
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO CrawlResults (url, depth, links_found, relevance_score, context_snippet, duration_sec, total_duration_sec)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                      (url, depth, links_found, relevance_score, context_snippet, duration_sec, total_duration_sec))
    conn.commit()
    conn.close()

def purge_backend_and_queue():
    """Purge Celery queue and backend."""
    try:
        # Purge Celery task queue
        app.control.purge()
        logging.info("Purged Celery task queue.")

        # Remove SQLite backend file
        backend_file = "results.sqlite3"
        if os.path.exists(backend_file):
            os.remove(backend_file)
            logging.info(f"Removed SQLite backend file: {backend_file}")
    except Exception as e:
        logging.error(f"Error while purging backend and queue: {e}")

class WebCrawler:
    def __init__(self, seed_urls, word, max_depth=2, max_horizon=100, user_agent="MyCrawler"):
        self.target_word = word
        self.max_horizon = max_horizon
        self.frontier = seed_urls  # List of URLs to crawl
        self.visited = set()  # Keep track of visited URLs
        self.max_depth = max_depth
        self.user_agent = user_agent
        self.robots_cache = {}  # Cache for robots parsers per domain
        self.last_access_times = {}  # For rate limiting per domain
        self.default_delay = 1  # Default delay in seconds
        self.crawled_data = []  # Store results for reporting

    def get_robot_parser(self, base_url):
        """Get or fetch the Robots parser for a given base URL."""
        if base_url in self.robots_cache:
            return self.robots_cache[base_url]
        else:
            robots_url = f"{base_url}/robots.txt"
            parser = RobotExclusionRulesParser()
            try:
                response = requests.get(robots_url, headers={"User-Agent": self.user_agent}, timeout=5)
                if response.status_code == 200:
                    parser.parse(response.text)
                else:
                    # Default to allowing all if robots.txt not found
                    parser.parse('')
                self.robots_cache[base_url] = parser
                return parser
            except requests.RequestException as e:
                logging.error(f"Failed to fetch robots.txt from {robots_url}: {e}")
                # Default to allowing all if there's a network error
                parser.parse('')
                self.robots_cache[base_url] = parser
                return parser

    def fetch_page(self, url):
        """Fetch the HTML content of a page."""
        try:
            # Parse the base URL
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # Get the Robots parser
            parser = self.get_robot_parser(base_url)

            # Check robots.txt compliance
            if not parser.is_allowed(self.user_agent, url):
                logging.info(f"Disallowed by robots.txt: {url}")
                return None

            # Implement rate limiting based on Crawl-delay
            now = time.time()
            last_access = self.last_access_times.get(base_url, 0)
            crawl_delay = parser.get_crawl_delay(self.user_agent)
            if crawl_delay is not None:
                delay = crawl_delay
            else:
                delay = self.default_delay  # Use default if Crawl-delay not specified

            elapsed = now - last_access
            logging.info(f"Elapsed time since last access to {base_url}: {elapsed:.2f} seconds; required delay: {delay} seconds")

            if elapsed < delay:
                sleep_time = delay - elapsed
                logging.info(f"Rate limiting {base_url}: sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)

            # Update last access time
            self.last_access_times[base_url] = time.time()

            # Fetch the page
            response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                logging.warning(f"Non-200 status code {response.status_code} for URL: {url}")
        except requests.RequestException as e:
            logging.error(f"Failed to fetch {url}: {e}")
        return None

    def validate_url(self, url):
        """Validate a URL to ensure it's complete and has a valid scheme."""
        parsed_url = urlparse(url)
        return parsed_url.scheme in ["http", "https"] and parsed_url.netloc

    def parse_links(self, html, base_url, context_range=100):
        """Extract all links from a web page."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for link in soup.find_all('a', href=True):
            try:
                # Resolve the full URL
                url = urljoin(base_url, link['href'])

                # Check if the URL starts with http/https and has not been visited
                if not (url.startswith("http") or url.startswith("https")) or url in self.visited:
                    continue

                # Get the text content of the <a> tag
                link_text = link.get_text(strip=True)

                # Get the surrounding context, with error handling for missing elements
                try:
                    preceding_text = link.find_previous(string=True)
                except AttributeError:
                    preceding_text = ""
                try:
                    following_text = link.find_next(string=True).find_next(string=True)
                except AttributeError:
                    following_text = ""

                # Merge the context and split into words
                context = (
                    (preceding_text or "").strip() + " " + link_text + " " + (following_text or "").strip()
                )
                context_words = context.split()

                # Limit to the specified number of context words
                start = max(0, len(context_words) // 2 - context_range)
                end = min(len(context_words), len(context_words) // 2 + context_range)
                context_snippet = " ".join(context_words[start:end])

                # Add the link and context snippet if valid
                if len(context_snippet.split()) > 3:
                    links.append((url, context_snippet))

            except ValueError:
                # Handle malformed URLs gracefully
                logging.warning(f"Skipping malformed URL: {link['href']}")
                continue

        return links


    def calculate_relevance(self, content, keyword):
        """Calculate relevance of page content to a keyword."""
        soup = BeautifulSoup(content, 'html.parser')
        human_readable_text = soup.get_text()

        scores = clean_html(human_readable_text.split(), keyword)
        average = sum(scores) / len(scores)
        return average

    def log_progress(self, url, depth, filename="myfile.txt"):
        """Write progress updates to a hierarchical file."""
        indent = "    " * depth  # Indent based on depth
        with open(filename, "a", encoding="utf-8") as file:
            file.write(f"{indent}{url}\n")

    def crawl(self, url, depth=0, log_file="myfile.txt"):
        """Recursively crawl a URL to the specified depth."""
        global WORKER_START_TIME
        start_time = time.time() 

        if depth > self.max_depth or url in self.visited:
            logging.info(f"Skipping URL (Depth {depth}): {url}")
            return
        
        if not self.validate_url(url):
            logging.warning(f"Skipping invalid URL during crawl: {url}")
            return

        self.visited.add(url)
        logging.info(f"Crawling: {url} (Depth: {depth})")

        html = self.fetch_page(url)
        if not html:
            logging.warning(f"Skipping invalid URL during crawl: {url} - could not get HTML")
            return
        
        relevance_score = self.calculate_relevance(html, self.target_word)
        links = self.parse_links(html, url, 20)
        cleaned_links = clean_words(links)

        # Save the crawl results
        duration_sec = time.time() - start_time
        total_duration_sec = time.time() - WORKER_START_TIME if WORKER_START_TIME else duration_sec
        insert_crawl_result(url, depth, len(cleaned_links), round(relevance_score,4), "; ".join(snippet for _, snippet in cleaned_links), duration_sec, total_duration_sec)
        
        #self.crawled_data.append(entry)
        self.log_progress(url, depth, log_file)

        if depth + 1 > self.max_depth:  # Avoid making calculations for depths were never going to visit
            logging.warning(f"Skipping finding children of {url}")
            return
        
        # Use ThreadPoolExecutor for limited workers
        MAX_WORKERS = 10  # Limit the number of processes
        tasks = [(item, self.target_word) for item in cleaned_links]

        # Define the Pool with MAX_WORKERS
        with Pool(processes=MAX_WORKERS) as pool:
            results = pool.starmap(calculate_similarities, tasks)


        # Use a TopValues object to prioritize the best results
        horizon = TopValues(self.max_horizon)
        for a_url, values in results:
            try:
                url_average = sum(values) / len(values)
            except ZeroDivisionError:
                url_average = float("-inf")
            horizon.add((a_url, url_average))

        # Recursively crawl the top URLs
        while len(horizon.get_top_values()) > 0:
            logging.info(f"{url} current Horizon Size: {len(horizon.get_top_values())}")
            score, next_url = horizon.pop_highest()
            logging.info(f"{score} Next target: {next_url}")
            self.crawl(next_url, depth + 1, log_file)
        
        return

    def start(self, log_file="myfile.txt"):
        """Start the crawling process."""
        with open(log_file, "w", encoding="utf-8") as file:
            file.write("Starting Web Crawler...\n")
        for url in self.frontier:
            self.crawl(url, log_file=log_file)


@app.task(name="crawler.crawl_url")
def celery_crawl_url(seed_url, target_word, max_depth=2, max_horizon=100, log_file="myfile.txt"):
    """Wrap the WebCrawler logic for distributed tasks."""
    crawler = WebCrawler([seed_url], target_word, max_depth, max_horizon)
    crawler.start(log_file=log_file)
    return crawler.crawled_data


@app.task(name="crawler.generate_report")
def generate_csv_report(filename="crawled_report.csv"):
    """Generate a CSV report from the SQLite database."""
    conn = sqlite3.connect("results.sqlite3")
    cursor = conn.cursor()
    cursor.execute('''SELECT url, depth, links_found, relevance_score, context_snippet FROM CrawlResults''')
    rows = cursor.fetchall()
    conn.close()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Depth", "Links Found", "Relevance Score", "Context Snippet"])
        writer.writerows(rows)

    logging.info(f"Report saved to {filename}")

def start_celery_worker(seed_url, concurrency=5):
    """Start a Celery worker for a specific seed URL."""
    logging.info(f"Starting Celery worker for: {seed_url}")
    command = [
        sys.executable,
        "-m", "celery",
        "-A", "src.crawler.crawler",
        "worker",
        "--pool=threads",
        f"--concurrency={concurrency}",
        "--loglevel=info",
        "--hostname", f"worker_{seed_url.replace('://', '_').replace('/', '_')}"
    ]
    return Popen(command, stdout=sys.stdout, stderr=sys.stderr)

def terminate_all_tasks():
    """Terminate all running Celery tasks."""
    try:
        # Get the list of all active tasks
        active_tasks = app.control.inspect().active()
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    task_id = task['id']
                    logging.info(f"Revoking task {task_id} on worker {worker}")
                    app.control.revoke(task_id, terminate=True)
        logging.info("All active tasks have been terminated.")
    except Exception as e:
        logging.error(f"Error during task termination: {e}")

def stop_all_workers(workers):
    """Stop all worker processes."""
    for worker in workers:
        if worker.poll() is None:  # Check if the worker is still running
            logging.info(f"Terminating worker PID: {worker.pid}")
            worker.terminate()
            worker.wait()
    logging.info("All workers have been stopped.")

if __name__ == "__main__":
    seed_urls = ["https://en.wikipedia.org/wiki/Special:Random"]
    target_word = "crawler"
    max_depth = 2
    max_horizon = 4
    log_file = "myfile.txt"

    # Purge Celery queue and backend before starting
    purge_backend_and_queue()

    initialize_database()

    workers = []
    try:
        for seed_url in seed_urls:
            worker_process = start_celery_worker(seed_url)
            workers.append(worker_process)

        time.sleep(5)  # Allow workers to start up

        crawl_tasks = group(
            celery_crawl_url.s(seed_url, target_word, max_depth=max_depth, max_horizon=max_horizon, log_file=log_file)
            for seed_url in seed_urls
        )
        logging.info("Tasks for crawling have been enqueued.")
        crawl_tasks.apply_async().get()

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected! Stopping workers and tasks...")

    finally:
        # Stop all workers
        logging.info("Stopping all workers...")
        stop_all_workers(workers)

        # Terminate any remaining active tasks
        logging.info("Terminating any remaining active tasks...")
        terminate_all_tasks()

        logging.info("Crawling process complete.")

        generate_csv_report()