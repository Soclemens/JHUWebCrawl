import urllib.robotparser
import requests

class RobotsHandler:
    def __init__(self):
        # Dictionary to store robot parsers for each domain
        self.parsers = {}

    def get_parser(self, base_url):
        """
        Retrieve or create a parser for the domain.
        Handles errors if robots.txt is missing or inaccessible.
        """
        if base_url not in self.parsers:
            parser = urllib.robotparser.RobotFileParser()
            robots_url = f"{base_url}/robots.txt"

            try:
                # Fetch and read the robots.txt
                response = requests.get(robots_url, timeout=5)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                else:
                    print(f"robots.txt not found or inaccessible for {base_url}. Defaulting to allow all.")
                    parser.allow_all = True  # Allow all if robots.txt is missing
            except requests.RequestException as e:
                print(f"Error fetching robots.txt for {base_url}: {e}. Defaulting to allow all.")
                parser.allow_all = True  # Allow all if there’s a network error

            self.parsers[base_url] = parser

        return self.parsers[base_url]

    def can_fetch(self, base_url, user_agent, url):
        """
        Check if the user agent is allowed to fetch the URL.
        Handles malformed robots.txt by defaulting to allow all.
        """
        parser = self.get_parser(base_url)

        # Check if the parser has valid rules; allow all if rules are missing or invalid
        try:
            return parser.can_fetch(user_agent, url)
        except Exception as e:
            print(f"Error parsing robots.txt for {base_url}: {e}. Defaulting to allow all.")
            return True  # Default to allow all if parsing fails
