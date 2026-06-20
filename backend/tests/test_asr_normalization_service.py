from app.services.asr_normalization_service import ASRNormalizationService


def test_common_kannada_asr_errors_are_normalized():
    service = ASRNormalizationService()

    assert service.normalize("ಫಾರ್ಮರ್ ಮಟ್ಕೆ ನಿರ್ ತುಂಬಿದ") == "farmer ಮಡಿಕೆ ನೀರು ತುಂಬಿದ"


def test_code_mixed_words_are_preserved():
    service = ASRNormalizationService()

    assert service.normalize("ನಾನು school project submit ಮಾಡಿದೆ") == "ನಾನು school project submit ಮಾಡಿದೆ"


def test_unclear_words_are_not_overcorrected():
    service = ASRNormalizationService()

    unclear = "ಸಿಯಿಚ್ಕೊಳನ್ನ ಇದು"

    assert service.normalize(unclear) == unclear
