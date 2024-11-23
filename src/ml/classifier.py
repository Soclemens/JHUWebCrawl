from sklearn.ensemble import RandomForestClassifier

class RelevanceClassifier:
    def __init__(self):
        """Initialize the classifier and pretrain with dummy data."""
        self.model = RandomForestClassifier()
        self._pretrain()

    def _pretrain(self):
        """Train the model with initial dummy data."""
        # Dummy features and labels: Replace these with real labeled data later
        features = [
            [10, 2],  # Example: [URL length, keyword count]
            [15, 0],
            [7, 3],
            [20, 1]
        ]
        labels = [1, 0, 1, 0]  # 1 = relevant, 0 = not relevant
        self.train(features, labels)

    def train(self, features, labels):
        """
        Train the model with the provided features and labels.
        :param features: List of feature vectors.
        :param labels: List of labels (1 for relevant, 0 for not relevant).
        """
        self.model.fit(features, labels)

    def predict(self, features):
        """
        Predict relevance for the given features.
        :param features: Feature vector of a single item.
        :return: Predicted label (1 for relevant, 0 for not relevant).
        """
        # Ensure input is in the correct shape for the model
        return self.model.predict([features])  # Returns a list, so access [0] for the value
