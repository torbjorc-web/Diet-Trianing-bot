"""Specialized ML classifiers for preference extraction."""

from chatbot.ml.base_classifier import MLClassifier


class GoalClassifier(MLClassifier):
    """Classify fitness goal from user input."""

    CLASSES = ["fat loss", "muscle gain", "maintenance", "general fitness"]

    def __init__(self):
        super().__init__("goal", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        classifier = self.model.get_params()["classifier"]
        if not hasattr(classifier, 'classes_'):
            training_examples = [
                ("lose weight fat loss", "fat loss"),
                ("weight loss diet", "fat loss"),
                ("cut down calories", "fat loss"),
                ("reduce body fat", "fat loss"),
                ("get lean", "fat loss"),
                ("build muscle gain mass", "muscle gain"),
                ("bulk up strength", "muscle gain"),
                ("gain muscle size", "muscle gain"),
                ("increase muscle", "muscle gain"),
                ("stay fit maintain", "maintenance"),
                ("maintain weight", "maintenance"),
                ("keep current fitness", "maintenance"),
                ("general fitness", "general fitness"),
                ("get fit healthy", "general fitness"),
                ("improve fitness", "general fitness"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class DietStyleClassifier(MLClassifier):
    """Classify diet style preference."""

    CLASSES = ["balanced", "vegetarian", "vegan", "low-carb", "high-protein"]

    def __init__(self):
        super().__init__("diet_style", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        classifier = self.model.get_params()["classifier"]
        if not hasattr(classifier, 'classes_'):
            training_examples = [
                ("normal balanced diet", "balanced"),
                ("all foods", "balanced"),
                ("omnivore", "balanced"),
                ("vegetarian diet no meat", "vegetarian"),
                ("no meat", "vegetarian"),
                ("vegan diet no animal", "vegan"),
                ("plant based only", "vegan"),
                ("low carb keto", "low-carb"),
                ("minimal carbs", "low-carb"),
                ("high protein diet", "high-protein"),
                ("protein focused", "high-protein"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class MealPreferenceClassifier(MLClassifier):
    """Classify meal preference/dietary restrictions."""

    CLASSES = ["none", "halal", "kosher", "vegan", "vegetarian"]

    def __init__(self):
        super().__init__("meal_preference", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        classifier = self.model.get_params()["classifier"]
        if not hasattr(classifier, 'classes_'):
            training_examples = [
                ("any food", "none"),
                ("no restrictions", "none"),
                ("halal certified", "halal"),
                ("halal only", "halal"),
                ("kosher certified", "kosher"),
                ("kosher diet", "kosher"),
                ("vegan only", "vegan"),
                ("no animal products", "vegan"),
                ("vegetarian only", "vegetarian"),
                ("no meat", "vegetarian"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class TrainingLevelClassifier(MLClassifier):
    """Classify training experience level."""

    CLASSES = ["beginner", "intermediate", "advanced"]

    def __init__(self):
        super().__init__("training_level", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        classifier = self.model.get_params()["classifier"]
        if not hasattr(classifier, 'classes_'):
            training_examples = [
                ("never trained", "beginner"),
                ("just starting", "beginner"),
                ("new to gym", "beginner"),
                ("beginner level", "beginner"),
                ("some experience", "intermediate"),
                ("trained for years", "intermediate"),
                ("intermediate level", "intermediate"),
                ("several years experience", "intermediate"),
                ("expert lifter", "advanced"),
                ("advanced athlete", "advanced"),
                ("competitive", "advanced"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)


class TrainingSettingClassifier(MLClassifier):
    """Classify training environment/setting."""

    CLASSES = ["self", "studio", "group"]

    def __init__(self):
        super().__init__("training_setting", self.CLASSES)
        self._train_default()

    def _train_default(self) -> None:
        """Train with default examples."""
        classifier = self.model.get_params()["classifier"]
        if not hasattr(classifier, 'classes_'):
            training_examples = [
                ("home training", "self"),
                ("at home", "self"),
                ("solo training", "self"),
                ("self guided", "self"),
                ("gym training", "studio"),
                ("studio gym", "studio"),
                ("fitness studio", "studio"),
                ("personal trainer", "studio"),
                ("group class", "group"),
                ("team training", "group"),
                ("group fitness", "group"),
                ("class training", "group"),
            ]
            texts = [t[0] for t in training_examples]
            labels = [t[1] for t in training_examples]
            self.train(texts, labels)
