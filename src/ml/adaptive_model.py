import tensorflow as tf
import numpy as np

class AdaptiveModel:
    def __init__(self):
        # Define model architecture for adaptive learning
        self.model = tf.keras.Sequential([
            tf.keras.Input(shape=(2,)),  # Update to match the number of features
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        self.model.compile(optimizer='adam', loss='binary_crossentropy')

    def train_on_new_data(self, features, labels):
        """
        Train on new data incrementally.
        :param features: List of feature vectors (2D array-like).
        :param labels: List of labels corresponding to the features.
        """
        # Convert to NumPy arrays
        features = np.array(features)
        labels = np.array(labels)

        # Train the model
        self.model.fit(features, labels, epochs=1, verbose=1)
