from app.evaluation.cer import character_error_rate
from app.evaluation.wer import word_error_rate


def test_word_error_rate():
    assert word_error_rate("I need help", "I need help") == 0.0
    assert word_error_rate("I need help", "I help") == 1 / 3


def test_character_error_rate():
    assert character_error_rate("ನೀರು", "ನೀರು") == 0.0
    assert character_error_rate("abc", "adc") == 1 / 3
