"""Tests for base ML classifier functionality."""

from chatbot.ml.base_classifier import MLClassifier


class TestMLClassifier:
    """Test suite for MLClassifier base class."""

    def test_classifier_initialization(self):
        """Test that classifier initializes correctly."""
        classifier = MLClassifier(
            model_name="test",
            classes=["a", "b", "c"]
        )
        assert classifier.model_name == "test"
        assert classifier.classes == ["a", "b", "c"]
        assert classifier.model is not None

    def test_train_and_predict(self):
        """Test training and prediction flow."""
        classifier = MLClassifier(
            model_name="test_train",
            classes=["positive", "negative"]
        )
        
        texts = ["I love this", "This is great", "I hate this", "Terrible"]
        labels = ["positive", "positive", "negative", "negative"]
        
        classifier.train(texts, labels)
        
        # Test prediction
        prediction, confidence = classifier.predict("I love it")
        assert prediction in ["positive", "negative"]
        assert 0 <= confidence <= 1

    def test_confidence_threshold(self):
        """Test that low confidence predictions fall back gracefully."""
        classifier = MLClassifier(
            model_name="test_conf",
            classes=["a", "b"]
        )
        
        # Train on very similar examples
        texts = ["apple", "apples", "apple fruit"]
        labels = ["a", "a", "a"]
        
        classifier.train(texts, labels)
        
        # Predict something completely different
        prediction, confidence = classifier.predict("xyz123random")
        
        # Should still return a prediction (no exception)
        assert prediction in ["a", "b"]
        assert isinstance(confidence, float)

    def test_model_persistence(self):
        """Test that models are saved and loaded correctly."""
        classifier1 = MLClassifier(
            model_name="test_persist_unique",
            classes=["x", "y"]
        )
        
        texts = ["text one", "text two"]
        labels = ["x", "y"]
        classifier1.train(texts, labels)
        pred1, conf1 = classifier1.predict("text one")
        
        # Create new classifier from same directory - should load saved model
        classifier2 = MLClassifier(
            model_name="test_persist_unique",
            classes=["x", "y"]
        )
        pred2, conf2 = classifier2.predict("text one")
        
        # Should produce similar predictions
        assert pred1 == pred2
        assert abs(conf1 - conf2) < 0.05  # Allow small floating point difference

    def test_multiple_training_rounds(self):
        """Test that classifier improves with more training data."""
        classifier = MLClassifier(
            model_name="test_multi",
            classes=["cat", "dog"]
        )
        
        # First round
        texts1 = ["meow", "woof"]
        labels1 = ["cat", "dog"]
        classifier.train(texts1, labels1)
        pred1, _conf1 = classifier.predict("meow")
        
        # Second round with more examples
        texts2 = texts1 + ["purr", "bark", "hiss", "growl"]
        labels2 = labels1 + ["cat", "dog", "cat", "dog"]
        classifier.train(texts2, labels2)
        pred2, _conf2 = classifier.predict("meow")
        
        # Both should predict cat
        assert pred1 == "cat"
        assert pred2 == "cat"

    def test_empty_prediction_handling(self):
        """Test behavior with empty text."""
        classifier = MLClassifier(
            model_name="test_empty",
            classes=["a", "b"]
        )
        
        texts = ["hello", "world"]
        labels = ["a", "b"]
        classifier.train(texts, labels)
        
        # Should handle empty string gracefully
        prediction, confidence = classifier.predict("")
        assert prediction in ["a", "b"]
        assert isinstance(confidence, float)

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        classifier = MLClassifier(
            model_name="test_special",
            classes=["normal", "special"]
        )
        
        texts = [
            "hello world",
            "hello @#$% &*()!",
            "test text",
            "test @#$%"
        ]
        labels = ["normal", "special", "normal", "special"]
        
        classifier.train(texts, labels)
        
        prediction, confidence = classifier.predict("hello !@#$%")
        assert prediction in ["normal", "special"]
        assert isinstance(confidence, float)
