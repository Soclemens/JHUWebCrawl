from ml.classifier import RelevanceClassifier
from ml.adaptive_model import AdaptiveModel

class WebCrawler:
    def __init__(self, seed_urls):
        self.frontier = seed_urls
        self.classifier = RelevanceClassifier()
        self.adaptive_model = AdaptiveModel()
    # Additional crawling methods here
