from sklearn.ensemble import RandomForestClassifier

class RelevanceClassifier:
    def __init__(self):
        # Initialize a RandomForest classifier or another ML model
        self.model = RandomForestClassifier()

    def train(self, features, labels):
        # Train the model with labeled data
        self.model.fit(features, labels)

    def predict(self, features):
        # Predict relevance for new URLs
        return self.model.predict(features)
