from app.services.correction_service import IntentPreservingCorrectionService


def test_english_word_repetitions_are_removed():
    service = IntentPreservingCorrectionService()

    assert service._deterministic_cleanup("I I I want to explain my project") == "I want to explain my project"


def test_kannada_word_repetitions_are_removed():
    service = IntentPreservingCorrectionService()

    assert service._deterministic_cleanup("ನಾ ನಾ ನಾನು ಕಾಲೇಜಿಗೆ ಹೋಗುತ್ತೇನೆ") == "ನಾನು ಕಾಲೇಜಿಗೆ ಹೋಗುತ್ತೇನೆ"


def test_phrase_repetitions_are_removed():
    service = IntentPreservingCorrectionService()

    assert service._deterministic_cleanup("I want I want to speak") == "I want to speak"


def test_intentional_emphasis_is_preserved():
    service = IntentPreservingCorrectionService()

    assert service._deterministic_cleanup("The project is very very important") == (
        "The project is very very important"
    )


def test_partial_word_repetitions_are_removed():
    service = IntentPreservingCorrectionService()

    assert service._deterministic_cleanup("Pro-Pro-Project submission") == "Project submission"
    assert service._deterministic_cleanup("ಪ್ರ ಪ್ರ ಪ್ರಾಜೆಕ್ಟ್ ಸಲ್ಲಿಕೆ") == "ಪ್ರಾಜೆಕ್ಟ್ ಸಲ್ಲಿಕೆ"
