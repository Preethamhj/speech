from dataclasses import asdict, dataclass
from typing import Any


VERY_HIGH = "VERY_HIGH"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
VERY_LOW = "VERY_LOW"


@dataclass
class WordConfidence:
    word: str
    start: float
    end: float
    probability: float
    risk_level: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class SegmentConfidence:
    text: str
    avg_logprob: float
    no_speech_prob: float
    compression_ratio: float
    risk_level: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ConfidenceAnalysisService:
    def analyze(self, segments: list[Any]) -> tuple[list[SegmentConfidence], list[WordConfidence]]:
        segment_confidences: list[SegmentConfidence] = []
        word_confidences: list[WordConfidence] = []

        for segment in segments:
            segment_confidences.append(self.extract_segment_confidence(segment))
            word_confidences.extend(self.extract_word_confidences(segment))

        return segment_confidences, word_confidences

    def extract_segment_confidence(self, segment: Any) -> SegmentConfidence:
        avg_logprob = float(getattr(segment, "avg_logprob", 0.0) or 0.0)
        no_speech_prob = float(getattr(segment, "no_speech_prob", 0.0) or 0.0)
        compression_ratio = float(getattr(segment, "compression_ratio", 0.0) or 0.0)
        probability = self._segment_probability(avg_logprob, no_speech_prob, compression_ratio)

        return SegmentConfidence(
            text=str(getattr(segment, "text", "") or "").strip(),
            avg_logprob=avg_logprob,
            no_speech_prob=no_speech_prob,
            compression_ratio=compression_ratio,
            risk_level=classify(probability),
        )

    def extract_word_confidences(self, segment: Any) -> list[WordConfidence]:
        words = getattr(segment, "words", None) or []
        confidences: list[WordConfidence] = []
        for item in words:
            word = str(getattr(item, "word", "") or "").strip()
            if not word:
                continue
            probability = float(getattr(item, "probability", 0.0) or 0.0)
            confidences.append(
                WordConfidence(
                    word=word,
                    start=float(getattr(item, "start", 0.0) or 0.0),
                    end=float(getattr(item, "end", 0.0) or 0.0),
                    probability=round(probability, 4),
                    risk_level=classify(probability),
                )
            )
        return confidences

    def get_uncertain_words(
        self,
        words: list[WordConfidence],
        max_risk_level: str = LOW,
    ) -> list[dict[str, object]]:
        allowed = {LOW, VERY_LOW} if max_risk_level == LOW else {VERY_LOW}
        return [
            {"word": item.word, "confidence": item.probability, "risk": item.risk_level}
            for item in words
            if item.risk_level in allowed
        ]

    def _segment_probability(self, avg_logprob: float, no_speech_prob: float, compression_ratio: float) -> float:
        logprob_score = max(0.0, min(1.0, 1.0 + avg_logprob))
        speech_score = max(0.0, min(1.0, 1.0 - no_speech_prob))
        compression_penalty = 0.25 if compression_ratio > 2.4 else 0.0
        return max(0.0, min(1.0, min(logprob_score, speech_score) - compression_penalty))


def classify(probability: float) -> str:
    probability = max(0.0, min(1.0, probability))
    if probability >= 0.90:
        return VERY_HIGH
    if probability >= 0.75:
        return HIGH
    if probability >= 0.60:
        return MEDIUM
    if probability >= 0.40:
        return LOW
    return VERY_LOW
