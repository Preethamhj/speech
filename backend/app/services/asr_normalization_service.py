import re


COMMON_FIXES = {
    "ಮಟ್ಕೆ": "ಮಡಿಕೆ",
    "ಮಡ್ಕೆ": "ಮಡಿಕೆ",
    "ನಿರ್": "ನೀರು",
    "ಯೋಸ್ನೆ": "ಯೋಚನೆ",
    "ಮಾಟ್ರಡಾ": "ಮಾಡ್ತೀಯಾ",
    "ಫ್ಲಾವರ್ಸಿದೆ": "flowers ಇದೆ",
    "ಫಾರ್ಮರ್": "farmer",
}


class ASRNormalizationService:
    def normalize(self, transcript: str) -> str:
        text = transcript
        for source, replacement in COMMON_FIXES.items():
            text = self._replace_token(text, source, replacement)
        return self._normalize_spacing(text)

    def _replace_token(self, text: str, source: str, replacement: str) -> str:
        pattern = rf"(?<!\S){re.escape(source)}(?!\S)"
        return re.sub(pattern, replacement, text)

    def _normalize_spacing(self, text: str) -> str:
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
