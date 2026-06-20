from app.services.confidence_analysis import ConfidenceAnalysisService, classify


class FakeWord:
    def __init__(self, word: str, probability: float) -> None:
        self.word = word
        self.start = 0.0
        self.end = 0.5
        self.probability = probability


class FakeSegment:
    text = "farmer ಮಟ್ಕೆ"
    avg_logprob = -0.2
    no_speech_prob = 0.05
    compression_ratio = 1.2
    words = [FakeWord("farmer", 0.98), FakeWord("ಮಟ್ಕೆ", 0.22)]


def test_confidence_classification_thresholds():
    assert classify(0.95) == "VERY_HIGH"
    assert classify(0.80) == "HIGH"
    assert classify(0.65) == "MEDIUM"
    assert classify(0.45) == "LOW"
    assert classify(0.20) == "VERY_LOW"


def test_uncertain_words_are_extracted_from_word_metadata():
    service = ConfidenceAnalysisService()

    _segments, words = service.analyze([FakeSegment()])
    uncertain = service.get_uncertain_words(words)

    assert uncertain == [{"word": "ಮಟ್ಕೆ", "confidence": 0.22, "risk": "VERY_LOW"}]
